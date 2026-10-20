#pragma once

#include <atomic>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

// Private installer archive v1. Paths are normalized, printable ASCII using '/'.
// Archive metadata is public for diagnostics; Extract re-inspects the installer
// and rejects metadata which differs from the inspected archive.
namespace mdarchive {
struct Entry {
    std::wstring path;
    uint64_t size = 0;
    std::string sha256;
    uint64_t dataOffset = 0; // Relative to archive start, not the PE file.
    uint64_t dataLength = 0;
    uint32_t chunks = 0;
};
struct Info {
    std::string identity; // SHA256 of the complete manifest + chunk stream.
    uint64_t totalSize = 0;
    std::vector<Entry> files;
    uint64_t archiveOffset = 0;
    uint64_t archiveLength = 0;
    uint64_t manifestLength = 0;
    std::string manifestSha256;
};
using Progress = std::function<void(uint64_t, uint64_t)>;
bool Inspect(const std::filesystem::path& installer, Info&, std::wstring& error);
// Creates only listed files with CREATE_NEW. Caller owns staging and cleanup.
// Returns false with an error beginning "Cancelled." for cooperative cancellation.
bool Extract(const std::filesystem::path& installer, const std::filesystem::path& root,
             const Info&, const std::atomic<bool>* cancel, Progress, std::wstring& error);
// Checks every listed file. Unlisted mutable files are left alone.
bool Verify(const std::filesystem::path& root, const Info&, std::wstring& error);
bool HashFile(const std::filesystem::path&, std::string&, uint64_t&, std::wstring& error);
} // namespace mdarchive
