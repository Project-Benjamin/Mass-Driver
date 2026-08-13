[CmdletBinding()]
param(
    [string]$BuildManifest,
    [string]$PackageSource,
    [string]$PatchPath,
    [string]$CuePath,
    [string]$XdeltaSourceDirectory,
    [string]$OutputDirectory,
    [switch]$Force
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$Here = [IO.Path]::GetFullPath($PSScriptRoot)
$RepoRoot = [IO.Path]::GetFullPath([IO.Path]::Combine($Here, '..'))
if ([string]::IsNullOrWhiteSpace($BuildManifest)) {
    $BuildManifest = [IO.Path]::Combine($Here, 'build_manifest.json')
}
$BuildManifest = [IO.Path]::GetFullPath($BuildManifest)
$Manifest = Get-Content -LiteralPath $BuildManifest -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Manifest.format -ne 'xenogears-mass-driver-build-v1') {
    throw "Unsupported build manifest format: $($Manifest.format)"
}

function Assert-PlainName([string]$Label, [string]$Value, [string]$Extension = '') {
    $Stem = [IO.Path]::GetFileNameWithoutExtension($Value).TrimEnd(' ', '.').ToUpperInvariant()
    $Reserved = @('CON','PRN','AUX','NUL','COM1','COM2','COM3','COM4','COM5','COM6','COM7','COM8','COM9','LPT1','LPT2','LPT3','LPT4','LPT5','LPT6','LPT7','LPT8','LPT9')
    if ([string]::IsNullOrWhiteSpace($Value) -or [IO.Path]::GetFileName($Value) -cne $Value -or
        $Value.EndsWith(' ') -or $Value.EndsWith('.') -or $Reserved -contains $Stem -or
        $Value -in '.', '..' -or $Value.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0 -or
        (-not [string]::IsNullOrEmpty($Extension) -and [IO.Path]::GetExtension($Value) -ine $Extension)) {
        throw "$Label must be a plain $Extension file name: $Value"
    }
}

function Assert-SafeRelative([string]$Label, [string]$Value, [string]$RequiredPrefix, [string]$Extension) {
    if ([string]::IsNullOrWhiteSpace($Value) -or [IO.Path]::IsPathRooted($Value) -or $Value.Contains('\') -or
        $Value.Contains(':') -or ($Value -split '/') -contains '..' -or ($Value -split '/') -contains '.' -or
        -not $Value.StartsWith($RequiredPrefix, [StringComparison]::Ordinal) -or
        [IO.Path]::GetExtension($Value) -ine $Extension) {
        throw "$Label must be a normalized $Extension path under '$RequiredPrefix': $Value"
    }
    foreach ($Segment in ($Value -split '/')) {
        Assert-PlainName "$Label segment" $Segment
    }
}

Assert-PlainName 'package.directory_name' ([string]$Manifest.package.directory_name)
Assert-PlainName 'package.zip_filename' ([string]$Manifest.package.zip_filename) '.zip'
Assert-PlainName 'package.app_filename' ([string]$Manifest.package.app_filename) '.exe'
Assert-PlainName 'package.support_directory' ([string]$Manifest.package.support_directory)
Assert-PlainName 'package.output_folder' ([string]$Manifest.package.output_folder)
Assert-PlainName 'output.bin_name' ([string]$Manifest.output.bin_name) '.bin'
Assert-PlainName 'output.cue_name' ([string]$Manifest.output.cue_name) '.cue'
if ([string]$Manifest.package.directory_name -cne 'Xenogears_Mass_Driver' -or
    [string]$Manifest.package.zip_filename -cne 'Xenogears_Mass_Driver.zip' -or
    [string]$Manifest.package.app_filename -cne 'Xenogears_Mass_Driver.exe' -or
    [string]$Manifest.package.support_directory -cne 'MassDriverData' -or
    [string]$Manifest.package.output_folder -cne 'Mass Driver Game' -or
    [string]$Manifest.package.staging_prefix -cne '.MassDriverBuild.' -or
    [string]$Manifest.patch.relative_path -cne 'MassDriverData/patches/Mass_Driver.xdelta' -or
    [string]$Manifest.cue_template.relative_path -cne 'MassDriverData/game/Mass_Driver.cue.template' -or
    [string]$Manifest.output.bin_name -cne 'Xenogears_Mass_Driver.bin' -or
    [string]$Manifest.output.cue_name -cne 'Xenogears_Mass_Driver.cue') {
    throw 'Package and game filenames are stable and cannot be changed by a build manifest.'
}
if ([string]$Manifest.package.staging_prefix -notmatch '^\.[A-Za-z0-9_-]+\.$' -or
    ([string]$Manifest.package.staging_prefix).Length -gt 64) {
    throw "package.staging_prefix must be a short safe dotted prefix: $($Manifest.package.staging_prefix)"
}
Assert-SafeRelative 'patch.relative_path' ([string]$Manifest.patch.relative_path) (([string]$Manifest.package.support_directory) + '/patches/') '.xdelta'
Assert-SafeRelative 'cue_template.relative_path' ([string]$Manifest.cue_template.relative_path) (([string]$Manifest.package.support_directory) + '/game/') '.template'

$MiB = 1024L * 1024L
foreach ($Range in @(
    @{ Label = 'source.size'; Value = [long]$Manifest.source.size; Minimum = 100L * $MiB; Maximum = 1024L * $MiB },
    @{ Label = 'patch.size'; Value = [long]$Manifest.patch.size; Minimum = 1L; Maximum = 1024L * $MiB },
    @{ Label = 'cue_template.size'; Value = [long]$Manifest.cue_template.size; Minimum = 1L; Maximum = 4096L },
    @{ Label = 'output.bin_size'; Value = [long]$Manifest.output.bin_size; Minimum = 100L * $MiB; Maximum = 1024L * $MiB }
)) {
    if ($Range.Value -lt $Range.Minimum -or $Range.Value -gt $Range.Maximum) {
        throw "$($Range.Label) is outside the runtime safety range."
    }
}
if ([long]$Manifest.cue_template.size -ne [long]$Manifest.output.cue_size -or
    [string]$Manifest.cue_template.sha256 -cne [string]$Manifest.output.cue_sha256) {
    throw 'The output CUE size and SHA-256 must exactly match the supplied CUE template.'
}

if ([string]::IsNullOrWhiteSpace($PackageSource)) {
    $PackageSource = [IO.Path]::Combine($RepoRoot, 'dist', 'Xenogears Mass Driver')
}
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = [IO.Path]::Combine($RepoRoot, 'dist')
}
$PackageSource = [IO.Path]::GetFullPath($PackageSource)
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)

if ([string]::IsNullOrWhiteSpace($PatchPath)) {
    $PatchPath = [IO.Path]::Combine($PackageSource, 'patches', [IO.Path]::GetFileName([string]$Manifest.patch.relative_path))
}
if ([string]::IsNullOrWhiteSpace($CuePath)) {
    $CuePath = [IO.Path]::Combine($Here, 'game.cue.template')
}
if ([string]::IsNullOrWhiteSpace($XdeltaSourceDirectory)) {
    throw "Supply -XdeltaSourceDirectory pointing to a clean xdelta checkout at commit $($Manifest.decoder.source_commit)."
}
$PatchPath = [IO.Path]::GetFullPath($PatchPath)
$CuePath = [IO.Path]::GetFullPath($CuePath)
$XdeltaSourceDirectory = [IO.Path]::GetFullPath($XdeltaSourceDirectory)

function Assert-PinnedFile {
    param([string]$Label, [string]$Path, [long]$Size, [string]$Sha256)
    if (-not [IO.File]::Exists($Path)) { throw "$Label is missing: $Path" }
    $Item = Get-Item -LiteralPath $Path -Force
    if ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "$Label cannot be a reparse point: $Path" }
    if ($Item.Length -ne $Size) { throw "$Label size mismatch: expected $Size; found $($Item.Length)" }
    $Actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Actual -ne $Sha256.ToLowerInvariant()) {
        throw "$Label SHA-256 mismatch: expected $Sha256; found $Actual"
    }
}

function Assert-PinnedCheckout {
    param([string]$Label, [string]$Path, [string]$Commit)
    if (-not [IO.Directory]::Exists($Path)) { throw "$Label source checkout is missing: $Path" }
    $Git = (Get-Command git.exe -ErrorAction Stop).Source
    $Head = (& $Git -C $Path rev-parse --verify HEAD 2>$null).Trim()
    if ($LASTEXITCODE -ne 0 -or $Head -cne $Commit) {
        throw "$Label source commit mismatch: expected $Commit; found $Head"
    }
    $Status = @(& $Git -C $Path status --porcelain=v1 --untracked-files=all)
    if ($LASTEXITCODE -ne 0 -or $Status.Count -ne 0) {
        throw "$Label source checkout must be clean at pinned commit $Commit."
    }
}

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, (New-Object Text.UTF8Encoding($false)))
}

function Get-Relative([string]$Root, [string]$Path) {
    return $Path.Substring($Root.TrimEnd('\').Length + 1).Replace('\','/')
}

function New-MassDriverIcon([string]$Path) {
    # Deterministic code-native icon: a white missile over a red warning field.
    $Size = 32
    $Stride = 4 * [int][Math]::Ceiling($Size / 32.0)
    $Xor = New-Object byte[] ($Size * $Size * 4)
    $And = New-Object byte[] ($Stride * $Size)
    for ($Y = 0; $Y -lt $Size; ++$Y) {
        for ($X = 0; $X -lt $Size; ++$X) {
            $Index = (($Size - 1 - $Y) * $Size + $X) * 4
            $Dx = $X - 15.5; $Dy = $Y - 15.5
            $Radius = [Math]::Sqrt($Dx * $Dx + $Dy * $Dy)
            $B = 32; $G = 38; $R = 48; $A = 255
            if ($Radius -lt 14.5) { $B = 48; $G = 55; $R = 204 }
            # Upward missile body/nose, fins, window, and exhaust.
            $Missile = (($Y -ge 6 -and $Y -le 23 -and $X -ge 13 -and $X -le 18) -or
                ($Y -ge 4 -and $Y -le 8 -and [Math]::Abs($X - 15.5) -le ($Y - 3) / 2) -or
                ($Y -ge 19 -and $Y -le 25 -and (($X -ge 9 -and $X -le 13) -or ($X -ge 18 -and $X -le 22))))
            if ($Missile) { $B = 238; $G = 242; $R = 245 }
            if (($X -ge 14 -and $X -le 17 -and $Y -ge 10 -and $Y -le 13)) { $B = 76; $G = 153; $R = 42 }
            if ($Y -ge 24 -and $Y -le 28 -and [Math]::Abs($X - 15.5) -le (29 - $Y) / 2) {
                $B = 24; $G = 186; $R = 255
            }
            $Xor[$Index] = $B; $Xor[$Index + 1] = $G; $Xor[$Index + 2] = $R; $Xor[$Index + 3] = $A
        }
    }
    $BitmapBytes = 40 + $Xor.Length + $And.Length
    $Stream = New-Object IO.MemoryStream
    $Writer = New-Object IO.BinaryWriter($Stream)
    try {
        $Writer.Write([uint16]0); $Writer.Write([uint16]1); $Writer.Write([uint16]1)
        $Writer.Write([byte]$Size); $Writer.Write([byte]$Size); $Writer.Write([byte]0); $Writer.Write([byte]0)
        $Writer.Write([uint16]1); $Writer.Write([uint16]32); $Writer.Write([uint32]$BitmapBytes); $Writer.Write([uint32]22)
        $Writer.Write([uint32]40); $Writer.Write([int32]$Size); $Writer.Write([int32]($Size * 2))
        $Writer.Write([uint16]1); $Writer.Write([uint16]32); $Writer.Write([uint32]0); $Writer.Write([uint32]$Xor.Length)
        $Writer.Write([int32]0); $Writer.Write([int32]0); $Writer.Write([uint32]0); $Writer.Write([uint32]0)
        $Writer.Write($Xor); $Writer.Write($And); $Writer.Flush()
        [IO.File]::WriteAllBytes($Path, $Stream.ToArray())
    } finally { $Writer.Dispose(); $Stream.Dispose() }
}

foreach ($Hash in @(
    [string]$Manifest.source.sha256, [string]$Manifest.patch.sha256,
    [string]$Manifest.cue_template.sha256,
    [string]$Manifest.output.bin_sha256, [string]$Manifest.output.cue_sha256
)) {
    if ($Hash -notmatch '^[0-9a-fA-F]{64}$') { throw "Invalid SHA-256 in build manifest: $Hash" }
}
foreach ($Commit in @([string]$Manifest.decoder.source_commit)) {
    if ($Commit -notmatch '^[0-9a-f]{40}$') { throw "Invalid source commit in release manifest: $Commit" }
}
Assert-PinnedFile 'game patch' $PatchPath ([long]$Manifest.patch.size) ([string]$Manifest.patch.sha256)
Assert-PinnedFile 'CUE template' $CuePath ([long]$Manifest.cue_template.size) ([string]$Manifest.cue_template.sha256)
Assert-PinnedCheckout 'xdelta3' $XdeltaSourceDirectory ([string]$Manifest.decoder.source_commit)

$VsWhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
if (-not [IO.File]::Exists($VsWhere)) { throw 'Visual Studio Build Tools locator is not installed.' }
$VsInstall = (& $VsWhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath).Trim()
if ([string]::IsNullOrWhiteSpace($VsInstall)) { throw 'Visual C++ x64 build tools are not installed.' }
$VsDevCmd = [IO.Path]::Combine($VsInstall, 'Common7', 'Tools', 'VsDevCmd.bat')
$EnvironmentLines = & $env:ComSpec /d /c ('call "' + $VsDevCmd + '" -no_logo -arch=x64 -host_arch=x64 >nul && set')
if ($LASTEXITCODE -ne 0) { throw 'Could not initialize the Visual C++ x64 build environment.' }
foreach ($Line in $EnvironmentLines) {
    $Split = $Line.IndexOf('=')
    if ($Split -gt 0) { [Environment]::SetEnvironmentVariable($Line.Substring(0, $Split), $Line.Substring($Split + 1), 'Process') }
}
$Cl = (Get-Command cl.exe -ErrorAction Stop).Source
$Rc = (Get-Command rc.exe -ErrorAction Stop).Source

$BuildRoot = [IO.Path]::Combine($Here, ('.build.' + [Guid]::NewGuid().ToString('N')))
$StageRoot = [IO.Path]::Combine($OutputDirectory, ('.package.' + [Guid]::NewGuid().ToString('N')))
$FinalRoot = [IO.Path]::Combine($OutputDirectory, [string]$Manifest.package.directory_name)
$ZipPath = [IO.Path]::Combine($OutputDirectory, [string]$Manifest.package.zip_filename)
[IO.Directory]::CreateDirectory($BuildRoot) | Out-Null
[IO.Directory]::CreateDirectory($StageRoot) | Out-Null
try {
    Copy-Item -LiteralPath ([IO.Path]::Combine($Here, 'app.manifest')) -Destination ([IO.Path]::Combine($BuildRoot, 'app.manifest'))
    Copy-Item -LiteralPath ([IO.Path]::Combine($Here, 'resource.h')) -Destination ([IO.Path]::Combine($BuildRoot, 'resource.h'))
    $IconPath = [IO.Path]::Combine($BuildRoot, 'mass_driver.ico')
    New-MassDriverIcon $IconPath
    $IconExpectedSize = 4286L
    $IconExpectedSha256 = '0a91eecc797c1e353ff88b526c78e1ca68b9f9343eac3f7f55dbca8e577838cc'
    Assert-PinnedFile 'code-native app icon' $IconPath $IconExpectedSize $IconExpectedSha256

    $XdeltaConfig = @"
#ifndef XDELTA3_CONFIG_H
#define XDELTA3_CONFIG_H
#define SIZEOF_SIZE_T 8
#define SIZEOF_UNSIGNED_INT 4
#define SIZEOF_UNSIGNED_LONG 4
#define SIZEOF_UNSIGNED_LONG_LONG 8
#endif
"@
    Write-Utf8NoBom ([IO.Path]::Combine($BuildRoot, 'config.h')) $XdeltaConfig

    $MainRc = [IO.File]::ReadAllText([IO.Path]::Combine($Here, 'resources.rc'), [Text.Encoding]::UTF8)
    $MainRcPath = [IO.Path]::Combine($BuildRoot, 'resources.generated.rc')
    Write-Utf8NoBom $MainRcPath $MainRc
    $MainRes = [IO.Path]::Combine($BuildRoot, 'resources.res')
    & $Rc /nologo "/fo$MainRes" $MainRcPath
    if ($LASTEXITCODE -ne 0) { throw "rc.exe failed for app with exit code $LASTEXITCODE" }
    $StartExe = [IO.Path]::Combine($BuildRoot, [string]$Manifest.package.app_filename)
    $MainObj = [IO.Path]::Combine($BuildRoot, 'main.obj')
    $EmulatorObj = [IO.Path]::Combine($BuildRoot, 'emulator.obj')
    $DecoderObj = [IO.Path]::Combine($BuildRoot, 'xdelta_decoder.obj')
    $XdeltaCoreObj = [IO.Path]::Combine($BuildRoot, 'xdelta3_decode_core.obj')
    $XdeltaCodeDirectory = [IO.Path]::Combine($XdeltaSourceDirectory, 'xdelta3')
    $XdeltaSource = [IO.Path]::Combine($XdeltaCodeDirectory, 'xdelta3.c')
    if (-not [IO.File]::Exists($XdeltaSource)) {
        throw 'Pinned xdelta3 source is missing.'
    }
    $XdeltaAbiFlags = @('/DHAVE_CONFIG_H=1','/DXD3_USE_LARGESIZET=1','/DXD3_ENCODER=0',
        "/I$XdeltaCodeDirectory")
    $CompileFlags = @('/nologo','/c','/std:c++17','/O2','/Oi','/MT','/EHsc','/permissive-','/W4',
        '/DUNICODE','/D_UNICODE','/DWIN32_LEAN_AND_MEAN','/DNOMINMAX','/guard:cf','/sdl','/Brepro',"/I$BuildRoot","/I$Here") + $XdeltaAbiFlags
    & $Cl @CompileFlags "/Fo$MainObj" ([IO.Path]::Combine($Here, 'main.cpp'))
    if ($LASTEXITCODE -ne 0 -or -not [IO.File]::Exists($MainObj)) { throw 'Main source compilation failed.' }
    & $Cl @CompileFlags "/Fo$EmulatorObj" ([IO.Path]::Combine($Here, 'emulator.cpp'))
    if ($LASTEXITCODE -ne 0 -or -not [IO.File]::Exists($EmulatorObj)) { throw 'Emulator source compilation failed.' }
    & $Cl @CompileFlags "/Fo$DecoderObj" ([IO.Path]::Combine($Here, 'xdelta_decoder.cpp'))
    if ($LASTEXITCODE -ne 0 -or -not [IO.File]::Exists($DecoderObj)) { throw 'Integrated decoder wrapper compilation failed.' }
    $XdeltaCoreFlags = @('/nologo','/c','/TC','/std:c11','/O2','/Oi','/MT','/W3','/guard:cf','/sdl','/Brepro',
        '/D_CRT_SECURE_NO_WARNINGS','/D_CRT_NONSTDC_NO_WARNINGS','/DREGRESSION_TEST=0',
        '/DSECONDARY_DJW=0','/DSECONDARY_FGK=0','/DSECONDARY_LZMA=0','/DXD3_MAIN=0','/DXD3_DEBUG=0',
        '/DXD3_WIN32=1','/DXD3_POSIX=0','/DXD3_STDIO=0','/DEXTERNAL_COMPRESSION=0','/DSHELL_TESTS=0',
        "/I$BuildRoot") + $XdeltaAbiFlags
    & $Cl @XdeltaCoreFlags "/Fo$XdeltaCoreObj" $XdeltaSource
    if ($LASTEXITCODE -ne 0 -or -not [IO.File]::Exists($XdeltaCoreObj)) { throw 'Pinned xdelta3 decoder-core compilation failed.' }
    & $Cl /nologo "/Fe$StartExe" $MainObj $EmulatorObj $DecoderObj $XdeltaCoreObj $MainRes `
        user32.lib gdi32.lib shell32.lib comdlg32.lib bcrypt.lib ole32.lib version.lib `
        /link /SUBSYSTEM:WINDOWS /MACHINE:X64 /DYNAMICBASE /HIGHENTROPYVA /NXCOMPAT /CETCOMPAT /GUARD:CF /OPT:REF /OPT:ICF /BREPRO
    if ($LASTEXITCODE -ne 0 -or -not [IO.File]::Exists($StartExe)) { throw 'Application build failed.' }

    $StartLength = (Get-Item -LiteralPath $StartExe).Length
    $StartHash = (Get-FileHash -LiteralPath $StartExe -Algorithm SHA256).Hash.ToLowerInvariant()

    $PackageRoot = [IO.Path]::Combine($StageRoot, [string]$Manifest.package.directory_name)
    $SupportRoot = [IO.Path]::Combine($PackageRoot, [string]$Manifest.package.support_directory)
    [IO.Directory]::CreateDirectory([IO.Path]::Combine($SupportRoot, 'patches')) | Out-Null
    [IO.Directory]::CreateDirectory([IO.Path]::Combine($SupportRoot, 'game')) | Out-Null
    [IO.Directory]::CreateDirectory([IO.Path]::Combine($SupportRoot, 'licenses')) | Out-Null
    [IO.Directory]::CreateDirectory([IO.Path]::Combine($SupportRoot, 'docs')) | Out-Null
    Copy-Item -LiteralPath $StartExe -Destination ([IO.Path]::Combine($PackageRoot, [string]$Manifest.package.app_filename))
    Copy-Item -LiteralPath $PatchPath -Destination ([IO.Path]::Combine($PackageRoot, ($Manifest.patch.relative_path -replace '/', '\')))
    Copy-Item -LiteralPath $CuePath -Destination ([IO.Path]::Combine($PackageRoot, ($Manifest.cue_template.relative_path -replace '/', '\')))
    $RuntimeManifest = @(
        'format=xenogears-mass-driver-patch-v1'
        ('source_size=' + [string][long]$Manifest.source.size)
        ('source_sha256=' + [string]$Manifest.source.sha256.ToLowerInvariant())
        ('patch_size=' + [string][long]$Manifest.patch.size)
        ('patch_sha256=' + [string]$Manifest.patch.sha256.ToLowerInvariant())
        ('cue_size=' + [string][long]$Manifest.cue_template.size)
        ('cue_sha256=' + [string]$Manifest.cue_template.sha256.ToLowerInvariant())
        ('output_size=' + [string][long]$Manifest.output.bin_size)
        ('output_sha256=' + [string]$Manifest.output.bin_sha256.ToLowerInvariant())
    ) -join "`n"
    Write-Utf8NoBom ([IO.Path]::Combine($SupportRoot, 'patch_manifest.txt')) ($RuntimeManifest + "`n")
    foreach ($Name in @('README_FIRST.md','CREDITS_AND_LICENSES.md')) {
        Copy-Item -LiteralPath ([IO.Path]::Combine($Here, 'docs', $Name)) -Destination ([IO.Path]::Combine($SupportRoot, 'docs', $Name))
    }
    Copy-Item -LiteralPath ([IO.Path]::Combine($PackageSource, 'licenses', 'Perfect_Works_GPL-3.0.txt')) -Destination ([IO.Path]::Combine($SupportRoot, 'licenses'))
    Copy-Item -LiteralPath ([IO.Path]::Combine($PackageSource, 'licenses', 'xdelta-Apache-2.0.txt')) -Destination ([IO.Path]::Combine($SupportRoot, 'licenses'))

    $Files = Get-ChildItem -LiteralPath $PackageRoot -Recurse -File | Sort-Object { $_.FullName.Substring($PackageRoot.Length + 1).Replace('\','/') }
    $ChecksumLines = foreach ($File in $Files) {
        $Relative = $File.FullName.Substring($PackageRoot.Length + 1).Replace('\','/')
        '{0}  {1}' -f ((Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()), $Relative
    }
    Write-Utf8NoBom ([IO.Path]::Combine($SupportRoot, 'SHA256SUMS.txt')) (($ChecksumLines -join "`n") + "`n")

    $Expected = @(
        [string]$Manifest.package.app_filename,[string]$Manifest.patch.relative_path,
        [string]$Manifest.cue_template.relative_path,
        (([string]$Manifest.package.support_directory) + '/patch_manifest.txt'),
        (([string]$Manifest.package.support_directory) + '/docs/README_FIRST.md'),
        (([string]$Manifest.package.support_directory) + '/docs/CREDITS_AND_LICENSES.md'),
        (([string]$Manifest.package.support_directory) + '/SHA256SUMS.txt'),
        (([string]$Manifest.package.support_directory) + '/licenses/Perfect_Works_GPL-3.0.txt'),
        (([string]$Manifest.package.support_directory) + '/licenses/xdelta-Apache-2.0.txt')
    ) | Sort-Object
    $Actual = Get-ChildItem -LiteralPath $PackageRoot -Recurse -File | ForEach-Object {
        $_.FullName.Substring($PackageRoot.Length + 1).Replace('\','/')
    } | Sort-Object
    if (Compare-Object $Expected $Actual -CaseSensitive) { throw 'Package inventory differs from the build allowlist.' }

    foreach ($File in Get-ChildItem -LiteralPath $PackageRoot -Recurse -File) {
        $Bytes = [IO.File]::ReadAllBytes($File.FullName)
        $Ascii = [Text.Encoding]::ASCII.GetString($Bytes)
        $Unicode = [Text.Encoding]::Unicode.GetString($Bytes)
        foreach ($Text in @($Ascii, $Unicode)) {
            if ($Text -match '(?i)[A-Z]:\\[^\x00\r\n]{2,220}\\(?:src|source|build|temp|tmp|work)\\') {
                throw "Privacy check failed: $(Get-Relative $PackageRoot $File.FullName) contains an absolute development path."
            }
        }
    }

    [IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null
    $OutputPrefix = $OutputDirectory.TrimEnd('\') + '\'
    if ([IO.Path]::GetDirectoryName($FinalRoot) -ine $OutputDirectory -or
        [IO.Path]::GetDirectoryName($ZipPath) -ine $OutputDirectory -or
        -not $FinalRoot.StartsWith($OutputPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        -not $ZipPath.StartsWith($OutputPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Package output paths must be direct children of OutputDirectory.'
    }
    if (([IO.Directory]::Exists($FinalRoot) -or [IO.File]::Exists($ZipPath)) -and -not $Force) {
        throw 'Package output already exists; use -Force to replace it.'
    }
    if ([IO.Directory]::Exists($FinalRoot)) { Remove-Item -LiteralPath $FinalRoot -Recurse -Force }
    if ([IO.File]::Exists($ZipPath)) { Remove-Item -LiteralPath $ZipPath -Force }
    [IO.Directory]::Move($PackageRoot, $FinalRoot)
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $ZipStream = [IO.File]::Open($ZipPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    try {
        $Archive = New-Object IO.Compression.ZipArchive($ZipStream, [IO.Compression.ZipArchiveMode]::Create, $true)
        try {
            $FixedTime = [DateTimeOffset]::Parse('2026-01-01T00:00:00Z')
            $ArchiveFiles = Get-ChildItem -LiteralPath $FinalRoot -Recurse -File | Sort-Object {
                $_.FullName.Substring($OutputDirectory.TrimEnd('\').Length + 1).Replace('\','/')
            }
            foreach ($File in $ArchiveFiles) {
                $EntryName = $File.FullName.Substring($OutputDirectory.TrimEnd('\').Length + 1).Replace('\','/')
                $Entry = $Archive.CreateEntry($EntryName, [IO.Compression.CompressionLevel]::Optimal)
                $Entry.LastWriteTime = $FixedTime
                $Entry.ExternalAttributes = 0
                $Input = [IO.File]::OpenRead($File.FullName)
                $Output = $Entry.Open()
                try { $Input.CopyTo($Output) } finally { $Output.Dispose(); $Input.Dispose() }
            }
        }
        finally { $Archive.Dispose() }
    }
    finally { $ZipStream.Dispose() }

    $ReadStream = [IO.File]::OpenRead($ZipPath)
    try {
        $ReadArchive = New-Object IO.Compression.ZipArchive($ReadStream, [IO.Compression.ZipArchiveMode]::Read, $false)
        try {
            $ZipNames = @($ReadArchive.Entries | ForEach-Object FullName)
            $ExpectedZipNames = @($Actual | ForEach-Object { ([string]$Manifest.package.directory_name) + '/' + $_ })
            if ($ZipNames.Count -ne $ExpectedZipNames.Count -or (Compare-Object $ExpectedZipNames $ZipNames -CaseSensitive)) {
                throw 'ZIP inventory differs from the build allowlist.'
            }
            $UniqueZipNames = @($ZipNames | Sort-Object -Unique)
            if ($UniqueZipNames.Count -ne $ZipNames.Count) { throw 'ZIP contains duplicate case-insensitive entry names.' }
            $Reserved = @('CON','PRN','AUX','NUL','COM1','COM2','COM3','COM4','COM5','COM6','COM7','COM8','COM9','LPT1','LPT2','LPT3','LPT4','LPT5','LPT6','LPT7','LPT8','LPT9')
            foreach ($Entry in $ReadArchive.Entries) {
                if ($Entry.FullName.Contains('\') -or $Entry.FullName.StartsWith('/') -or
                    $Entry.FullName.Contains('../') -or $Entry.FullName.Contains('/./') -or
                    [IO.Path]::IsPathRooted($Entry.FullName)) {
                    throw "Unsafe ZIP entry name: $($Entry.FullName)"
                }
                foreach ($Segment in ($Entry.FullName -split '/')) {
                    $Stem = [IO.Path]::GetFileNameWithoutExtension($Segment).TrimEnd(' ', '.').ToUpperInvariant()
                    if ([string]::IsNullOrWhiteSpace($Segment) -or $Segment.EndsWith(' ') -or
                        $Segment.EndsWith('.') -or $Segment.Contains(':') -or
                        $Segment.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0 -or $Reserved -contains $Stem) {
                        throw "Unsafe ZIP path segment: $Segment"
                    }
                }
                if ($Entry.ExternalAttributes -ne 0) { throw "ZIP entry has unexpected external attributes: $($Entry.FullName)" }
                $Relative = $Entry.FullName.Substring(([string]$Manifest.package.directory_name).Length + 1)
                $SourceFile = [IO.Path]::Combine($FinalRoot, ($Relative -replace '/', '\'))
                $EntryStream = $Entry.Open()
                $Algorithm = [Security.Cryptography.SHA256]::Create()
                try { $EntryHash = [BitConverter]::ToString($Algorithm.ComputeHash($EntryStream)).Replace('-','').ToLowerInvariant() }
                finally { $Algorithm.Dispose(); $EntryStream.Dispose() }
                if ($EntryHash -ne (Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()) {
                    throw "ZIP entry differs from packaged file: $Relative"
                }
            }
        }
        finally { $ReadArchive.Dispose() }
    }
    finally { $ReadStream.Dispose() }
    Write-Host "Built folder: $FinalRoot"
    Write-Host "Built ZIP: $ZipPath"
    Write-Host "ZIP size: $((Get-Item -LiteralPath $ZipPath).Length)"
    Write-Host "ZIP SHA-256: $((Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant())"
    Write-Host "Application SHA-256: $StartHash"
}
finally {
    foreach ($Temporary in @($BuildRoot, $StageRoot)) {
        if ([IO.Directory]::Exists($Temporary)) {
            $Resolved = [IO.Path]::GetFullPath($Temporary)
            if (-not $Resolved.StartsWith(($Here.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase) -and
                -not $Resolved.StartsWith(($OutputDirectory.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) {
                throw "Refusing to clean unexpected path: $Resolved"
            }
            Remove-Item -LiteralPath $Resolved -Recurse -Force
        }
    }
}
