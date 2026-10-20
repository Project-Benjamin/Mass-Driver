#include "archive.h"

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#include <compressapi.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <cwchar>
#include <exception>
#include <limits>
#include <set>

namespace mdarchive {
namespace {
constexpr uint64_t kChunk = 4ull * 1024 * 1024;
constexpr uint64_t kTotal = 2ull * 1024 * 1024 * 1024;
constexpr uint64_t kManifest = 4ull * 1024 * 1024;
constexpr uint64_t kStub = 64ull * 1024 * 1024;
constexpr size_t kFooter = 104, kHeader = 48;
constexpr char kMagic[16] = {'M','D','A','R','C','H','I','V','E','v','1',0,0,0,0,0};
constexpr char kFootMagic[16] = {'M','D','F','O','O','T','E','R','v','1',0,0,0,0,0,0};

struct Handle {
    HANDLE h = INVALID_HANDLE_VALUE;
    ~Handle() { if (h != INVALID_HANDLE_VALUE) CloseHandle(h); }
    Handle() = default;
    Handle(const Handle&) = delete;
    Handle& operator=(const Handle&) = delete;
};
bool Fail(std::wstring& error, const std::wstring& text) { error = text; return false; }
bool WinFail(std::wstring& error, const wchar_t* text) {
    return Fail(error, std::wstring(text) + L" (Windows error " + std::to_wstring(GetLastError()) + L").");
}
bool Cancelled(const std::atomic<bool>* flag, std::wstring& error) {
    if (flag && flag->load(std::memory_order_relaxed)) {
        Fail(error, L"Cancelled. Temporary installation can be discarded.");
        return true;
    }
    return false;
}
uint16_t U16(const unsigned char* p) { return uint16_t(p[0]) | uint16_t(p[1]) << 8; }
uint32_t U32(const unsigned char* p) { return uint32_t(U16(p)) | uint32_t(U16(p + 2)) << 16; }
uint64_t U64(const unsigned char* p) { return uint64_t(U32(p)) | uint64_t(U32(p + 4)) << 32; }
std::string Hex(const unsigned char* p, size_t n) {
    constexpr char digits[] = "0123456789abcdef";
    std::string out(n * 2, '0');
    for (size_t i = 0; i < n; ++i) { out[i * 2] = digits[p[i] >> 4]; out[i * 2 + 1] = digits[p[i] & 15]; }
    return out;
}
struct Sha {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    std::vector<unsigned char> object;
    ~Sha() { if (hash) BCryptDestroyHash(hash); if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0); }
    bool Start(std::wstring& error) {
        DWORD length = 0, got = 0;
        if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0 ||
            BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH, reinterpret_cast<PUCHAR>(&length), sizeof(length), &got, 0) < 0 ||
            !length || length > 1024 * 1024) return Fail(error, L"Cannot initialize SHA256.");
        object.resize(length);
        if (BCryptCreateHash(algorithm, &hash, object.data(), length, nullptr, 0, 0) < 0) return Fail(error, L"Cannot create SHA256 state.");
        return true;
    }
    bool Add(const void* data, size_t length, std::wstring& error) {
        if (length > std::numeric_limits<ULONG>::max() ||
            BCryptHashData(hash, reinterpret_cast<PUCHAR>(const_cast<void*>(data)), static_cast<ULONG>(length), 0) < 0)
            return Fail(error, L"Cannot update SHA256.");
        return true;
    }
    bool Finish(std::string& value, std::wstring& error) {
        unsigned char digest[32];
        if (BCryptFinishHash(hash, digest, sizeof(digest), 0) < 0) return Fail(error, L"Cannot finish SHA256.");
        value = Hex(digest, sizeof(digest));
        return true;
    }
};
bool Size(HANDLE file, uint64_t& size, std::wstring& error) {
    LARGE_INTEGER n{};
    if (!GetFileSizeEx(file, &n) || n.QuadPart < 0) return WinFail(error, L"Cannot read file size");
    size = static_cast<uint64_t>(n.QuadPart); return true;
}
bool Seek(HANDLE file, uint64_t offset, std::wstring& error) {
    if (offset > static_cast<uint64_t>(std::numeric_limits<LONGLONG>::max())) return Fail(error, L"File offset is out of range.");
    LARGE_INTEGER n{}; n.QuadPart = static_cast<LONGLONG>(offset);
    if (!SetFilePointerEx(file, n, nullptr, FILE_BEGIN)) return WinFail(error, L"Cannot seek file");
    return true;
}
bool Read(HANDLE file, void* data, size_t size, std::wstring& error) {
    if (size > std::numeric_limits<DWORD>::max()) return Fail(error, L"Read is out of range.");
    DWORD got = 0;
    if (!ReadFile(file, data, static_cast<DWORD>(size), &got, nullptr)) return WinFail(error, L"Cannot read file");
    if (got != size) return Fail(error, L"File ended unexpectedly.");
    return true;
}
bool ReadAt(HANDLE file, uint64_t offset, void* data, size_t size, std::wstring& error) {
    return Seek(file, offset, error) && Read(file, data, size, error);
}
bool Write(HANDLE file, const void* data, size_t size, std::wstring& error) {
    DWORD wrote = 0;
    if (size > std::numeric_limits<DWORD>::max() || !WriteFile(file, data, static_cast<DWORD>(size), &wrote, nullptr))
        return WinFail(error, L"Cannot write installation file");
    return wrote == size || Fail(error, L"Installation write was incomplete.");
}
bool OrdinaryFile(HANDLE file, std::wstring& error) {
    BY_HANDLE_FILE_INFORMATION info{};
    if (!GetFileInformationByHandle(file, &info)) return WinFail(error, L"Cannot inspect file");
    if (info.dwFileAttributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT))
        return Fail(error, L"A regular file was required; directories and reparse points are forbidden.");
    return true;
}
bool OpenRead(const std::filesystem::path& path, Handle& file, std::wstring& error) {
    file.h = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                         FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
    if (file.h == INVALID_HANDLE_VALUE) return WinFail(error, L"Cannot open required file");
    return OrdinaryFile(file.h, error);
}
std::wstring Fold(std::wstring value) {
    for (wchar_t& c : value) if (c >= L'A' && c <= L'Z') c += L'a' - L'A';
    return value;
}
bool ValidPath(const std::wstring& path) {
    if (path.empty() || path.size() > 240) return false;
    size_t start = 0;
    while (start < path.size()) {
        size_t end = path.find(L'/', start);
        if (end == std::wstring::npos) end = path.size();
        std::wstring part = path.substr(start, end - start);
        if (part.empty() || part == L"." || part == L".." || part.back() == L'.' || part.back() == L' ') return false;
        for (wchar_t c : part) if (c < 32 || c > 126 || std::wcschr(L"<>:\"\\|?*", c)) return false;
        std::wstring stem = Fold(part.substr(0, part.find(L'.')));
        if (stem == L"con" || stem == L"prn" || stem == L"aux" || stem == L"nul" ||
            (stem.size() == 4 && (stem.substr(0, 3) == L"com" || stem.substr(0, 3) == L"lpt") && stem[3] >= L'1' && stem[3] <= L'9')) return false;
        if (end == path.size()) return true;
        start = end + 1;
    }
    return false;
}
bool ValidateFiles(const Info& info, std::wstring& error) {
    if (info.files.empty() || info.files.size() > 8192 || info.totalSize > kTotal) return Fail(error, L"Archive file count or total size is invalid.");
    std::set<std::wstring> paths;
    for (const Entry& entry : info.files)
        if (!paths.insert(Fold(entry.path)).second) return Fail(error, L"Archive contains case-insensitive path aliases.");
    std::wstring previous;
    uint64_t total = 0;
    for (const Entry& entry : info.files) {
        std::wstring key = Fold(entry.path);
        if (!ValidPath(entry.path) || (!previous.empty() && entry.path <= previous) || entry.size > kTotal || total > kTotal - entry.size ||
            entry.sha256.size() != 64 || entry.sha256.find_first_not_of("0123456789abcdef") != std::string::npos)
            return Fail(error, L"Archive paths, ordering, hashes, or file sizes are invalid.");
        for (size_t slash = key.find(L'/'); slash != std::wstring::npos; slash = key.find(L'/', slash + 1))
            if (paths.count(key.substr(0, slash))) return Fail(error, L"Archive file is also a directory prefix.");
        previous = entry.path; total += entry.size;
    }
    return total == info.totalSize || Fail(error, L"Archive total does not match its files.");
}
bool Directory(const std::filesystem::path& path, std::wstring& error) {
    DWORD attrs = GetFileAttributesW(path.c_str());
    if (attrs == INVALID_FILE_ATTRIBUTES) return WinFail(error, L"Cannot inspect installation directory");
    if (!(attrs & FILE_ATTRIBUTE_DIRECTORY) || (attrs & FILE_ATTRIBUTE_REPARSE_POINT))
        return Fail(error, L"Installation directories must be ordinary directories without reparse points.");
    return true;
}
bool SafeRoot(const std::filesystem::path& path, std::filesystem::path& absolute, std::wstring& error) {
    std::error_code ec;
    absolute = std::filesystem::absolute(path, ec).lexically_normal();
    if (ec || absolute.empty()) return Fail(error, L"Installation directory could not be resolved.");
    for (auto cursor = absolute; !cursor.empty();) {
        if (!Directory(cursor, error)) return false;
        auto parent = cursor.parent_path();
        if (parent == cursor) break;
        cursor = parent;
    }
    return true;
}
bool Destination(const std::filesystem::path& root, const Entry& entry, bool create,
                 std::filesystem::path& result, std::wstring& error) {
    result = root;
    size_t start = 0;
    for (size_t slash = entry.path.find(L'/'); slash != std::wstring::npos; slash = entry.path.find(L'/', start)) {
        result /= entry.path.substr(start, slash - start);
        if (create && !CreateDirectoryW(result.c_str(), nullptr) && GetLastError() != ERROR_ALREADY_EXISTS)
            return WinFail(error, L"Cannot create installation directory");
        if (!Directory(result, error)) return false;
        start = slash + 1;
    }
    result /= entry.path.substr(start);
    return true;
}
// Authenticode adds a PE security table at EOF, possibly after 0..7 zero bytes.
// This validates only table structure/bounds, never certificate trust.
bool FooterPosition(HANDLE file, uint64_t length, uint64_t& position, std::wstring& error) {
    if (length < 64 + kFooter) return Fail(error, L"Installer is too small.");
    unsigned char dos[64];
    if (!ReadAt(file, 0, dos, sizeof(dos), error)) return false;
    if (dos[0] != 'M' || dos[1] != 'Z') return Fail(error, L"Installer is not a PE executable.");
    uint64_t pe = U32(dos + 60);
    if (pe < 64 || pe > 1024 * 1024 || pe + 24 > length) return Fail(error, L"PE header offset is invalid.");
    unsigned char coff[24];
    if (!ReadAt(file, pe, coff, sizeof(coff), error)) return false;
    if (std::memcmp(coff, "PE\0\0", 4)) return Fail(error, L"PE signature is invalid.");
    uint16_t optionalSize = U16(coff + 20);
    if (optionalSize < 2 || optionalSize > 4096 || pe + 24 + optionalSize > length) return Fail(error, L"PE optional header is invalid.");
    std::vector<unsigned char> optional(optionalSize);
    if (!ReadAt(file, pe + 24, optional.data(), optional.size(), error)) return false;
    size_t directories = U16(optional.data()) == 0x20b ? 112 : U16(optional.data()) == 0x10b ? 96 : 0;
    if (!directories || optional.size() < directories) return Fail(error, L"PE optional header type is unsupported.");
    uint32_t count = U32(optional.data() + directories - 4);
    uint64_t certificate = 0, certificateSize = 0;
    if (count > 4) {
        if (optional.size() < directories + 40) return Fail(error, L"PE security directory is truncated.");
        certificate = U32(optional.data() + directories + 32);
        certificateSize = U32(optional.data() + directories + 36);
    }
    if (!certificate && !certificateSize) { position = length - kFooter; return true; }
    if (!certificate || !certificateSize || certificate % 8 || certificateSize < 8 || certificateSize > kStub ||
        certificate > length || certificateSize != length - certificate || certificate < pe + 24 + optionalSize + kFooter)
        return Fail(error, L"PE certificate table bounds are invalid.");
    uint64_t cursor = certificate;
    unsigned countCertificates = 0;
    while (cursor < length) {
        unsigned char header[8];
        if (length - cursor < 8 || ++countCertificates > 64 || !ReadAt(file, cursor, header, sizeof(header), error))
            return Fail(error, L"PE certificate table is truncated.");
        uint64_t n = U32(header), padded = (n + 7) & ~uint64_t(7);
        if (n < 8 || padded > length - cursor || (U16(header + 4) != 0x100 && U16(header + 4) != 0x200) || U16(header + 6) != 2)
            return Fail(error, L"PE certificate record is invalid.");
        if (padded > n) {
            unsigned char padding[7];
            if (!ReadAt(file, cursor + n, padding, static_cast<size_t>(padded - n), error)) return false;
            for (size_t i = 0; i < padded - n; ++i) if (padding[i]) return Fail(error, L"PE certificate padding is invalid.");
        }
        cursor += padded;
    }
    for (uint64_t pad = 0; pad < 8 && certificate >= kFooter + pad; ++pad) {
        unsigned char footer[kFooter];
        uint64_t candidate = certificate - pad - kFooter;
        if (!ReadAt(file, candidate, footer, sizeof(footer), error)) return false;
        if (std::memcmp(footer, kFootMagic, 16)) continue;
        if (pad) {
            unsigned char padding[7];
            if (!ReadAt(file, certificate - pad, padding, static_cast<size_t>(pad), error)) return false;
            for (size_t i = 0; i < pad; ++i) if (padding[i]) return Fail(error, L"PE signing alignment padding is invalid.");
        }
        position = candidate; return true;
    }
    return Fail(error, L"Archive footer was not found before the PE certificate table.");
}
bool InspectOpen(HANDLE file, Info& out, std::wstring& error) {
    uint64_t length = 0, footerAt = 0;
    if (!Size(file, length, error) || !FooterPosition(file, length, footerAt, error)) return false;
    unsigned char footer[kFooter];
    if (!ReadAt(file, footerAt, footer, sizeof(footer), error)) return false;
    if (std::memcmp(footer, kFootMagic, 16)) return Fail(error, L"Installer archive footer is missing.");
    Info info;
    info.archiveOffset = U64(footer + 16); info.archiveLength = U64(footer + 24); info.manifestLength = U64(footer + 32);
    info.identity = Hex(footer + 40, 32); info.manifestSha256 = Hex(footer + 72, 32);
    if (info.archiveOffset < 64 || info.archiveOffset > kStub || info.manifestLength < kHeader || info.manifestLength > kManifest ||
        info.archiveLength < info.manifestLength || info.archiveLength > kTotal + kManifest + (kTotal / kChunk + 8192) * 16 ||
        info.archiveOffset > footerAt || info.archiveLength != footerAt - info.archiveOffset)
        return Fail(error, L"Installer archive layout is invalid.");
    std::vector<unsigned char> manifest(static_cast<size_t>(info.manifestLength));
    if (!ReadAt(file, info.archiveOffset, manifest.data(), manifest.size(), error)) return false;
    Sha sha; std::string digest;
    if (!sha.Start(error) || !sha.Add(manifest.data(), manifest.size(), error) || !sha.Finish(digest, error)) return false;
    if (digest != info.manifestSha256) return Fail(error, L"Archive manifest checksum does not match.");
    const unsigned char* h = manifest.data();
    uint32_t files = U32(h + 24);
    info.totalSize = U64(h + 32);
    if (std::memcmp(h, kMagic, 16) || U32(h + 16) != 1 || U32(h + 20) != kChunk || U32(h + 28) ||
        U64(h + 40) != info.manifestLength || !files || files > 8192 || info.totalSize > kTotal)
        return Fail(error, L"Archive manifest header is unsupported or invalid.");
    size_t at = kHeader;
    uint64_t dataAt = info.manifestLength;
    info.files.reserve(files);
    for (uint32_t i = 0; i < files; ++i) {
        if (manifest.size() - at < 64) return Fail(error, L"Archive entry header is truncated.");
        const unsigned char* p = h + at;
        uint16_t nameLength = U16(p);
        if (U16(p + 2) || !nameLength || nameLength > 240 || manifest.size() - at - 64 < nameLength)
            return Fail(error, L"Archive entry path is truncated or invalid.");
        Entry entry;
        entry.chunks = U32(p + 4); entry.size = U64(p + 8); entry.dataOffset = U64(p + 16); entry.dataLength = U64(p + 24);
        entry.sha256 = Hex(p + 32, 32);
        for (size_t j = 0; j < nameLength; ++j) entry.path += static_cast<wchar_t>(p[64 + j]);
        uint64_t expectedChunks = (entry.size + kChunk - 1) / kChunk;
        if (entry.size > kTotal || entry.chunks != expectedChunks || entry.dataOffset != dataAt ||
            entry.dataLength < expectedChunks * 16 || entry.dataLength > entry.size + expectedChunks * 16 ||
            entry.dataLength > info.archiveLength - dataAt)
            return Fail(error, L"Archive entry stream bounds are invalid.");
        dataAt += entry.dataLength; at += 64 + nameLength; info.files.push_back(std::move(entry));
    }
    if (at != manifest.size() || dataAt != info.archiveLength || !ValidateFiles(info, error))
        return error.empty() ? Fail(error, L"Archive contains unlisted or trailing data.") : false;
    out = std::move(info); return true;
}
bool SameInfo(const Info& a, const Info& b) {
    if (a.identity != b.identity || a.totalSize != b.totalSize || a.archiveOffset != b.archiveOffset ||
        a.archiveLength != b.archiveLength || a.manifestLength != b.manifestLength || a.manifestSha256 != b.manifestSha256 || a.files.size() != b.files.size()) return false;
    for (size_t i = 0; i < a.files.size(); ++i) {
        const Entry& x = a.files[i]; const Entry& y = b.files[i];
        if (x.path != y.path || x.size != y.size || x.sha256 != y.sha256 || x.dataOffset != y.dataOffset || x.dataLength != y.dataLength || x.chunks != y.chunks) return false;
    }
    return true;
}
bool HashOpen(HANDLE file, std::string& digest, uint64_t& size, std::wstring& error) {
    if (!Size(file, size, error) || !Seek(file, 0, error)) return false;
    Sha sha; if (!sha.Start(error)) return false;
    std::vector<unsigned char> data(static_cast<size_t>(kChunk));
    for (uint64_t done = 0; done < size;) {
        size_t n = static_cast<size_t>(std::min(kChunk, size - done));
        if (!Read(file, data.data(), n, error) || !sha.Add(data.data(), n, error)) return false;
        done += n;
    }
    return sha.Finish(digest, error);
}
bool ExtractImpl(const std::filesystem::path& installer, const std::filesystem::path& root,
                 const Info& expected, const std::atomic<bool>* cancel, Progress progress, std::wstring& error) {
    if (Cancelled(cancel, error)) return false;
    Handle input; Info info;
    if (!OpenRead(installer, input, error) || !InspectOpen(input.h, info, error)) return false;
    if (!SameInfo(expected, info)) return Fail(error, L"Installer metadata changed after inspection.");
    std::filesystem::path base;
    if (!SafeRoot(root, base, error)) return false;
    struct Decompressor { DECOMPRESSOR_HANDLE h = nullptr; ~Decompressor() { if (h) CloseDecompressor(h); } } decoder;
    if (!CreateDecompressor(COMPRESS_ALGORITHM_XPRESS_HUFF, nullptr, &decoder.h)) return WinFail(error, L"Cannot initialize Windows decompressor");
    Sha archiveSha;
    if (!archiveSha.Start(error) || !Seek(input.h, info.archiveOffset, error)) return false;
    std::vector<unsigned char> manifest(static_cast<size_t>(info.manifestLength));
    if (!Read(input.h, manifest.data(), manifest.size(), error) || !archiveSha.Add(manifest.data(), manifest.size(), error)) return false;
    std::vector<unsigned char> stored(static_cast<size_t>(kChunk)), raw(static_cast<size_t>(kChunk));
    uint64_t complete = 0;
    if (progress) progress(complete, info.totalSize);
    for (const Entry& entry : info.files) {
        if (Cancelled(cancel, error)) return false;
        std::filesystem::path destination;
        if (!Destination(base, entry, true, destination, error)) return false;
        Handle output;
        output.h = CreateFileW(destination.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW,
                               FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
        if (output.h == INVALID_HANDLE_VALUE) return WinFail(error, L"Cannot create a new installation file");
        if (!OrdinaryFile(output.h, error)) return false;
        Sha fileSha; if (!fileSha.Start(error)) return false;
        uint64_t produced = 0, consumed = 0;
        for (uint32_t chunk = 0; chunk < entry.chunks; ++chunk) {
            if (Cancelled(cancel, error)) return false;
            unsigned char header[16];
            if (entry.dataLength - consumed < sizeof(header) || !Read(input.h, header, sizeof(header), error) || !archiveSha.Add(header, sizeof(header), error))
                return error.empty() ? Fail(error, L"Archive chunk header is truncated.") : false;
            consumed += sizeof(header);
            uint32_t rawLength = U32(header), storedLength = U32(header + 4), codec = U32(header + 8);
            uint64_t expectedLength = std::min(kChunk, entry.size - produced);
            if (U32(header + 12) || !rawLength || rawLength != expectedLength || !storedLength || storedLength > rawLength ||
                codec > 1 || (codec == 0 && storedLength != rawLength) || (codec == 1 && storedLength >= rawLength) || storedLength > entry.dataLength - consumed)
                return Fail(error, L"Archive chunk bounds or codec are invalid.");
            if (!Read(input.h, stored.data(), storedLength, error) || !archiveSha.Add(stored.data(), storedLength, error)) return false;
            consumed += storedLength;
            const unsigned char* bytes = stored.data();
            if (codec) {
                SIZE_T actual = 0;
                if (!Decompress(decoder.h, stored.data(), storedLength, raw.data(), rawLength, &actual) || actual != rawLength)
                    return Fail(error, L"Archive decompression failed or produced an unexpected size.");
                bytes = raw.data();
            }
            if (Cancelled(cancel, error)) return false;
            if (!fileSha.Add(bytes, rawLength, error) || !Write(output.h, bytes, rawLength, error)) return false;
            produced += rawLength; complete += rawLength;
            if (progress) progress(complete, info.totalSize);
        }
        std::string digest;
        if (produced != entry.size || consumed != entry.dataLength || !fileSha.Finish(digest, error))
            return error.empty() ? Fail(error, L"Extracted file size is invalid.") : false;
        if (digest != entry.sha256) return Fail(error, L"Extracted file checksum does not match: " + entry.path);
        if (!FlushFileBuffers(output.h)) return WinFail(error, L"Cannot flush installation file");
    }
    if (Cancelled(cancel, error)) return false;
    std::string digest;
    if (!archiveSha.Finish(digest, error)) return false;
    return digest == info.identity || Fail(error, L"Installer archive checksum does not match.");
}
} // namespace

bool Inspect(const std::filesystem::path& installer, Info& info, std::wstring& error) {
    error.clear(); info = Info{};
    try { Handle file; return OpenRead(installer, file, error) && InspectOpen(file.h, info, error); }
    catch (const std::exception&) { return Fail(error, L"Cannot inspect archive metadata."); }
}
bool Extract(const std::filesystem::path& installer, const std::filesystem::path& root,
             const Info& info, const std::atomic<bool>* cancel, Progress progress, std::wstring& error) {
    error.clear();
    try { return ExtractImpl(installer, root, info, cancel, progress, error); }
    catch (const std::exception&) { return Fail(error, L"Cannot extract installer archive."); }
}
bool Verify(const std::filesystem::path& root, const Info& info, std::wstring& error) {
    error.clear();
    try {
        if (!ValidateFiles(info, error)) return false;
        std::filesystem::path base;
        if (!SafeRoot(root, base, error)) return false;
        for (const Entry& entry : info.files) {
            std::filesystem::path file;
            if (!Destination(base, entry, false, file, error)) return false;
            std::string digest; uint64_t size = 0;
            if (!HashFile(file, digest, size, error)) return false;
            if (size != entry.size || digest != entry.sha256) return Fail(error, L"Installed file does not match: " + entry.path);
        }
        return true;
    } catch (const std::exception&) { return Fail(error, L"Cannot verify installed files."); }
}
bool HashFile(const std::filesystem::path& path, std::string& digest, uint64_t& size, std::wstring& error) {
    error.clear(); digest.clear(); size = 0;
    try { Handle file; return OpenRead(path, file, error) && HashOpen(file.h, digest, size, error); }
    catch (const std::exception&) { return Fail(error, L"Cannot hash required file."); }
}
} // namespace mdarchive
