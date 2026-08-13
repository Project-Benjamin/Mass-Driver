[CmdletBinding()]
param(
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
$Contract = Get-Content -LiteralPath ([IO.Path]::Combine($Here, 'release_manifest.json')) -Raw -Encoding UTF8 | ConvertFrom-Json
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
    $AppName,[string]$Contract.decoder.relative_path,
    [string]$Contract.patch.relative_path,[string]$Contract.cue_template.relative_path,
    "$SupportName/patch_manifest.json","$SupportName/docs/README_FIRST.md",
    "$SupportName/docs/RELEASE_NOTES.md","$SupportName/docs/TEST_CHECKLIST.md",
    "$SupportName/docs/FEEDBACK_TEMPLATE.md","$SupportName/docs/CREDITS_AND_LICENSES.md",
    "$SupportName/SHA256SUMS.txt","$SupportName/licenses/Perfect_Works_GPL-3.0.txt",
    "$SupportName/licenses/xdelta-Apache-2.0.txt","$SupportName/licenses/xz-libLZMA-0BSD.txt"
) | Sort-Object
$Actual = @(Get-ChildItem -LiteralPath $PackageDirectory -Recurse -File | ForEach-Object {
    Get-Relative $PackageDirectory $_.FullName
} | Sort-Object)
Assert-True (-not (Compare-Object $Expected $Actual -CaseSensitive)) 'Package inventory differs from the one-app allowlist.'
$RootEntries = @(Get-ChildItem -LiteralPath $PackageDirectory -Force)
Assert-True ($RootEntries.Count -eq 2) 'Package root must contain exactly the app and support directory.'
Assert-True ([IO.File]::Exists([IO.Path]::Combine($PackageDirectory, $AppName))) 'Root app is missing.'
Assert-True ([IO.Directory]::Exists([IO.Path]::Combine($PackageDirectory, $SupportName))) 'Support directory is missing.'

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
$Public = Get-Content -LiteralPath ([IO.Path]::Combine($Support, 'patch_manifest.json')) -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ($Public.format -ceq 'xenogears-mass-driver-one-app-v1') 'Public manifest format is wrong.'
foreach ($Executable in @(
    @{ Path = [IO.Path]::Combine($PackageDirectory, $AppName); Size = [long]$Public.package.app_size; Hash = [string]$Public.package.app_sha256 },
    @{ Path = [IO.Path]::Combine($Support, 'tools', 'xdelta3.exe'); Size = [long]$Public.decoder.size; Hash = [string]$Public.decoder.sha256 }
)) {
    $Item = Get-Item -LiteralPath $Executable.Path
    Assert-True ($Item.Length -eq $Executable.Size) "Executable size mismatch: $($Executable.Path)"
    Assert-True ((Get-FileHash -LiteralPath $Executable.Path -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $Executable.Hash) "Executable hash mismatch: $($Executable.Path)"
    $Bytes = [IO.File]::ReadAllBytes($Executable.Path)
    $Ascii = [Text.Encoding]::ASCII.GetString($Bytes); $Unicode = [Text.Encoding]::Unicode.GetString($Bytes)
    foreach ($Forbidden in @('CREATE_SUSPENDED','CREATE_NO_WINDOW','SW_HIDE')) {
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
    $QaRoot = [IO.Path]::Combine($QaParent, ('MassDriverOneAppQA.' + [Guid]::NewGuid().ToString('N')))
    [IO.Directory]::CreateDirectory($QaRoot) | Out-Null
    try {
        $SourceBefore = Get-Item -LiteralPath $SourceBin
        $SourceLengthBefore = $SourceBefore.Length
        $SourceWriteBefore = $SourceBefore.LastWriteTimeUtc
        $SourceHashBefore = (Get-FileHash -LiteralPath $SourceBin -Algorithm SHA256).Hash
        $PackageBefore = @(Get-ChildItem -LiteralPath $PackageDirectory -Recurse -File | Sort-Object FullName | ForEach-Object {
            (Get-Relative $PackageDirectory $_.FullName) + '|' + $_.Length + '|' + $_.LastWriteTimeUtc.Ticks + '|' +
                (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        })
        $Output = [IO.Path]::Combine($QaRoot, (([string]$Contract.package.display_version) + ' output'))
        $Run = Invoke-App ('--headless --source "' + $SourceBin.Replace('"','\"') + '" --output "' + $Output.Replace('"','\"') + '"')
        Assert-True ($Run.ExitCode -eq 0 -and $Run.Out.Contains('BUILD_SUCCESS=') -and [string]::IsNullOrEmpty($Run.Err)) "Dynamic patch failed: $($Run.Err)"
        $OutputBin = [IO.Path]::Combine($Output, [string]$Public.output.bin_name)
        $OutputCue = [IO.Path]::Combine($Output, [string]$Public.output.cue_name)
        Assert-True ((Get-Item -LiteralPath $OutputBin).Length -eq [long]$Public.output.bin_size) 'Output BIN size is wrong.'
        Assert-True ((Get-FileHash -LiteralPath $OutputBin -Algorithm SHA256).Hash.ToLowerInvariant() -ceq [string]$Public.output.bin_sha256) 'Output BIN hash is wrong.'
        Assert-True ((Get-Item -LiteralPath $OutputCue).Length -eq [long]$Public.output.cue_size) 'Output CUE size is wrong.'
        Assert-True ((Get-FileHash -LiteralPath $OutputCue -Algorithm SHA256).Hash.ToLowerInvariant() -ceq [string]$Public.output.cue_sha256) 'Output CUE hash is wrong.'

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
        if ([IO.Directory]::Exists($QaRoot) -and [IO.Path]::GetFileName($QaRoot) -match '^MassDriverOneAppQA\.[0-9a-f]{32}$' -and
            $QaRoot.StartsWith(($QaParent.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $QaRoot -Recurse -Force
        }
    }
}

Write-Host 'One-app package verification: PASS'
Write-Host "ZIP SHA-256: $((Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant())"
