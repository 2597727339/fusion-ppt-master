[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$InputFile,

    [string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-ExternalTool {
    param(
        [Parameter(Mandatory)]
        [string]$OverrideVariable,

        [Parameter(Mandatory)]
        [string[]]$CommandNames,

        [string[]]$CandidatePaths = @(),

        [string]$WinGetFilename
    )

    $override = [Environment]::GetEnvironmentVariable($OverrideVariable)
    if ($override) {
        $resolvedOverride = [IO.Path]::GetFullPath($override)
        if (Test-Path -LiteralPath $resolvedOverride -PathType Leaf) {
            return $resolvedOverride
        }
        throw "$OverrideVariable points to a missing executable: $resolvedOverride"
    }

    foreach ($name in $CommandNames) {
        $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($command -and $command.Source) {
            return $command.Source
        }
    }

    foreach ($candidate in $CandidatePaths) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return [IO.Path]::GetFullPath($candidate)
        }
    }

    if ($WinGetFilename) {
        $localAppData = [Environment]::GetEnvironmentVariable('LOCALAPPDATA')
        if ($localAppData) {
            $winGetRoot = Join-Path $localAppData 'Microsoft\WinGet\Packages'
            if (Test-Path -LiteralPath $winGetRoot -PathType Container) {
                $winGetMatch = Get-ChildItem -LiteralPath $winGetRoot -Filter $WinGetFilename -File -Recurse -ErrorAction SilentlyContinue |
                    Select-Object -First 1
                if ($winGetMatch) {
                    return $winGetMatch.FullName
                }
            }
        }
    }

    throw "Required renderer is unavailable. Set $OverrideVariable or add one of these commands to PATH: $($CommandNames -join ', ')."
}

$source = (Resolve-Path -LiteralPath $InputFile).Path
$extension = [IO.Path]::GetExtension($source).ToLowerInvariant()
if ($extension -notin @('.pptx', '.docx', '.xlsx')) {
    throw "Unsupported file type '$extension'. Use PPTX, DOCX, or XLSX."
}

if (-not $OutputDirectory) {
    $stem = [IO.Path]::GetFileNameWithoutExtension($source)
    $OutputDirectory = Join-Path (Split-Path -Parent $source) "$stem-visual-review"
}
$output = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $output -PathType Leaf) {
    throw "OutputDirectory must be a directory: $output"
}
New-Item -ItemType Directory -Force -Path $output | Out-Null

$programFilesRoots = @(
    [Environment]::GetEnvironmentVariable('ProgramFiles'),
    [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
) | Where-Object { $_ }
$sofficeCandidates = @()
foreach ($root in $programFilesRoots) {
    $sofficeCandidates += Join-Path $root 'LibreOffice\program\soffice.com'
    $sofficeCandidates += Join-Path $root 'LibreOffice\program\soffice.exe'
}

$programData = [Environment]::GetEnvironmentVariable('ProgramData')
$pdftoppmCandidates = @()
if ($programData) {
    $pdftoppmCandidates += Join-Path $programData 'chocolatey\bin\pdftoppm.exe'
}

$sofficeArguments = @{
    OverrideVariable = 'FUSION_SOFFICE'
    CommandNames = @('soffice.com', 'soffice.exe', 'soffice')
    CandidatePaths = $sofficeCandidates
}
$soffice = Resolve-ExternalTool @sofficeArguments
$pdftoppmArguments = @{
    OverrideVariable = 'FUSION_PDFTOPPM'
    CommandNames = @('pdftoppm.exe', 'pdftoppm')
    CandidatePaths = $pdftoppmCandidates
    WinGetFilename = 'pdftoppm.exe'
}
$pdftoppm = Resolve-ExternalTool @pdftoppmArguments

$stage = Join-Path ([IO.Path]::GetTempPath()) (
    'fusion-local-office-review-' + [guid]::NewGuid().ToString('N')
)
New-Item -ItemType Directory -Force -Path $stage | Out-Null

try {
    $stagedSource = Join-Path $stage ('source' + $extension)
    Copy-Item -LiteralPath $source -Destination $stagedSource

    & $soffice --headless --convert-to pdf --outdir $stage $stagedSource | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "LibreOffice conversion failed with exit code $LASTEXITCODE."
    }

    $stagedPdf = Join-Path $stage 'source.pdf'
    if (-not (Test-Path -LiteralPath $stagedPdf -PathType Leaf)) {
        throw 'LibreOffice did not produce a PDF.'
    }

    $pdf = Join-Path $output 'document.pdf'
    if (Test-Path -LiteralPath $pdf -PathType Leaf) {
        Remove-Item -LiteralPath $pdf -Force
    }
    Get-ChildItem -LiteralPath $output -Filter 'page-*.png' -File -ErrorAction SilentlyContinue |
        Remove-Item -Force

    Copy-Item -LiteralPath $stagedPdf -Destination $pdf
    $prefix = Join-Path $output 'page'
    & $pdftoppm -png -r 150 $pdf $prefix | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Poppler rasterization failed with exit code $LASTEXITCODE."
    }

    $pages = @(Get-ChildItem -LiteralPath $output -Filter 'page-*.png' -File | Sort-Object Name)
    if ($pages.Count -eq 0) {
        throw 'Poppler did not produce page images.'
    }

    [pscustomobject]@{
        status = 'success'
        source = $source
        pdf = $pdf
        page_count = $pages.Count
        pages = @($pages.FullName)
        renderer = 'fusion-bundled-local'
    } | ConvertTo-Json -Depth 3
}
finally {
    Remove-Item -LiteralPath $stage -Force -Recurse -ErrorAction SilentlyContinue
}
