[CmdletBinding()]
param(
    [string]$BuildManifest,
    [string]$PackageDirectory,
    [string]$ZipPath,
    [string]$SourceBin,
    [string]$QaParent,
    [switch]$SkipDynamic
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$Here = [IO.Path]::GetFullPath($PSScriptRoot)
$RepoRoot = [IO.Path]::GetFullPath([IO.Path]::Combine($Here, '..'))
if ([string]::IsNullOrWhiteSpace($BuildManifest)) {
    $BuildManifest = [IO.Path]::Combine($Here, 'build_manifest.json')
}
$BuildManifest = [IO.Path]::GetFullPath($BuildManifest)
$Contract = Get-Content -LiteralPath $BuildManifest -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Contract.format -cne 'xenogears-mass-driver-build-v1') { throw 'Build manifest format is wrong.' }
if ([string]::IsNullOrWhiteSpace($PackageDirectory)) {
    $PackageDirectory = [IO.Path]::Combine($RepoRoot, 'dist', [string]$Contract.package.directory_name)
}
if ([string]::IsNullOrWhiteSpace($ZipPath)) {
    $ZipPath = [IO.Path]::Combine($RepoRoot, 'dist', [string]$Contract.package.zip_filename)
}
$PackageDirectory = [IO.Path]::GetFullPath($PackageDirectory)
$ZipPath = [IO.Path]::GetFullPath($ZipPath)
if (-not [IO.Directory]::Exists($PackageDirectory)) { throw "Package directory is missing: $PackageDirectory" }
if (-not [IO.File]::Exists($ZipPath)) { throw "Package ZIP is missing: $ZipPath" }

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Get-Relative([string]$Root, [string]$Path) {
    return $Path.Substring($Root.TrimEnd('\').Length + 1).Replace('\','/')
}

$SupportName = [string]$Contract.package.support_directory
$AppName = [string]$Contract.package.app_filename
$Expected = @(
    $AppName,[string]$Contract.patch.relative_path,[string]$Contract.cue_template.relative_path,
    "$SupportName/patch_manifest.txt","$SupportName/docs/README_FIRST.md",
    "$SupportName/docs/CREDITS_AND_LICENSES.md",
    "$SupportName/SHA256SUMS.txt","$SupportName/licenses/Perfect_Works_GPL-3.0.txt",
    "$SupportName/licenses/xdelta-Apache-2.0.txt"
) | Sort-Object
$Actual = @(Get-ChildItem -LiteralPath $PackageDirectory -Recurse -File | ForEach-Object {
    Get-Relative $PackageDirectory $_.FullName
} | Sort-Object)
Assert-True (-not (Compare-Object $Expected $Actual -CaseSensitive)) 'Package inventory differs from the build allowlist.'
$RootEntries = @(Get-ChildItem -LiteralPath $PackageDirectory -Force)
Assert-True ($RootEntries.Count -eq 2) 'Package root must contain exactly the app and support directory.'
Assert-True ([IO.File]::Exists([IO.Path]::Combine($PackageDirectory, $AppName))) 'Root app is missing.'
Assert-True ([IO.Directory]::Exists([IO.Path]::Combine($PackageDirectory, $SupportName))) 'Support directory is missing.'
$PackagedExecutables = @(Get-ChildItem -LiteralPath $PackageDirectory -Recurse -File -Filter '*.exe')
Assert-True ($PackagedExecutables.Count -eq 1 -and $PackagedExecutables[0].Name -ceq $AppName) 'The app must be the package''s only executable.'

$PrivacyNeedles = @(
    $RepoRoot,[Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile),
    [IO.Path]::GetTempPath().TrimEnd('\'),'\work\','\Users\'
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique
foreach ($File in Get-ChildItem -LiteralPath $PackageDirectory -Recurse -File) {
    $Bytes = [IO.File]::ReadAllBytes($File.FullName)
    $Ascii = [Text.Encoding]::ASCII.GetString($Bytes)
    $Unicode = [Text.Encoding]::Unicode.GetString($Bytes)
    foreach ($Needle in $PrivacyNeedles) {
        Assert-True (-not $Ascii.Contains($Needle) -and -not $Unicode.Contains($Needle)) "Privacy marker found in $(Get-Relative $PackageDirectory $File.FullName)"
    }
    foreach ($Text in @($Ascii, $Unicode)) {
        Assert-True ($Text -notmatch '(?i)[A-Z]:\\[^\x00\r\n]{2,220}\\(?:src|source|build|temp|tmp|work)\\') "Absolute development path found in $(Get-Relative $PackageDirectory $File.FullName)"
    }
}

$Support = [IO.Path]::Combine($PackageDirectory, $SupportName)
$RuntimeManifest = @(
    'format=xenogears-mass-driver-patch-v1'
    ('source_size=' + [string][long]$Contract.source.size)
    ('source_sha256=' + [string]$Contract.source.sha256.ToLowerInvariant())
    ('patch_size=' + [string][long]$Contract.patch.size)
    ('patch_sha256=' + [string]$Contract.patch.sha256.ToLowerInvariant())
    ('cue_size=' + [string][long]$Contract.cue_template.size)
    ('cue_sha256=' + [string]$Contract.cue_template.sha256.ToLowerInvariant())
    ('output_size=' + [string][long]$Contract.output.bin_size)
    ('output_sha256=' + [string]$Contract.output.bin_sha256.ToLowerInvariant())
) -join "`n"
$RuntimePath = [IO.Path]::Combine($Support, 'patch_manifest.txt')
Assert-True ((Get-Content -LiteralPath $RuntimePath -Raw -Encoding UTF8) -ceq ($RuntimeManifest + "`n")) 'Runtime manifest differs from the build contract.'
foreach ($Executable in @(
    @{ Path = [IO.Path]::Combine($PackageDirectory, $AppName) }
)) {
    $Item = Get-Item -LiteralPath $Executable.Path
    Assert-True ($Item.Length -gt 0) "Executable is empty: $($Executable.Path)"
    $Bytes = [IO.File]::ReadAllBytes($Executable.Path)
    $Ascii = [Text.Encoding]::ASCII.GetString($Bytes); $Unicode = [Text.Encoding]::Unicode.GetString($Bytes)
    foreach ($Forbidden in @('CREATE_SUSPENDED','CREATE_NO_WINDOW','SW_HIDE','missile')) {
        Assert-True (-not $Ascii.Contains($Forbidden) -and -not $Unicode.Contains($Forbidden)) "Executable contains forbidden marker '$Forbidden': $($Executable.Path)"
    }
}

$Checksums = New-Object 'Collections.Generic.Dictionary[string,string]' ([StringComparer]::Ordinal)
foreach ($Line in (Get-Content -LiteralPath ([IO.Path]::Combine($Support, 'SHA256SUMS.txt')) -Encoding UTF8)) {
    Assert-True ($Line -match '^([0-9a-f]{64})  ([^\\]+)$') "Malformed SHA256SUMS line: $Line"
    Assert-True (-not $Checksums.ContainsKey($Matches[2])) "Duplicate SHA256SUMS path: $($Matches[2])"
    $Checksums[$Matches[2]] = $Matches[1]
}
$ExpectedChecksums = @($Expected | Where-Object { $_ -cne "$SupportName/SHA256SUMS.txt" })
Assert-True ($Checksums.Count -eq $ExpectedChecksums.Count) 'SHA256SUMS entry count is wrong.'
foreach ($Relative in $ExpectedChecksums) {
    Assert-True $Checksums.ContainsKey($Relative) "SHA256SUMS is missing $Relative"
    $Hash = (Get-FileHash -LiteralPath ([IO.Path]::Combine($PackageDirectory, ($Relative -replace '/', '\'))) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($Hash -ceq $Checksums[$Relative]) "SHA256SUMS mismatch for $Relative"
}

Add-Type -AssemblyName System.IO.Compression
$ZipStream = [IO.File]::OpenRead($ZipPath)
try {
    $Archive = New-Object IO.Compression.ZipArchive($ZipStream, [IO.Compression.ZipArchiveMode]::Read, $false)
    try {
        $ExpectedZip = @($Actual | ForEach-Object { ([string]$Contract.package.directory_name) + '/' + $_ })
        $Names = @($Archive.Entries | ForEach-Object FullName)
        Assert-True ($Names.Count -eq $ExpectedZip.Count -and -not (Compare-Object $ExpectedZip $Names -CaseSensitive)) 'ZIP inventory differs from package directory.'
        $OrdinalNames = New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
        $FoldedNames = New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
        foreach ($Name in $Names) {
            Assert-True ($OrdinalNames.Add($Name)) 'ZIP contains duplicate entry names.'
            Assert-True ($FoldedNames.Add($Name)) 'ZIP contains case-insensitive colliding entry names.'
        }
        $Reserved = @('CON','PRN','AUX','NUL','COM1','COM2','COM3','COM4','COM5','COM6','COM7','COM8','COM9','LPT1','LPT2','LPT3','LPT4','LPT5','LPT6','LPT7','LPT8','LPT9')
        foreach ($Entry in $Archive.Entries) {
            Assert-True (-not $Entry.FullName.Contains('\') -and -not $Entry.FullName.Contains('../') -and
                -not $Entry.FullName.Contains('/./') -and -not $Entry.FullName.StartsWith('/') -and
                -not [IO.Path]::IsPathRooted($Entry.FullName)) "Unsafe ZIP entry: $($Entry.FullName)"
            foreach ($Segment in ($Entry.FullName -split '/')) {
                $Stem = [IO.Path]::GetFileNameWithoutExtension($Segment).TrimEnd(' ', '.').ToUpperInvariant()
                Assert-True (-not [string]::IsNullOrWhiteSpace($Segment) -and -not $Segment.EndsWith(' ') -and
                    -not $Segment.EndsWith('.') -and -not $Segment.Contains(':') -and
                    $Segment.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -lt 0 -and $Reserved -notcontains $Stem) "Unsafe ZIP segment: $Segment"
            }
            Assert-True ($Entry.ExternalAttributes -eq 0) "ZIP entry has unexpected external attributes: $($Entry.FullName)"
            Assert-True ($Entry.LastWriteTime.DateTime -eq [DateTime]::Parse('2026-01-01T00:00:00')) "ZIP timestamp is not fixed: $($Entry.FullName)"
            $Relative = $Entry.FullName.Substring(([string]$Contract.package.directory_name).Length + 1)
            $SourcePath = [IO.Path]::Combine($PackageDirectory, ($Relative -replace '/', '\'))
            $Reader = $Entry.Open(); $Algorithm = [Security.Cryptography.SHA256]::Create()
            try { $EntryHash = [BitConverter]::ToString($Algorithm.ComputeHash($Reader)).Replace('-','').ToLowerInvariant() }
            finally { $Algorithm.Dispose(); $Reader.Dispose() }
            Assert-True ($EntryHash -ceq (Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash.ToLowerInvariant()) "ZIP content mismatch: $Relative"
        }
    } finally { $Archive.Dispose() }
} finally { $ZipStream.Dispose() }

$App = [IO.Path]::Combine($PackageDirectory, $AppName)
function Invoke-AppAt([string]$Executable, [string]$WorkingDirectory, [string]$Arguments, [hashtable]$Environment = @{}) {
    $Info = New-Object Diagnostics.ProcessStartInfo
    $Info.FileName = $Executable; $Info.Arguments = $Arguments; $Info.WorkingDirectory = $WorkingDirectory
    $Info.UseShellExecute = $false; $Info.RedirectStandardOutput = $true; $Info.RedirectStandardError = $true
    foreach ($Name in $Environment.Keys) { $Info.EnvironmentVariables[[string]$Name] = [string]$Environment[$Name] }
    $Process = [Diagnostics.Process]::Start($Info)
    $Out = $Process.StandardOutput.ReadToEnd(); $Err = $Process.StandardError.ReadToEnd(); $Process.WaitForExit()
    return @{ ExitCode = $Process.ExitCode; Out = $Out; Err = $Err }
}
function Invoke-App([string]$Arguments, [hashtable]$Environment = @{}) {
    return Invoke-AppAt $App $PackageDirectory $Arguments $Environment
}
$Check = Invoke-App '--headless --check-package'
Assert-True ($Check.ExitCode -eq 0 -and $Check.Out.Trim() -ceq 'PACKAGE_OK' -and [string]::IsNullOrEmpty($Check.Err)) 'App package self-check failed.'

if (-not $SkipDynamic) {
    if ([string]::IsNullOrWhiteSpace($SourceBin)) { throw 'Dynamic verification requires -SourceBin or -SkipDynamic.' }
    $SourceBin = [IO.Path]::GetFullPath($SourceBin)
    if ([string]::IsNullOrWhiteSpace($QaParent)) { $QaParent = [IO.Path]::Combine($RepoRoot, 'work') }
    $QaParent = [IO.Path]::GetFullPath($QaParent); [IO.Directory]::CreateDirectory($QaParent) | Out-Null
    $QaRoot = [IO.Path]::Combine($QaParent, ('MassDriverPackageQA.' + [Guid]::NewGuid().ToString('N')))
    [IO.Directory]::CreateDirectory($QaRoot) | Out-Null
    try {
        function Assert-ManifestRejected([string]$Name, [string]$Content) {
            $Fixture = [IO.Path]::Combine($QaRoot, ('manifest-' + $Name))
            [IO.Directory]::CreateDirectory($Fixture) | Out-Null
            Copy-Item -Path ([IO.Path]::Combine($PackageDirectory, '*')) -Destination $Fixture -Recurse -Force
            $FixtureManifest = [IO.Path]::Combine($Fixture, $SupportName, 'patch_manifest.txt')
            [IO.File]::WriteAllText($FixtureManifest, $Content, (New-Object Text.UTF8Encoding($false)))
            $FixtureApp = [IO.Path]::Combine($Fixture, $AppName)
            $Rejected = Invoke-AppAt $FixtureApp $Fixture '--headless --check-package'
            Assert-True ($Rejected.ExitCode -eq 21 -and $Rejected.Err.Contains('PACKAGE_ERROR=21:')) "Unsafe runtime manifest was accepted: $Name"
        }

        $CanonicalManifest = Get-Content -LiteralPath $RuntimePath -Raw -Encoding UTF8
        $ManifestLines = @($CanonicalManifest.TrimEnd("`n") -split "`n")
        Assert-ManifestRejected 'blank' ''
        Assert-ManifestRejected 'nul' ($CanonicalManifest + [char]0)
        Assert-ManifestRejected 'non-ascii' ($CanonicalManifest.Replace('format=', ('format=' + [char]0x00e9)))
        Assert-ManifestRejected 'too-large' ('x' * 4097)
        Assert-ManifestRejected 'unknown-key' ($CanonicalManifest + "unknown=value`n")
        Assert-ManifestRejected 'missing-key' (($ManifestLines | Where-Object { -not $_.StartsWith('patch_sha256=') }) -join "`n")
        Assert-ManifestRejected 'duplicate-key' ($CanonicalManifest + $ManifestLines[1] + "`n")
        Assert-ManifestRejected 'uppercase-hash' ($CanonicalManifest.Replace([string]$Contract.source.sha256, ([string]$Contract.source.sha256).ToUpperInvariant()))
        Assert-ManifestRejected 'short-hash' ($CanonicalManifest.Replace([string]$Contract.source.sha256, 'abc'))
        Assert-ManifestRejected 'signed-size' ($CanonicalManifest.Replace(('source_size=' + [string][long]$Contract.source.size), 'source_size=-1'))
        Assert-ManifestRejected 'overflow-size' ($CanonicalManifest.Replace(('source_size=' + [string][long]$Contract.source.size), 'source_size=18446744073709551616'))
        Assert-ManifestRejected 'small-source' ($CanonicalManifest.Replace(('source_size=' + [string][long]$Contract.source.size), 'source_size=1'))
        Assert-ManifestRejected 'large-output' ($CanonicalManifest.Replace(('output_size=' + [string][long]$Contract.output.bin_size), 'output_size=1073741825'))
        Assert-ManifestRejected 'crlf' ($CanonicalManifest.Replace("`n", "`r`n"))

        $SourceBefore = Get-Item -LiteralPath $SourceBin
        $SourceLengthBefore = $SourceBefore.Length
        $SourceWriteBefore = $SourceBefore.LastWriteTimeUtc
        $SourceHashBefore = (Get-FileHash -LiteralPath $SourceBin -Algorithm SHA256).Hash
        $PackageBefore = @(Get-ChildItem -LiteralPath $PackageDirectory -Recurse -File | Sort-Object FullName | ForEach-Object {
            (Get-Relative $PackageDirectory $_.FullName) + '|' + $_.Length + '|' + $_.LastWriteTimeUtc.Ticks + '|' +
                (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        })
        $Output = [IO.Path]::Combine($QaRoot, 'game output')
        $Run = Invoke-App ('--headless --source "' + $SourceBin.Replace('"','\"') + '" --output "' + $Output.Replace('"','\"') + '"')
        Assert-True ($Run.ExitCode -eq 0 -and $Run.Out.Contains('BUILD_SUCCESS=') -and [string]::IsNullOrEmpty($Run.Err)) "Dynamic patch failed: $($Run.Err)"
        $OutputBin = [IO.Path]::Combine($Output, [string]$Contract.output.bin_name)
        $OutputCue = [IO.Path]::Combine($Output, [string]$Contract.output.cue_name)
        Assert-True ((Get-Item -LiteralPath $OutputBin).Length -eq [long]$Contract.output.bin_size) 'Output BIN size is wrong.'
        Assert-True ((Get-FileHash -LiteralPath $OutputBin -Algorithm SHA256).Hash.ToLowerInvariant() -ceq [string]$Contract.output.bin_sha256) 'Output BIN hash is wrong.'
        Assert-True ((Get-Item -LiteralPath $OutputCue).Length -eq [long]$Contract.output.cue_size) 'Output CUE size is wrong.'
        Assert-True ((Get-FileHash -LiteralPath $OutputCue -Algorithm SHA256).Hash.ToLowerInvariant() -ceq [string]$Contract.output.cue_sha256) 'Output CUE hash is wrong.'

        # A second build against an already verified output must be a true no-op.
        $Sentinel = [IO.Path]::Combine($Output, 'qa-user-file.keep')
        [IO.File]::WriteAllText($Sentinel, 'preserve', (New-Object Text.UTF8Encoding($false)))
        $BeforeBin = Get-Item -LiteralPath $OutputBin
        $BeforeCue = Get-Item -LiteralPath $OutputCue
        $BeforeBinWrite = $BeforeBin.LastWriteTimeUtc
        $BeforeCueWrite = $BeforeCue.LastWriteTimeUtc
        $BeforeBinHash = (Get-FileHash -LiteralPath $OutputBin -Algorithm SHA256).Hash
        $BeforeCueHash = (Get-FileHash -LiteralPath $OutputCue -Algorithm SHA256).Hash
        $NoOp = Invoke-App ('--headless --source "' + $SourceBin.Replace('"','\"') + '" --output "' + $Output.Replace('"','\"') + '"')
        Assert-True ($NoOp.ExitCode -eq 0 -and $NoOp.Out.Contains('already ready') -and $NoOp.Out.Contains('BUILD_SUCCESS=')) 'Existing exact output was not handled as a successful no-op.'
        Assert-True ((Get-FileHash -LiteralPath $OutputBin -Algorithm SHA256).Hash -ceq $BeforeBinHash -and
            (Get-Item -LiteralPath $OutputBin).LastWriteTimeUtc -eq $BeforeBinWrite) 'No-op changed the existing BIN.'
        Assert-True ((Get-FileHash -LiteralPath $OutputCue -Algorithm SHA256).Hash -ceq $BeforeCueHash -and
            (Get-Item -LiteralPath $OutputCue).LastWriteTimeUtc -eq $BeforeCueWrite) 'No-op changed the existing CUE.'
        Assert-True ((Get-Content -LiteralPath $Sentinel -Raw) -ceq 'preserve') 'No-op changed or removed an unrelated user file.'

        # A bad source selection must not damage a valid build or make Play diagnostics fail.
        $WrongSource = [IO.Path]::Combine($QaRoot, 'wrong-disc.bin')
        [IO.File]::WriteAllBytes($WrongSource, [byte[]](0, 1, 2, 3))
        $Wrong = Invoke-App ('--headless --source "' + $WrongSource.Replace('"','\"') + '" --output "' + $Output.Replace('"','\"') + '"')
        Assert-True ($Wrong.ExitCode -eq 11 -and $Wrong.Err.Contains('BUILD_ERROR=11:')) 'Wrong-size source was not rejected clearly.'
        Assert-True ((Get-FileHash -LiteralPath $OutputBin -Algorithm SHA256).Hash -ceq $BeforeBinHash -and
            (Get-FileHash -LiteralPath $OutputCue -Algorithm SHA256).Hash -ceq $BeforeCueHash) 'Wrong source changed the valid output.'

        # Use a known native Windows application as a QA-only custom emulator fixture.
        # GetBinaryTypeW intentionally rejects PowerShell Add-Type's managed AnyCPU EXEs.
        $Mock = [IO.Path]::Combine($QaRoot, 'qa_custom_emulator.exe')
        $NativeFixture = [IO.Path]::Combine([Environment]::GetFolderPath([Environment+SpecialFolder]::System), 'notepad.exe')
        Assert-True ([IO.File]::Exists($NativeFixture)) 'Native QA custom-emulator fixture is unavailable.'
        [IO.File]::Copy($NativeFixture, $Mock)
        Assert-True ([IO.File]::Exists($Mock)) 'QA custom-emulator fixture was not built.'
        $GameArgument = '--game "' + $Output.Replace('"','\"') + '"'
        $NoEmulator = Invoke-App ('--headless --play-check ' + $GameArgument + ' --no-emulator')
        Assert-True ($NoEmulator.ExitCode -eq 4 -and $NoEmulator.Out.Contains('EMULATOR_REQUIRED')) 'Forced no-emulator Play path is wrong.'
        $MissingEmulator = Invoke-App ('--headless --play-check ' + $GameArgument + ' --emulator "' + ([IO.Path]::Combine($QaRoot, 'missing.exe')) + '"')
        Assert-True ($MissingEmulator.ExitCode -eq 4 -and $MissingEmulator.Out.Contains('EMULATOR_REQUIRED')) 'Missing emulator was not rejected.'
        $SelfEmulator = Invoke-App ('--headless --play-check ' + $GameArgument + ' --emulator "' + $App.Replace('"','\"') + '"')
        Assert-True ($SelfEmulator.ExitCode -eq 4 -and $SelfEmulator.Out.Contains('EMULATOR_REQUIRED')) 'The app incorrectly accepted itself as an emulator.'

        $Custom = Invoke-App ('--headless --play-check ' + $GameArgument + ' --emulator "' + $Mock.Replace('"','\"') + '"')
        $CustomPredicates = @(
            ($Custom.ExitCode -eq 0)
            $Custom.Out.Contains('EMULATOR_NAME=')
            $Custom.Out.Contains('(custom)')
            $Custom.Out.Contains('EMULATOR_COMMAND=')
            $Custom.Out.Contains($OutputCue)
        )
        Assert-True (-not ($CustomPredicates -contains $false)) ("Custom-emulator dry-run is wrong. Exit={0}; Predicates={1}; Out={2}; Err={3}" -f
            $Custom.ExitCode, ($CustomPredicates -join ','), ($Custom.Out -replace "`r?`n", ' | '), ($Custom.Err -replace "`r?`n", ' | '))
        Assert-True (-not (Get-Process -Name 'qa_custom_emulator' -ErrorAction SilentlyContinue)) 'Play diagnostics launched the custom emulator.'

        $IsolatedLocal = [IO.Path]::Combine($QaRoot, 'isolated-local')
        $DetectedDirectory = [IO.Path]::Combine($IsolatedLocal, 'Programs', 'DuckStation')
        [IO.Directory]::CreateDirectory($DetectedDirectory) | Out-Null
        $DetectedExe = [IO.Path]::Combine($DetectedDirectory, 'duckstation.exe')
        [IO.File]::Copy($Mock, $DetectedExe)
        $EmptyProgramFiles = [IO.Path]::Combine($QaRoot, 'empty-program-files')
        $EmptyProgramFilesX86 = [IO.Path]::Combine($QaRoot, 'empty-program-files-x86')
        $EmptyAppData = [IO.Path]::Combine($QaRoot, 'empty-appdata')
        [IO.Directory]::CreateDirectory($EmptyProgramFiles) | Out-Null
        [IO.Directory]::CreateDirectory($EmptyProgramFilesX86) | Out-Null
        [IO.Directory]::CreateDirectory($EmptyAppData) | Out-Null
        $DetectedEnvironment = @{
            LOCALAPPDATA = $IsolatedLocal; APPDATA = $EmptyAppData
            ProgramFiles = $EmptyProgramFiles; 'ProgramFiles(x86)' = $EmptyProgramFilesX86
        }
        $Detected = Invoke-App ('--headless --play-check ' + $GameArgument) $DetectedEnvironment
        Assert-True ($Detected.ExitCode -eq 0 -and $Detected.Out.Contains('EMULATOR_NAME=DuckStation') -and
            $Detected.Out.Contains($DetectedExe) -and $Detected.Out.Contains('-nofullscreen -fastboot --')) 'Isolated DuckStation detection dry-run is wrong.'
        Assert-True (-not (Get-Process -Name 'duckstation' -ErrorAction SilentlyContinue)) 'Play diagnostics launched the detected emulator.'

        # Package self-check must reject changed runtime data without creating files.
        $TamperedPackage = [IO.Path]::Combine($QaRoot, 'tampered-package')
        [IO.Directory]::CreateDirectory($TamperedPackage) | Out-Null
        Copy-Item -Path ([IO.Path]::Combine($PackageDirectory, '*')) -Destination $TamperedPackage -Recurse -Force
        $TamperedPatch = [IO.Path]::Combine($TamperedPackage, ($Contract.patch.relative_path -replace '/', '\'))
        $TamperStream = [IO.File]::Open($TamperedPatch, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        try {
            $TamperStream.Position = $TamperStream.Length - 1
            $Original = $TamperStream.ReadByte()
            $TamperStream.Position = $TamperStream.Length - 1
            $TamperStream.WriteByte([byte]($Original -bxor 1))
        } finally { $TamperStream.Dispose() }
        $TamperedApp = [IO.Path]::Combine($TamperedPackage, $AppName)
        $Tampered = Invoke-AppAt $TamperedApp $TamperedPackage '--headless --check-package'
        Assert-True ($Tampered.ExitCode -eq 21 -and $Tampered.Err.Contains('PACKAGE_ERROR=21:')) 'Changed patch was not rejected by package self-check.'

        $SourceAfter = Get-Item -LiteralPath $SourceBin
        Assert-True ($SourceAfter.Length -eq $SourceLengthBefore -and $SourceAfter.LastWriteTimeUtc -eq $SourceWriteBefore -and
            (Get-FileHash -LiteralPath $SourceBin -Algorithm SHA256).Hash -ceq $SourceHashBefore) 'The source BIN changed during verification.'
        $PackageAfter = @(Get-ChildItem -LiteralPath $PackageDirectory -Recurse -File | Sort-Object FullName | ForEach-Object {
            (Get-Relative $PackageDirectory $_.FullName) + '|' + $_.Length + '|' + $_.LastWriteTimeUtc.Ticks + '|' +
                (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        })
        Assert-True (-not (Compare-Object $PackageBefore $PackageAfter -CaseSensitive)) 'The package wrote settings or changed its distributed files.'
    } finally {
        if ([IO.Directory]::Exists($QaRoot) -and [IO.Path]::GetFileName($QaRoot) -match '^MassDriverPackageQA\.[0-9a-f]{32}$' -and
            $QaRoot.StartsWith(($QaParent.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $QaRoot -Recurse -Force
        }
    }
}

Write-Host 'Xenogears Cut Content Patcher package verification: PASS'
Write-Host "ZIP SHA-256: $((Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant())"
