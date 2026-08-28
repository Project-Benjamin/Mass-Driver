#include "emulator.h"

#include <commdlg.h>
#include <shellapi.h>
#include <algorithm>
#include <cwctype>
#include <set>
#include <vector>

#pragma comment(lib, "comdlg32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "version.lib")

namespace fs = std::filesystem;

static const wchar_t* kTitle = L"Xenogears Cut Content Patcher";
static const wchar_t* kDuckStationUrl = L"https://www.duckstation.org/windl";
static const wchar_t* kRetroArchUrl = L"https://www.retroarch.com/?page=platforms";

static std::wstring Lower(std::wstring value) {
    for (wchar_t& character : value)
        character = static_cast<wchar_t>(std::towlower(character));
    return value;
}

static bool Contains(const std::wstring& value, const std::wstring& needle) {
    return Lower(value).find(Lower(needle)) != std::wstring::npos;
}

static std::wstring ErrorText(DWORD value) {
    wchar_t* text = nullptr;
    FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |
        FORMAT_MESSAGE_IGNORE_INSERTS, nullptr, value, 0,
        reinterpret_cast<wchar_t*>(&text), 0, nullptr);
    std::wstring result = text ? text : L"Unknown Windows error";
    if (text) LocalFree(text);
    while (!result.empty() && (result.back() == L'\r' || result.back() == L'\n')) result.pop_back();
    return result;
}

static fs::path AbsolutePath(const fs::path& path) {
    if (path.empty()) return {};
    std::error_code error;
    fs::path absolute = fs::absolute(path, error);
    return error ? fs::path{} : absolute.lexically_normal();
}

static std::wstring EnvironmentValue(const wchar_t* name) {
    DWORD needed = GetEnvironmentVariableW(name, nullptr, 0);
    if (!needed) return L"";
    std::vector<wchar_t> value(static_cast<size_t>(needed));
    DWORD written = GetEnvironmentVariableW(name, value.data(), needed);
    if (!written || written >= needed) return L"";
    return std::wstring(value.data(), written);
}

static fs::path EnvironmentDirectory(const wchar_t* name) {
    const std::wstring value = EnvironmentValue(name);
    if (value.empty()) return {};
    const fs::path path(value);
    return path.is_absolute() ? AbsolutePath(path) : fs::path{};
}

static bool RegularExe(const fs::path& path) {
    std::error_code error;
    if (!fs::is_regular_file(path, error) || error || Lower(path.extension().wstring()) != L".exe")
        return false;
    DWORD binaryType = 0;
    return GetBinaryTypeW(path.c_str(), &binaryType) &&
        (binaryType == SCS_32BIT_BINARY || binaryType == SCS_64BIT_BINARY);
}

static bool IsThisApplication(const fs::path& path) {
    std::vector<wchar_t> buffer(32768);
    DWORD size = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (!size || size >= buffer.size()) return false;
    std::error_code error;
    bool same = fs::equivalent(path, fs::path(std::wstring(buffer.data(), size)), error);
    return !error && same;
}

static std::wstring ReadVersionValue(const fs::path& path, const wchar_t* field) {
    DWORD unused = 0;
    DWORD size = GetFileVersionInfoSizeW(path.c_str(), &unused);
    if (!size || size > 16U * 1024U * 1024U) return L"";
    std::vector<unsigned char> data(size);
    if (!GetFileVersionInfoW(path.c_str(), 0, size, data.data())) return L"";
    struct Translation { WORD language; WORD codePage; };
    Translation* translations = nullptr;
    UINT translationBytes = 0;
    if (!VerQueryValueW(data.data(), L"\\VarFileInfo\\Translation",
        reinterpret_cast<void**>(&translations), &translationBytes) ||
        translationBytes < sizeof(Translation)) return L"";
    wchar_t query[128]{};
    swprintf_s(query, L"\\StringFileInfo\\%04x%04x\\%s",
        translations[0].language, translations[0].codePage, field);
    wchar_t* value = nullptr;
    UINT length = 0;
    if (!VerQueryValueW(data.data(), query, reinterpret_cast<void**>(&value), &length) || !value)
        return L"";
    return std::wstring(value, length ? length - 1 : 0);
}

static fs::path FindRetroArchCore(const fs::path& emulator) {
    static const wchar_t* names[] = {
        L"swanstation_libretro.dll", L"beetle_psx_hw_libretro.dll",
        L"beetle_psx_libretro.dll", L"pcsx_rearmed_libretro.dll"
    };
    for (const wchar_t* name : names) {
        fs::path candidate = emulator.parent_path() / L"cores" / name;
        std::error_code error;
        if (fs::is_regular_file(candidate, error) && !error) return candidate;
    }
    return {};
}

static Emulator DescribeEmulator(const fs::path& path, bool acceptCustom) {
    const fs::path absolute = AbsolutePath(path);
    if (absolute.empty() || !RegularExe(absolute) || IsThisApplication(absolute)) return {};
    const std::wstring filename = Lower(absolute.filename().wstring());
    const std::wstring product = ReadVersionValue(absolute, L"ProductName");
    const std::wstring description = ReadVersionValue(absolute, L"FileDescription");
    if (Contains(product, L"Xenogears Cut Content Patcher") ||
        Contains(description, L"Xenogears Cut Content Patcher") ||
        Contains(product, L"Xenogears Mass Driver") ||
        Contains(description, L"Xenogears Mass Driver")) return {};
    const bool duckStation = Contains(product, L"DuckStation") ||
        Contains(description, L"DuckStation") || filename.find(L"duckstation") != std::wstring::npos;
    if (duckStation && (filename.find(L"uninstall") != std::wstring::npos ||
        filename.find(L"updater") != std::wstring::npos || Contains(product, L"Installer") ||
        Contains(description, L"Installer"))) return {};
    if (Contains(product, L"PCSX2") || Contains(description, L"PCSX2") ||
        filename.find(L"pcsx2") != std::wstring::npos) return {};
    if (duckStation) return {EmulatorKind::DuckStation, absolute, {}, L"DuckStation"};
    if (filename == L"retroarch.exe" || Contains(product, L"RetroArch")) {
        fs::path core = FindRetroArchCore(absolute);
        if (core.empty()) return {};
        return {EmulatorKind::RetroArch, absolute, core, L"RetroArch with " + core.stem().wstring()};
    }
    if (Contains(product, L"ePSXe") || Contains(description, L"ePSXe") ||
        (acceptCustom && filename.find(L"epsxe") != std::wstring::npos))
        return {EmulatorKind::Standalone, absolute, {}, L"ePSXe"};
    if (Contains(product, L"Mednafen") || Contains(description, L"Mednafen") ||
        (acceptCustom && filename.find(L"mednafen") != std::wstring::npos))
        return {EmulatorKind::Standalone, absolute, {}, L"Mednafen"};
    if (Contains(product, L"PCSX") || Contains(description, L"PCSX") ||
        Contains(product, L"XEBRA") || Contains(description, L"XEBRA") ||
        (acceptCustom && (filename.find(L"pcsx") != std::wstring::npos ||
            filename.find(L"xebra") != std::wstring::npos)))
        return {EmulatorKind::Standalone, absolute, {}, absolute.stem().wstring()};
    if (!acceptCustom) return {};
    std::wstring name = product.empty() ? absolute.stem().wstring() : product;
    return {EmulatorKind::Standalone, absolute, {}, name + L" (custom)"};
}

static void AddDuckStationCandidates(std::vector<fs::path>& candidates, const fs::path& root) {
    if (root.empty()) return;
    static const wchar_t* names[] = {
        L"duckstation-qt-x64-ReleaseLTCG.exe", L"duckstation-qt-x64-Release.exe",
        L"duckstation-qt.exe", L"duckstation.exe"
    };
    for (const wchar_t* name : names) candidates.push_back(root / name);
}

Emulator DetectEmulator() {
    std::vector<fs::path> candidates;
    const fs::path local = EnvironmentDirectory(L"LOCALAPPDATA");
    const fs::path programFiles = EnvironmentDirectory(L"ProgramFiles");
    const fs::path programFilesX86 = EnvironmentDirectory(L"ProgramFiles(x86)");
    const fs::path appData = EnvironmentDirectory(L"APPDATA");
    if (!local.empty()) {
        AddDuckStationCandidates(candidates, local / L"Programs" / L"DuckStation");
        AddDuckStationCandidates(candidates, local / L"DuckStation");
        candidates.push_back(local / L"RetroArch" / L"retroarch.exe");
    }
    if (!programFiles.empty()) {
        AddDuckStationCandidates(candidates, programFiles / L"DuckStation");
        candidates.push_back(programFiles / L"RetroArch-Win64" / L"retroarch.exe");
        candidates.push_back(programFiles / L"RetroArch" / L"retroarch.exe");
    }
    if (!programFilesX86.empty()) {
        AddDuckStationCandidates(candidates, programFilesX86 / L"DuckStation");
        candidates.push_back(programFilesX86 / L"RetroArch-Win64" / L"retroarch.exe");
        candidates.push_back(programFilesX86 / L"RetroArch" / L"retroarch.exe");
    }
    if (!appData.empty()) candidates.push_back(appData / L"RetroArch" / L"retroarch.exe");
    std::set<std::wstring> seen;
    for (const fs::path& candidate : candidates) {
        fs::path absolute = AbsolutePath(candidate);
        if (absolute.empty() || !seen.insert(Lower(absolute.wstring())).second) continue;
        Emulator emulator = DescribeEmulator(absolute, false);
        if (emulator.kind != EmulatorKind::None) return emulator;
    }
    return {};
}

Emulator DescribeEmulatorForDiagnostics(const fs::path& path) {
    return DescribeEmulator(path, true);
}

Emulator ChooseEmulator(HWND owner, bool& canceled, std::wstring& error) {
    canceled = false;
    error.clear();
    wchar_t file[32768]{};
    OPENFILENAMEW dialog{sizeof(dialog)};
    dialog.hwndOwner = owner;
    dialog.lpstrFilter = L"Applications (*.exe)\0*.exe\0All files (*.*)\0*.*\0";
    dialog.lpstrFile = file;
    dialog.nMaxFile = static_cast<DWORD>(std::size(file));
    dialog.lpstrTitle = L"Choose your PlayStation emulator";
    dialog.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR | OFN_DONTADDTORECENT;
    if (!GetOpenFileNameW(&dialog)) {
        canceled = CommDlgExtendedError() == 0;
        if (!canceled) error = L"Windows could not open the emulator file picker.";
        return {};
    }
    Emulator emulator = DescribeEmulator(file, true);
    if (emulator.kind == EmulatorKind::None) {
        fs::path selected = AbsolutePath(file);
        if (!selected.empty() && Lower(selected.filename().wstring()) == L"retroarch.exe" &&
            RegularExe(selected) && FindRetroArchCore(selected).empty())
            error = L"RetroArch needs a PlayStation core before it can launch this game.";
        else error = L"Choose your PlayStation emulator's Windows .exe file.";
        return {};
    }
    if (emulator.name.size() >= 9 &&
        emulator.name.compare(emulator.name.size() - 9, 9, L" (custom)") == 0 &&
        MessageBoxW(owner,
            L"This app does not recognize that emulator. It will pass the game CUE as its first argument. Continue?",
            kTitle, MB_YESNO | MB_ICONQUESTION) != IDYES) {
        canceled = true;
        return {};
    }
    return emulator;
}

static std::wstring Quote(const std::wstring& value) {
    std::wstring result = L"\"";
    unsigned slashes = 0;
    for (wchar_t character : value) {
        if (character == L'\\') { ++slashes; continue; }
        if (character == L'\"') {
            result.append(slashes * 2 + 1, L'\\');
            result += L'\"'; slashes = 0; continue;
        }
        result.append(slashes, L'\\'); slashes = 0; result += character;
    }
    result.append(slashes * 2, L'\\'); result += L'\"';
    return result;
}

bool LaunchGame(const Emulator& emulator, const fs::path& cue, std::wstring& error) {
    Emulator current = DescribeEmulator(emulator.path, true);
    if (current.kind == EmulatorKind::None) {
        error = L"The selected emulator is no longer available. Choose it again.";
        return false;
    }
    std::wstring command = Quote(current.path.wstring());
    if (current.kind == EmulatorKind::DuckStation)
        command += L" -nofullscreen -fastboot -- " + Quote(cue.wstring());
    else if (current.kind == EmulatorKind::RetroArch)
        command += L" -L " + Quote(current.core.wstring()) + L" " + Quote(cue.wstring());
    else command += L" " + Quote(cue.wstring());
    std::vector<wchar_t> mutableCommand(command.begin(), command.end());
    mutableCommand.push_back(0);
    STARTUPINFOW startup{sizeof(startup)};
    PROCESS_INFORMATION process{};
    if (!CreateProcessW(current.path.c_str(), mutableCommand.data(), nullptr, nullptr, FALSE,
        0, nullptr, current.path.parent_path().c_str(), &startup, &process)) {
        error = L"The emulator could not be started: " + ErrorText(GetLastError());
        return false;
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return true;
}

static void OpenPage(HWND owner, const wchar_t* url) {
    if (reinterpret_cast<INT_PTR>(ShellExecuteW(owner, L"open", url, nullptr, nullptr, SW_SHOWNORMAL)) <= 32)
        MessageBoxW(owner, L"Windows could not open the official download page.",
            kTitle, MB_OK | MB_ICONERROR);
}

void OpenDuckStationPage(HWND owner) { OpenPage(owner, kDuckStationUrl); }
void OpenRetroArchPage(HWND owner) { OpenPage(owner, kRetroArchUrl); }
