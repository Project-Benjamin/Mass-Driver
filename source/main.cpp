#include <windows.h>
#include <commdlg.h>
#include <shellapi.h>
#include <bcrypt.h>
#include <objbase.h>
#include <atomic>
#include <charconv>
#include <cwctype>
#include <filesystem>
#include <iomanip>
#include <iterator>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>
#include "resource.h"
#include "emulator.h"
#include "xdelta_decoder.h"

#pragma comment(lib, "bcrypt.lib")
#pragma comment(lib, "comdlg32.lib")
#pragma comment(lib, "shell32.lib")

namespace fs = std::filesystem;

static const wchar_t* kTitle = L"Xenogears Mass Driver";
static const wchar_t* kBinName = L"Xenogears_Mass_Driver.bin";
static const wchar_t* kCueName = L"Xenogears_Mass_Driver.cue";
static const wchar_t* kOutputFolder = L"Mass Driver Game";
static const wchar_t* kStagePrefix = L".MassDriverBuild.";
static const wchar_t* kPatchRelative = L"MassDriverData\\patches\\Mass_Driver.xdelta";
static const wchar_t* kCueRelative = L"MassDriverData\\game\\Mass_Driver.cue.template";
static const wchar_t* kManifestRelative = L"MassDriverData\\patch_manifest.txt";
static const wchar_t* kAppFilename = L"Xenogears_Mass_Driver.exe";

struct PatchConfig {
    unsigned long long sourceSize = 0;
    unsigned long long patchSize = 0;
    unsigned long long cueSize = 0;
    unsigned long long outputSize = 0;
    std::string sourceSha;
    std::string patchSha;
    std::string cueSha;
    std::string outputSha;
};

static PatchConfig gConfig;
static bool gConfigReady = false;

enum ExitCode {
    OK = 0, CLI_USAGE = 2, SOURCE_MISSING = 10, SOURCE_SIZE = 11,
    SOURCE_HASH = 12, PACKAGE_MISSING = 20, PACKAGE_BAD = 21,
    OUTPUT_INVALID = 30, DISK_SPACE = 31, XDELTA_FAILED = 40,
    OUTPUT_BAD = 41, MATERIALIZE_FAILED = 42, COMMIT_FAILED = 50,
    UNEXPECTED = 60
};

static HINSTANCE gInstance = nullptr;
static HWND gWindow = nullptr;
static HWND gSourceEdit = nullptr;
static HWND gStatus = nullptr;
static HWND gBuild = nullptr;
static HWND gPlay = nullptr;
static HWND gOpen = nullptr;
static HWND gChooseEmulator = nullptr;
static HWND gAutoDetectEmulator = nullptr;
static HWND gGetDuckStation = nullptr;
static HWND gGetRetroArch = nullptr;
static HFONT gFont = nullptr;
static HFONT gTitleFont = nullptr;
static std::atomic<bool> gBuilding(false);
static std::wstring gSource;
static fs::path gRoot;
static fs::path gFinal;
static Emulator gEmulator;

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

static void WriteConsole(const std::wstring& value, bool error = false) {
    HANDLE handle = GetStdHandle(error ? STD_ERROR_HANDLE : STD_OUTPUT_HANDLE);
    if (!handle || handle == INVALID_HANDLE_VALUE) return;
    int length = WideCharToMultiByte(CP_UTF8, 0, value.c_str(), static_cast<int>(value.size()),
        nullptr, 0, nullptr, nullptr);
    if (length <= 0) return;
    std::string utf8(static_cast<size_t>(length), '\0');
    WideCharToMultiByte(CP_UTF8, 0, value.c_str(), static_cast<int>(value.size()),
        utf8.data(), length, nullptr, nullptr);
    utf8 += "\r\n";
    DWORD written = 0;
    WriteFile(handle, utf8.data(), static_cast<DWORD>(utf8.size()), &written, nullptr);
}

static fs::path ExecutableDirectory() {
    std::vector<wchar_t> buffer(32768);
    DWORD size = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (!size || size >= buffer.size()) throw std::runtime_error("Cannot determine program path");
    return fs::path(std::wstring(buffer.data(), size)).parent_path();
}

class ReadLock {
public:
    ReadLock() = default;
    ~ReadLock() { Close(); }
    ReadLock(const ReadLock&) = delete;
    ReadLock& operator=(const ReadLock&) = delete;
    ReadLock(ReadLock&& other) noexcept : handle_(other.handle_) {
        other.handle_ = INVALID_HANDLE_VALUE;
    }
    ReadLock& operator=(ReadLock&& other) noexcept {
        if (this != &other) {
            Close();
            handle_ = other.handle_;
            other.handle_ = INVALID_HANDLE_VALUE;
        }
        return *this;
    }
    bool Open(const fs::path& path) {
        Close();
        handle_ = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr,
            OPEN_EXISTING, FILE_FLAG_SEQUENTIAL_SCAN | FILE_FLAG_OPEN_REPARSE_POINT, nullptr);
        if (handle_ == INVALID_HANDLE_VALUE) return false;
        FILE_ATTRIBUTE_TAG_INFO attributes{};
        if (!GetFileInformationByHandleEx(handle_, FileAttributeTagInfo, &attributes, sizeof(attributes)) ||
            (attributes.FileAttributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT)) != 0) {
            Close();
            return false;
        }
        return true;
    }
    HANDLE Get() const { return handle_; }
private:
    void Close() {
        if (handle_ != INVALID_HANDLE_VALUE) {
            CloseHandle(handle_);
            handle_ = INVALID_HANDLE_VALUE;
        }
    }
    HANDLE handle_ = INVALID_HANDLE_VALUE;
};

static bool ReadLockedText(HANDLE handle, std::string& text) {
    LARGE_INTEGER size{};
    if (!GetFileSizeEx(handle, &size) || size.QuadPart <= 0 || size.QuadPart > 4096) return false;
    LARGE_INTEGER start{};
    if (!SetFilePointerEx(handle, start, nullptr, FILE_BEGIN)) return false;
    text.assign(static_cast<size_t>(size.QuadPart), '\0');
    DWORD read = 0;
    if (!ReadFile(handle, text.data(), static_cast<DWORD>(text.size()), &read, nullptr) ||
        read != text.size()) return false;
    return true;
}

static bool SafePackageDirectory(const fs::path& path) {
    DWORD attributes = GetFileAttributesW(path.c_str());
    return attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY) != 0 &&
        (attributes & FILE_ATTRIBUTE_REPARSE_POINT) == 0;
}

static bool ParseSize(const std::string& text, unsigned long long minimum,
    unsigned long long maximum, unsigned long long& result) {
    if (text.empty()) return false;
    const char* first = text.data();
    const char* last = first + text.size();
    auto parsed = std::from_chars(first, last, result, 10);
    return parsed.ec == std::errc() && parsed.ptr == last && result >= minimum && result <= maximum;
}

static bool ValidSha256(const std::string& value) {
    if (value.size() != 64) return false;
    for (char character : value)
        if (!((character >= '0' && character <= '9') || (character >= 'a' && character <= 'f'))) return false;
    return true;
}

static bool LoadPatchConfig(std::wstring& error) {
    try {
        const fs::path support = gRoot / L"MassDriverData";
        if (!SafePackageDirectory(support) || !SafePackageDirectory(support / L"patches") ||
            !SafePackageDirectory(support / L"game")) {
            error = L"The MassDriverData folder is missing or is not a safe extracted package folder.";
            return false;
        }
        ReadLock manifestLock;
        if (!manifestLock.Open(gRoot / kManifestRelative)) {
            error = L"The patch manifest is missing or could not be opened safely.";
            return false;
        }
        std::string content;
        if (!ReadLockedText(manifestLock.Get(), content) || content.find('\0') != std::string::npos) {
            error = L"The patch manifest is empty, too large, or malformed.";
            return false;
        }
        std::map<std::string, std::string> fields;
        size_t start = 0;
        while (start < content.size()) {
            size_t end = content.find('\n', start);
            if (end == std::string::npos) end = content.size();
            std::string line = content.substr(start, end - start);
            size_t equals = line.find('=');
            if (line.empty() || equals == std::string::npos || equals == 0 || equals + 1 >= line.size() ||
                line.find('=', equals + 1) != std::string::npos) {
                error = L"The patch manifest contains a malformed line.";
                return false;
            }
            std::string key = line.substr(0, equals);
            std::string value = line.substr(equals + 1);
            for (unsigned char character : line) {
                if (character < 0x21 || character > 0x7e) {
                    error = L"The patch manifest must contain plain ASCII fields.";
                    return false;
                }
            }
            if (!fields.emplace(std::move(key), std::move(value)).second) {
                error = L"The patch manifest contains a duplicate field.";
                return false;
            }
            start = end + 1;
        }
        static const char* expected[] = {"format", "source_size", "source_sha256", "patch_size",
            "patch_sha256", "cue_size", "cue_sha256", "output_size", "output_sha256"};
        if (fields.size() != std::size(expected)) {
            error = L"The patch manifest has missing or unsupported fields.";
            return false;
        }
        for (const char* key : expected) {
            if (fields.find(key) == fields.end()) {
                error = L"The patch manifest has missing or unsupported fields.";
                return false;
            }
        }
        if (fields["format"] != "xenogears-mass-driver-patch-v1") {
            error = L"This patch manifest format is not supported.";
            return false;
        }
        PatchConfig parsed;
        constexpr unsigned long long MiB = 1024ULL * 1024ULL;
        if (!ParseSize(fields["source_size"], 100ULL * MiB, 1024ULL * MiB, parsed.sourceSize) ||
            !ParseSize(fields["patch_size"], 1, 1024ULL * MiB, parsed.patchSize) ||
            !ParseSize(fields["cue_size"], 1, 4096, parsed.cueSize) ||
            !ParseSize(fields["output_size"], 100ULL * MiB, 1024ULL * MiB, parsed.outputSize)) {
            error = L"The patch manifest contains an unsafe or invalid file size.";
            return false;
        }
        parsed.sourceSha = fields["source_sha256"];
        parsed.patchSha = fields["patch_sha256"];
        parsed.cueSha = fields["cue_sha256"];
        parsed.outputSha = fields["output_sha256"];
        if (!ValidSha256(parsed.sourceSha) || !ValidSha256(parsed.patchSha) ||
            !ValidSha256(parsed.cueSha) || !ValidSha256(parsed.outputSha)) {
            error = L"The patch manifest contains an invalid SHA-256 value.";
            return false;
        }
        gConfig = std::move(parsed);
        gConfigReady = true;
        return true;
    } catch (...) {
        error = L"The patch manifest could not be checked.";
        return false;
    }
}

static std::string Sha256Handle(HANDLE file) {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    DWORD objectSize = 0, digestSize = 0, used = 0;
    std::vector<unsigned char> object, digest, buffer(1024 * 1024);
    auto fail = [&]() {
        if (hash) BCryptDestroyHash(hash);
        if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
        throw std::runtime_error("SHA-256 operation failed");
    };
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0) fail();
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
        reinterpret_cast<PUCHAR>(&objectSize), sizeof(objectSize), &used, 0) < 0) fail();
    if (BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
        reinterpret_cast<PUCHAR>(&digestSize), sizeof(digestSize), &used, 0) < 0) fail();
    object.resize(objectSize); digest.resize(digestSize);
    if (BCryptCreateHash(algorithm, &hash, object.data(), objectSize, nullptr, 0, 0) < 0) fail();
    LARGE_INTEGER start{};
    if (!SetFilePointerEx(file, start, nullptr, FILE_BEGIN)) fail();
    for (;;) {
        DWORD got = 0;
        if (!ReadFile(file, buffer.data(), static_cast<DWORD>(buffer.size()), &got, nullptr)) fail();
        if (!got) break;
        if (BCryptHashData(hash, buffer.data(), got, 0) < 0) fail();
    }
    if (BCryptFinishHash(hash, digest.data(), digestSize, 0) < 0) fail();
    BCryptDestroyHash(hash); BCryptCloseAlgorithmProvider(algorithm, 0);
    std::ostringstream text;
    for (unsigned char value : digest)
        text << std::hex << std::setfill('0') << std::setw(2) << static_cast<int>(value);
    return text.str();
}

static bool PinnedHandle(HANDLE handle, unsigned long long size, const char* sha) {
    try {
        LARGE_INTEGER length{};
        return handle != INVALID_HANDLE_VALUE && GetFileSizeEx(handle, &length) && length.QuadPart >= 0 &&
            static_cast<unsigned long long>(length.QuadPart) == size && Sha256Handle(handle) == sha;
    } catch (...) { return false; }
}

static bool Pinned(const fs::path& path, unsigned long long size, const char* sha) {
    try {
        ReadLock lock;
        return lock.Open(path) && PinnedHandle(lock.Get(), size, sha);
    } catch (...) { return false; }
}

static fs::path Extended(const fs::path& path) {
    std::error_code error;
    std::wstring absolute = fs::absolute(path, error).wstring();
    if (error || absolute.empty()) throw std::runtime_error("Cannot make extended path");
    if (absolute.rfind(L"\\\\?\\", 0) == 0) return absolute;
    if (absolute.rfind(L"\\\\", 0) == 0) return fs::path(L"\\\\?\\UNC\\" + absolute.substr(2));
    return fs::path(L"\\\\?\\" + absolute);
}

static std::wstring Quote(const std::wstring& value) {
    std::wstring result = L"\"";
    unsigned slashes = 0;
    for (wchar_t character : value) {
        if (character == L'\\') { ++slashes; continue; }
        if (character == L'\"') {
            result.append(slashes * 2 + 1, L'\\'); result += L'\"'; slashes = 0; continue;
        }
        result.append(slashes, L'\\'); slashes = 0; result += character;
    }
    result.append(slashes * 2, L'\\'); result += L'\"';
    return result;
}

static std::wstring EmulatorCommand(const Emulator& emulator, const fs::path& cue) {
    std::wstring command = Quote(emulator.path.wstring());
    if (emulator.kind == EmulatorKind::DuckStation)
        return command + L" -nofullscreen -fastboot -- " + Quote(cue.wstring());
    if (emulator.kind == EmulatorKind::RetroArch)
        return command + L" -L " + Quote(emulator.core.wstring()) + L" " + Quote(cue.wstring());
    return command + L" " + Quote(cue.wstring());
}

static fs::path MakeStage(const fs::path& final) {
    GUID id{};
    if (CoCreateGuid(&id) != S_OK) throw std::runtime_error("Cannot create build identifier");
    wchar_t text[33]{};
    swprintf_s(text, L"%08x%04x%04x%02x%02x%02x%02x%02x%02x%02x%02x",
        id.Data1, id.Data2, id.Data3, id.Data4[0], id.Data4[1], id.Data4[2], id.Data4[3],
        id.Data4[4], id.Data4[5], id.Data4[6], id.Data4[7]);
    return final.parent_path() / (std::wstring(kStagePrefix) + text);
}

static void Status(const std::wstring& message, bool headless) {
    if (headless) WriteConsole(message);
    else if (gWindow) PostMessageW(gWindow, WM_BUILD_STATUS, 0,
        reinterpret_cast<LPARAM>(new std::wstring(message)));
}

static bool ExactOutput(const fs::path& final) {
    try {
        return gConfigReady && SafePackageDirectory(final) &&
            Pinned(final / kBinName, gConfig.outputSize, gConfig.outputSha.c_str()) &&
            Pinned(final / kCueName, gConfig.cueSize, gConfig.cueSha.c_str());
    } catch (...) { return false; }
}

static int CheckPackage(std::wstring& error, std::vector<ReadLock>* retained = nullptr) {
    try {
        if (!gConfigReady && !LoadPatchConfig(error)) return PACKAGE_BAD;
        const fs::path patch = gRoot / kPatchRelative;
        const fs::path cueTemplate = gRoot / kCueRelative;
        std::vector<ReadLock> localLocks;
        std::vector<ReadLock>& locks = retained ? *retained : localLocks;
        locks.clear();
        locks.reserve(2);
        ReadLock patchLock, cueLock;
        if (!patchLock.Open(patch) || !cueLock.Open(cueTemplate)) {
            error = L"A patch-kit file is missing, busy, or could not be locked for a safe build.";
            return PACKAGE_BAD;
        }
        locks.push_back(std::move(patchLock));
        locks.push_back(std::move(cueLock));
        if (!PinnedHandle(locks[0].Get(), gConfig.patchSize, gConfig.patchSha.c_str()) ||
            !PinnedHandle(locks[1].Get(), gConfig.cueSize, gConfig.cueSha.c_str())) {
            error = L"A patch-kit file is missing or changed. Extract a fresh copy of the complete ZIP.";
            return PACKAGE_BAD;
        }
        return OK;
    } catch (...) {
        error = L"The patch-kit files could not be checked.";
        return PACKAGE_BAD;
    }
}

static int BuildGame(const fs::path& source, const fs::path& final,
    bool headless, std::wstring& error) {
    fs::path stage;
    bool stageOwned = false;
    try {
        ReadLock sourceLock;
        if (!sourceLock.Open(source) || !fs::is_regular_file(source)) {
            error = L"Choose the .bin file from your original USA Xenogears Disc 2.";
            return SOURCE_MISSING;
        }
        if (fs::file_size(source) != gConfig.sourceSize) {
            error = L"This is not the supported USA Disc 2 image. Choose an unmodified raw .bin file.";
            return SOURCE_SIZE;
        }
        Status(L"Checking your original Disc 2 BIN...", headless);
        if (Sha256Handle(sourceLock.Get()) != gConfig.sourceSha) {
            error = L"This BIN is not the supported unmodified USA Disc 2 image.";
            return SOURCE_HASH;
        }

        Status(L"Checking the patch-kit files...", headless);
        std::vector<ReadLock> packageLocks;
        int packageResult = CheckPackage(error, &packageLocks);
        if (packageResult != OK) return packageResult;
        const fs::path cueTemplate = gRoot / kCueRelative;

        if (fs::exists(final)) {
            if (ExactOutput(final)) {
                Status(L"The game is already ready. Select Play in this app.", headless);
                return OK;
            }
            error = L"The output folder already exists but does not match this build. Move or rename it, then try again.";
            return OUTPUT_INVALID;
        }
        std::error_code fileError;
        fs::create_directories(final.parent_path(), fileError);
        if (fileError || !SafePackageDirectory(final.parent_path())) {
            error = L"The patch-kit folder is not writable."; return OUTPUT_INVALID;
        }
        ULARGE_INTEGER available{};
        if (!GetDiskFreeSpaceExW(final.parent_path().c_str(), &available, nullptr, nullptr) ||
            available.QuadPart < gConfig.outputSize + 64ULL * 1024 * 1024) {
            error = L"There is not enough free space to build the game."; return DISK_SPACE;
        }
        stage = MakeStage(final);
        if (!fs::create_directory(stage)) {
            error = L"Windows could not create the temporary output folder."; return OUTPUT_INVALID;
        }
        stageOwned = true;
        fs::path output = stage / kBinName;
        Status(L"Building the game with the integrated xdelta decoder. This may take several minutes...", headless);
        int decoderResult = DecodeVcdiff(sourceLock.Get(), packageLocks[0].Get(),
            Extended(output).c_str(), gConfig.outputSize, error);
        if (decoderResult != 0) {
            if (error.empty()) error = L"The integrated xdelta decoder could not build the game (error " +
                std::to_wstring(decoderResult) + L").";
            fs::remove_all(stage, fileError); stageOwned = false; return XDELTA_FAILED;
        }
        Status(L"Checking the finished game...", headless);
        if (!Pinned(output, gConfig.outputSize, gConfig.outputSha.c_str())) {
            error = L"The finished BIN did not match the expected build.";
            fs::remove_all(stage, fileError); stageOwned = false; return OUTPUT_BAD;
        }
        fs::copy_file(cueTemplate, stage / kCueName, fs::copy_options::none, fileError);
        if (fileError || !Pinned(stage / kCueName, gConfig.cueSize, gConfig.cueSha.c_str())) {
            error = L"The CUE file could not be copied or verified.";
            fs::remove_all(stage, fileError); stageOwned = false; return MATERIALIZE_FAILED;
        }
        if (!MoveFileExW(stage.c_str(), final.c_str(), MOVEFILE_WRITE_THROUGH)) {
            error = L"The verified game folder could not be moved into place: " + ErrorText(GetLastError());
            fs::remove_all(stage, fileError); stageOwned = false; return COMMIT_FAILED;
        }
        stageOwned = false;
        Status(L"The game is ready. Select Play in this app.", headless);
        return OK;
    } catch (...) {
        std::error_code fileError;
        if (stageOwned && !stage.empty() && stage.parent_path() == final.parent_path() &&
            stage.filename().wstring().rfind(kStagePrefix, 0) == 0)
            fs::remove_all(stage, fileError);
        error = L"The patcher stopped because of an unexpected Windows error.";
        return UNEXPECTED;
    }
}

static HWND Child(const wchar_t* cls, const wchar_t* text, DWORD style,
    int x, int y, int width, int height, HWND parent, int id = 0) {
    return CreateWindowExW(0, cls, text, WS_CHILD | WS_VISIBLE | style,
        x, y, width, height, parent,
        id ? reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)) : nullptr, gInstance, nullptr);
}

static void SetFont(HWND control, HFONT font = nullptr) {
    SendMessageW(control, WM_SETFONT, reinterpret_cast<WPARAM>(font ? font : gFont), TRUE);
}

static std::wstring ChooseBin(HWND owner) {
    wchar_t buffer[32768]{};
    OPENFILENAMEW dialog{sizeof(dialog)};
    dialog.hwndOwner = owner;
    dialog.lpstrFilter = L"Disc image (*.bin)\0*.bin\0All files (*.*)\0*.*\0";
    dialog.lpstrFile = buffer;
    dialog.nMaxFile = static_cast<DWORD>(std::size(buffer));
    dialog.lpstrTitle = L"Choose your original USA Xenogears Disc 2 BIN";
    dialog.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR | OFN_DONTADDTORECENT;
    return GetOpenFileNameW(&dialog) ? std::wstring(buffer) : L"";
}

static void SetFinishedUi(bool ready, const std::wstring& message) {
    SetWindowTextW(gStatus, message.c_str());
    EnableWindow(gBuild, TRUE);
    EnableWindow(gSourceEdit, TRUE);
    EnableWindow(GetDlgItem(gWindow, IDC_SELECT_SOURCE), TRUE);
    EnableWindow(gPlay, ready ? TRUE : FALSE);
    EnableWindow(gOpen, ready ? TRUE : FALSE);
}

static bool StartGame(HWND owner) {
    if (!ExactOutput(gFinal)) {
        MessageBoxW(owner, L"Build the game from your original Disc 2 BIN before selecting Play.",
            kTitle, MB_OK | MB_ICONINFORMATION);
        SetFinishedUi(false, L"The finished game is missing or changed. Choose your original Disc 2 BIN to build it again.");
        return false;
    }
    std::wstring error;
    Emulator emulator = gEmulator;
    if (emulator.kind == EmulatorKind::None) emulator = DetectEmulator();
    if (emulator.kind == EmulatorKind::None) {
        int choice = MessageBoxW(owner,
            L"No compatible PlayStation emulator was found.\r\n\r\nSelect Yes to choose an emulator you already installed.\r\nSelect No to return and use an official download button.",
            kTitle, MB_YESNOCANCEL | MB_ICONINFORMATION);
        if (choice != IDYES) return false;
        bool canceled = false;
        emulator = ChooseEmulator(owner, canceled, error);
        if (emulator.kind == EmulatorKind::None) {
            if (!canceled && !error.empty()) MessageBoxW(owner, error.c_str(), kTitle, MB_OK | MB_ICONERROR);
            return false;
        }
    }
    gEmulator = emulator;
    if (!LaunchGame(gEmulator, gFinal / kCueName, error)) {
        gEmulator = {};
        MessageBoxW(owner, error.c_str(), L"The game could not start", MB_OK | MB_ICONERROR);
        return false;
    }
    SetWindowTextW(gStatus, (L"Game started with " + emulator.name + L". You can keep this app open or close it.").c_str());
    return true;
}

static LRESULT CALLBACK WindowProc(HWND window, UINT message, WPARAM word, LPARAM value) {
    switch (message) {
    case WM_CREATE: {
        gWindow = window;
        gFont = CreateFontW(-17, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, DEFAULT_CHARSET,
            OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
        gTitleFont = CreateFontW(-26, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET,
            OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
        HWND title = Child(L"STATIC", L"Xenogears Mass Driver", SS_LEFT, 24, 18, 540, 38, window);
        SetFont(title, gTitleFont);
        SetFont(Child(L"STATIC", L"Build and start the included Mass Driver update.",
            SS_LEFT, 24, 58, 700, 24, window));
        SetFont(Child(L"STATIC", L"1. Choose the unmodified USA Disc 2 BIN you legally own.",
            SS_LEFT, 24, 104, 700, 24, window));
        gSourceEdit = Child(L"EDIT", L"", ES_AUTOHSCROLL | WS_BORDER | WS_TABSTOP,
            24, 136, 560, 30, window, IDC_SOURCE_PATH); SetFont(gSourceEdit);
        HWND browse = Child(L"BUTTON", L"&Browse...", BS_PUSHBUTTON | WS_TABSTOP,
            596, 136, 130, 30, window, IDC_SELECT_SOURCE); SetFont(browse);
        SetFont(Child(L"STATIC", L"2. Select Build game. Your source BIN is read only and is never changed.",
            SS_LEFT, 24, 194, 700, 24, window));
        gBuild = Child(L"BUTTON", L"&Build game", BS_DEFPUSHBUTTON | WS_TABSTOP,
            24, 228, 180, 38, window, IDC_BUILD); SetFont(gBuild);
        SetFont(Child(L"STATIC", L"3. Select Play here. The app finds your emulator or asks you to choose it.",
            SS_LEFT, 24, 296, 710, 42, window));
        bool ready = ExactOutput(gFinal);
        std::wstring readyText =
            L"The game is ready. Select Play, or Browse to build from another clean Disc 2 BIN.";
        gStatus = Child(L"STATIC", ready ? readyText.c_str() :
            L"Ready. Keep Xenogears_Mass_Driver.exe beside the MassDriverData folder.",
            SS_LEFT, 24, 350, 700, 60, window, IDC_STATUS); SetFont(gStatus);
        gPlay = Child(L"BUTTON", L"&Play", BS_PUSHBUTTON | WS_TABSTOP,
            24, 422, 150, 38, window, IDC_PLAY); SetFont(gPlay); EnableWindow(gPlay, ready ? TRUE : FALSE);
        gOpen = Child(L"BUTTON", L"&Open game folder", BS_PUSHBUTTON | WS_TABSTOP,
            188, 422, 190, 38, window, IDC_OPEN_FOLDER); SetFont(gOpen); EnableWindow(gOpen, ready ? TRUE : FALSE);
        SetFont(Child(L"STATIC", L"Optional: emulator setup", SS_LEFT,
            24, 478, 700, 24, window));
        gChooseEmulator = Child(L"BUTTON", L"&Choose emulator...", BS_PUSHBUTTON | WS_TABSTOP,
            24, 508, 168, 36, window, IDC_CHOOSE_EMULATOR); SetFont(gChooseEmulator);
        gAutoDetectEmulator = Child(L"BUTTON", L"&Auto-detect emulator", BS_PUSHBUTTON | WS_TABSTOP,
            204, 508, 188, 36, window, IDC_AUTO_DETECT_EMULATOR); SetFont(gAutoDetectEmulator);
        gGetDuckStation = Child(L"BUTTON", L"Get &DuckStation", BS_PUSHBUTTON | WS_TABSTOP,
            404, 508, 154, 36, window, IDC_GET_DUCKSTATION); SetFont(gGetDuckStation);
        gGetRetroArch = Child(L"BUTTON", L"Get &RetroArch", BS_PUSHBUTTON | WS_TABSTOP,
            570, 508, 154, 36, window, IDC_GET_RETROARCH); SetFont(gGetRetroArch);
        SetFocus(gSourceEdit);
        return 0;
    }
    case WM_COMMAND:
        switch (LOWORD(word)) {
        case IDC_SELECT_SOURCE: {
            std::wstring selected = ChooseBin(window);
            if (!selected.empty()) { gSource = selected; SetWindowTextW(gSourceEdit, selected.c_str()); }
            return 0;
        }
        case IDC_BUILD: {
            int length = GetWindowTextLengthW(gSourceEdit);
            std::vector<wchar_t> buffer(static_cast<size_t>(length) + 1);
            GetWindowTextW(gSourceEdit, buffer.data(), static_cast<int>(buffer.size()));
            gSource = buffer.data();
            if (gSource.empty()) {
                MessageBoxW(window, L"Choose your original Disc 2 BIN first.", kTitle, MB_OK | MB_ICONINFORMATION);
                return 0;
            }
            gBuilding.store(true);
            EnableWindow(gBuild, FALSE); EnableWindow(gSourceEdit, FALSE);
            EnableWindow(GetDlgItem(window, IDC_SELECT_SOURCE), FALSE);
            EnableWindow(gPlay, FALSE); EnableWindow(gOpen, FALSE);
            SetWindowTextW(gStatus, L"Starting checks...");
            std::wstring source = gSource;
            std::thread([source]() {
                std::wstring error;
                std::error_code absoluteError;
                fs::path absolute = fs::absolute(source, absoluteError);
                int result = absoluteError ? UNEXPECTED : BuildGame(absolute, gFinal, false, error);
                if (absoluteError) error = L"Windows could not read the selected BIN path.";
                PostMessageW(gWindow, WM_BUILD_COMPLETE, 0,
                    reinterpret_cast<LPARAM>(new std::pair<int, std::wstring>(result, error)));
            }).detach();
            return 0;
        }
        case IDC_PLAY: {
            StartGame(window);
            return 0;
        }
        case IDC_OPEN_FOLDER:
            if (reinterpret_cast<INT_PTR>(ShellExecuteW(window, L"open", gFinal.c_str(), nullptr,
                gRoot.c_str(), SW_SHOWNORMAL)) <= 32)
                MessageBoxW(window, L"The game folder could not be opened.", kTitle, MB_OK | MB_ICONERROR);
            return 0;
        case IDC_CHOOSE_EMULATOR: {
            bool canceled = false;
            std::wstring error;
            Emulator chosen = ChooseEmulator(window, canceled, error);
            if (chosen.kind != EmulatorKind::None) {
                gEmulator = chosen;
                SetWindowTextW(gStatus, (L"Using " + chosen.name + L" for this session. Select Play when the game is ready.").c_str());
            } else if (!canceled && !error.empty()) MessageBoxW(window, error.c_str(), kTitle, MB_OK | MB_ICONERROR);
            return 0;
        }
        case IDC_AUTO_DETECT_EMULATOR:
            gEmulator = DetectEmulator();
            if (gEmulator.kind == EmulatorKind::None)
                MessageBoxW(window, L"No compatible emulator was found. Choose its .exe file or use an official download button.",
                    kTitle, MB_OK | MB_ICONINFORMATION);
            else SetWindowTextW(gStatus, (L"Found " + gEmulator.name + L". Select Play when the game is ready.").c_str());
            return 0;
        case IDC_GET_DUCKSTATION: OpenDuckStationPage(window); return 0;
        case IDC_GET_RETROARCH: OpenRetroArchPage(window); return 0;
        }
        break;
    case WM_BUILD_STATUS: {
        auto text = reinterpret_cast<std::wstring*>(value);
        SetWindowTextW(gStatus, text->c_str()); delete text; return 0;
    }
    case WM_BUILD_COMPLETE: {
        auto result = reinterpret_cast<std::pair<int, std::wstring>*>(value);
        gBuilding.store(false);
        bool ready = ExactOutput(gFinal);
        std::wstring text = result->first == OK ? L"The game is ready. Select Play." : result->second;
        int code = result->first; delete result;
        SetFinishedUi(ready, text);
        if (code != OK) MessageBoxW(window, text.c_str(), L"Build did not complete", MB_OK | MB_ICONERROR);
        return code;
    }
    case WM_CLOSE:
        if (gBuilding.load()) {
            MessageBoxW(window, L"Wait for the game build to finish before closing this window.", kTitle,
                MB_OK | MB_ICONINFORMATION); return 0;
        }
        DestroyWindow(window); return 0;
    case WM_DESTROY:
        if (gTitleFont) DeleteObject(gTitleFont);
        if (gFont) DeleteObject(gFont);
        PostQuitMessage(0); return 0;
    }
    return DefWindowProcW(window, message, word, value);
}

static int Headless(int argc, wchar_t** argv) {
    std::wstring source, output;
    std::wstring emulatorPath;
    std::wstring gamePath;
    bool sourceSeen = false, outputSeen = false, checkPackage = false;
    bool playCheck = false, noEmulator = false, emulatorSeen = false, gameSeen = false;
    for (int index = 2; index < argc; ++index) {
        std::wstring argument = argv[index];
        if (argument == L"--source" && index + 1 < argc && !sourceSeen && !checkPackage && !playCheck) {
            source = argv[++index]; sourceSeen = true;
        }
        else if (argument == L"--output" && index + 1 < argc && !outputSeen && !checkPackage && !playCheck) {
            output = argv[++index]; outputSeen = true;
        }
        else if (argument == L"--check-package" && !checkPackage && !sourceSeen && !outputSeen && !playCheck) {
            checkPackage = true;
        }
        else if (argument == L"--play-check" && !playCheck && !checkPackage && !sourceSeen && !outputSeen) {
            playCheck = true;
        }
        else if (argument == L"--no-emulator" && playCheck && !noEmulator && !emulatorSeen) {
            noEmulator = true;
        }
        else if (argument == L"--emulator" && playCheck && index + 1 < argc && !emulatorSeen && !noEmulator) {
            emulatorPath = argv[++index]; emulatorSeen = !emulatorPath.empty();
            if (!emulatorSeen) { WriteConsole(L"ERROR: invalid command line", true); return CLI_USAGE; }
        }
        else if (argument == L"--game" && playCheck && index + 1 < argc && !gameSeen) {
            gamePath = argv[++index]; gameSeen = !gamePath.empty();
            if (!gameSeen) { WriteConsole(L"ERROR: invalid command line", true); return CLI_USAGE; }
        }
        else { WriteConsole(L"ERROR: invalid command line", true); return CLI_USAGE; }
    }
    if (checkPackage) {
        std::wstring error;
        int result = CheckPackage(error);
        if (result == OK) WriteConsole(L"PACKAGE_OK");
        else WriteConsole(L"PACKAGE_ERROR=" + std::to_wstring(result) + L":" + error, true);
        return result;
    }
    if (playCheck) {
        fs::path game = gFinal;
        if (gameSeen) {
            std::error_code gameError;
            game = fs::absolute(gamePath, gameError);
            if (gameError) { WriteConsole(L"ERROR: invalid game path", true); return CLI_USAGE; }
        }
        if (!ExactOutput(game)) { WriteConsole(L"GAME_NOT_FOUND"); return OUTPUT_INVALID; }
        fs::path cue = game / kCueName;
        WriteConsole(L"GAME_CUE=" + cue.wstring());
        Emulator emulator = noEmulator ? Emulator{} :
            (emulatorSeen ? DescribeEmulatorForDiagnostics(emulatorPath) : DetectEmulator());
        if (emulator.kind == EmulatorKind::None) { WriteConsole(L"EMULATOR_REQUIRED"); return 4; }
        WriteConsole(L"EMULATOR_NAME=" + emulator.name);
        WriteConsole(L"EMULATOR_PATH=" + emulator.path.wstring());
        WriteConsole(L"EMULATOR_COMMAND=" + EmulatorCommand(emulator, cue));
        return OK;
    }
    if (source.empty()) {
        WriteConsole(L"Usage: --headless --check-package | --headless --play-check [--game <OUTPUT_FOLDER>] [--no-emulator|--emulator <EXE>] | --headless --source <BIN> [--output <EXACT_OUTPUT_FOLDER>]", true);
        return CLI_USAGE;
    }
    std::error_code absoluteError;
    fs::path absoluteSource = fs::absolute(source, absoluteError);
    if (absoluteError) { WriteConsole(L"BUILD_ERROR=60:Windows could not read the selected BIN path.", true); return UNEXPECTED; }
    fs::path final = output.empty() ? gFinal : fs::absolute(output, absoluteError);
    if (absoluteError) { WriteConsole(L"BUILD_ERROR=60:Windows could not read the output path.", true); return UNEXPECTED; }
    std::wstring error;
    int result = BuildGame(absoluteSource, final, true, error);
    if (result == OK) {
        WriteConsole(L"BUILD_SUCCESS=" + final.wstring());
        WriteConsole(L"PLAY_APP=" + (gRoot / kAppFilename).wstring());
    } else WriteConsole(L"BUILD_ERROR=" + std::to_wstring(result) + L":" + error, true);
    return result;
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int show) {
    gInstance = instance;
    try { gRoot = ExecutableDirectory(); gFinal = gRoot / kOutputFolder; }
    catch (...) { return UNEXPECTED; }
    int argc = 0;
    wchar_t** argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    const bool headless = argv && argc > 1 && std::wstring(argv[1]) == L"--headless";
    std::wstring configError;
    if (!LoadPatchConfig(configError)) {
        if (headless) WriteConsole(L"PACKAGE_ERROR=21:" + configError, true);
        else MessageBoxW(nullptr, configError.c_str(), L"Patch package could not be opened", MB_OK | MB_ICONERROR);
        if (argv) LocalFree(argv);
        return PACKAGE_BAD;
    }
    if (headless) {
        int result = Headless(argc, argv); LocalFree(argv); return result;
    }
    if (argv) LocalFree(argv);
    WNDCLASSEXW cls{sizeof(cls)};
    cls.lpfnWndProc = WindowProc; cls.hInstance = instance;
    cls.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    cls.hIcon = LoadIconW(instance, MAKEINTRESOURCEW(IDI_MASS_DRIVER));
    if (!cls.hIcon) cls.hIcon = LoadIconW(nullptr, IDI_APPLICATION);
    cls.hIconSm = cls.hIcon; cls.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_WINDOW + 1);
    cls.lpszClassName = L"XenogearsMassDriver";
    if (!RegisterClassExW(&cls)) return UNEXPECTED;
    gWindow = CreateWindowExW(0, cls.lpszClassName, kTitle,
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 778, 620, nullptr, nullptr, instance, nullptr);
    if (!gWindow) return UNEXPECTED;
    ShowWindow(gWindow, show); UpdateWindow(gWindow);
    MSG message{};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        if (!IsDialogMessageW(gWindow, &message)) {
            TranslateMessage(&message); DispatchMessageW(&message);
        }
    }
    return static_cast<int>(message.wParam);
}
