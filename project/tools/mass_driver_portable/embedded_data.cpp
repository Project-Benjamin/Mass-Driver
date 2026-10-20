#include "embedded_data.h"
#include "resource.h"
#include <bcrypt.h>
#include <shlobj.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <vector>

namespace fs = std::filesystem;
namespace {
struct Entry { fs::path name; const unsigned char* data; size_t size; std::array<unsigned char, 32> sha; };

std::array<unsigned char, 32> Hash(const unsigned char* data, size_t size) {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    std::array<unsigned char, 32> result{};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0)
        throw std::runtime_error("Cannot open SHA-256");
    if (BCryptCreateHash(algorithm, &hash, nullptr, 0, nullptr, 0, 0) < 0) {
        BCryptCloseAlgorithmProvider(algorithm, 0); throw std::runtime_error("Cannot create SHA-256");
    }
    NTSTATUS status = 0;
    while (size && status >= 0) {
        ULONG amount = static_cast<ULONG>(std::min<size_t>(size, 1ULL << 24));
        status = BCryptHashData(hash, const_cast<PUCHAR>(data), amount, 0);
        data += amount; size -= amount;
    }
    if (status >= 0) status = BCryptFinishHash(hash, result.data(), static_cast<ULONG>(result.size()), 0);
    BCryptDestroyHash(hash); BCryptCloseAlgorithmProvider(algorithm, 0);
    if (status < 0) throw std::runtime_error("SHA-256 failed");
    return result;
}

bool PlainDirectory(const fs::path& path) {
    DWORD attributes = GetFileAttributesW(path.c_str());
    return attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY) &&
        !(attributes & FILE_ATTRIBUTE_REPARSE_POINT);
}

bool CheckedPath(const fs::path& root, const fs::path& relative) {
    fs::path current = root;
    for (const auto& part : relative.parent_path()) {
        current /= part;
        if (!PlainDirectory(current)) return false;
    }
    DWORD attributes = GetFileAttributesW((root / relative).c_str());
    return attributes != INVALID_FILE_ATTRIBUTES &&
        !(attributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT));
}

bool Verify(const fs::path& root, const std::vector<Entry>& entries) {
    if (!PlainDirectory(root)) return false;
    for (const auto& item : entries) {
        if (!CheckedPath(root, item.name) || fs::file_size(root / item.name) != item.size) return false;
        std::ifstream source(root / item.name, std::ios::binary);
        if (!source) return false;
        std::vector<unsigned char> data((std::istreambuf_iterator<char>(source)), {});
        if (data.size() != item.size || Hash(data.data(), data.size()) != item.sha) return false;
    }
    return true;
}

std::vector<Entry> Parse(const unsigned char* data, size_t size) {
    const unsigned char* end = data + size;
    auto number = [&](size_t bytes) {
        if (static_cast<size_t>(end - data) < bytes) throw std::runtime_error("Truncated bundle");
        unsigned long long value = 0;
        for (size_t i = 0; i != bytes; ++i) value |= static_cast<unsigned long long>(*data++) << (8 * i);
        return value;
    };
    if (size < 12 || std::memcmp(data, "XGMDATA1", 8)) throw std::runtime_error("Invalid bundle");
    data += 8;
    auto count = number(4);
    if (count < 5 || count > 32) throw std::runtime_error("Invalid bundle inventory");
    std::vector<Entry> entries;
    for (unsigned long long i = 0; i != count; ++i) {
        auto nameSize = number(2), contentSize = number(8);
        if (nameSize == 0 || nameSize > 200 || contentSize > (1ULL << 30) ||
            static_cast<unsigned long long>(end - data) < 32 + nameSize + contentSize)
            throw std::runtime_error("Invalid bundle entry");
        Entry entry{};
        std::copy(data, data + 32, entry.sha.begin()); data += 32;
        std::string name(reinterpret_cast<const char*>(data), static_cast<size_t>(nameSize)); data += nameSize;
        if (name.rfind("MassDriverData/", 0) || name.find("..") != std::string::npos ||
            name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./-") != std::string::npos ||
            name.find("//") != std::string::npos || name.back() == '/' || name.find("/./") != std::string::npos)
            throw std::runtime_error("Unsafe bundle path");
        entry.name = fs::path(name);
        const auto extension = entry.name.extension().string();
        if (extension != ".txt" && extension != ".md" && extension != ".template" && extension != ".xdelta")
            throw std::runtime_error("Bundle contains unsupported data");
        for (const auto& prior : entries) if (prior.name == entry.name) throw std::runtime_error("Duplicate bundle entry");
        entry.data = data; entry.size = static_cast<size_t>(contentSize); data += contentSize;
        if (Hash(entry.data, entry.size) != entry.sha) throw std::runtime_error("Embedded data hash mismatch");
        entries.push_back(entry);
    }
    if (data != end) throw std::runtime_error("Trailing bundle data");
    return entries;
}
} // namespace

bool HasEmbeddedData(HINSTANCE instance) {
    return FindResourceW(instance, MAKEINTRESOURCEW(IDR_EMBEDDED_DATA), RT_RCDATA) != nullptr;
}

bool PrepareEmbeddedData(HINSTANCE instance, fs::path& dataRoot, fs::path& defaultGame, std::wstring& error) {
    fs::path stage;
    bool owned = false;
    try {
        HRSRC resource = FindResourceW(instance, MAKEINTRESOURCEW(IDR_EMBEDDED_DATA), RT_RCDATA);
        HGLOBAL loaded = resource ? LoadResource(instance, resource) : nullptr;
        auto* data = loaded ? static_cast<const unsigned char*>(LockResource(loaded)) : nullptr;
        size_t size = resource ? SizeofResource(instance, resource) : 0;
        if (!data || !size) throw std::runtime_error("Embedded support data is missing");
        auto entries = Parse(data, size);
        auto digest = Hash(data, size);
        const wchar_t* hex = L"0123456789abcdef";
        std::wstring key;
        for (auto byte : digest) { key += hex[byte >> 4]; key += hex[byte & 15]; }
        PWSTR local = nullptr;
        if (FAILED(SHGetKnownFolderPath(FOLDERID_LocalAppData, KF_FLAG_CREATE, nullptr, &local)))
            throw std::runtime_error("Local application data is unavailable");
        fs::path base = fs::path(local) / L"Xenogears Mass Driver";
        CoTaskMemFree(local);
        fs::create_directories(base);
        if (!PlainDirectory(base)) throw std::runtime_error("Application data directory is linked or invalid");
        auto cache = base / L"PatcherData";
        fs::create_directories(cache);
        if (!PlainDirectory(cache)) throw std::runtime_error("Cache directory is linked or invalid");
        auto final = cache / key;
        if (fs::exists(final)) {
            if (!Verify(final, entries)) {
                error = L"The cached patch data is missing or changed. Close the app, remove this cache folder, and try again:\r\n" + final.wstring();
                return false;
            }
        } else {
            GUID guid{}; wchar_t text[40]{};
            if (FAILED(CoCreateGuid(&guid)) || !StringFromGUID2(guid, text, 40))
                throw std::runtime_error("Cannot create cache staging identity");
            stage = cache / (L".staging-" + std::wstring(text));
            if (!fs::create_directory(stage)) throw std::runtime_error("Cannot create cache staging directory");
            owned = true;
            for (const auto& item : entries) {
                auto target = stage / item.name;
                fs::create_directories(target.parent_path());
                std::ofstream output(target, std::ios::binary | std::ios::out);
                if (!output || !output.write(reinterpret_cast<const char*>(item.data), item.size))
                    throw std::runtime_error("Cannot extract patch data");
            }
            if (!Verify(stage, entries)) throw std::runtime_error("Extracted data hash mismatch");
            std::error_code moveError;
            fs::rename(stage, final, moveError);
            if (moveError) {
                if (!Verify(final, entries)) throw std::runtime_error("Cannot commit verified patch data");
                fs::remove_all(stage);
            }
            owned = false;
        }
        dataRoot = final;
        defaultGame = base / L"Mass Driver Game";
        return true;
    } catch (...) {
        if (owned) { std::error_code ignored; fs::remove_all(stage, ignored); }
        error = L"Windows could not prepare or verify the embedded patch data in your local application folder.";
        return false;
    }
}
