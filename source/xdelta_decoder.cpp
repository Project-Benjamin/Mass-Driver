#include <windows.h>

#include <algorithm>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

extern "C" {
#include "xdelta3.h"
}

#include "xdelta_decoder.h"

namespace {

constexpr usize_t kInputBufferSize = 1ULL << 23;
constexpr usize_t kSourceBlockSize = 1ULL << 20;
constexpr xoff_t kSourceWindowSize = 1ULL << 26;

class Handle {
public:
    Handle() = default;
    explicit Handle(HANDLE value) : value_(value) {}
    ~Handle() { Close(); }
    Handle(const Handle&) = delete;
    Handle& operator=(const Handle&) = delete;

    HANDLE Get() const { return value_; }
    bool Valid() const { return value_ != INVALID_HANDLE_VALUE; }

private:
    void Close() {
        if (Valid()) {
            CloseHandle(value_);
            value_ = INVALID_HANDLE_VALUE;
        }
    }

    HANDLE value_ = INVALID_HANDLE_VALUE;
};

struct DecoderContext {
    HANDLE source = INVALID_HANDLE_VALUE;
    unsigned long long sourceSize = 0;
    std::vector<uint8_t> sourceBlock;
};

static std::wstring WindowsError(const wchar_t* operation, DWORD value) {
    wchar_t* message = nullptr;
    FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |
        FORMAT_MESSAGE_IGNORE_INSERTS, nullptr, value, 0,
        reinterpret_cast<wchar_t*>(&message), 0, nullptr);
    std::wstring result = operation;
    result += L": ";
    result += message ? message : L"unknown Windows error";
    if (message) LocalFree(message);
    while (!result.empty() && (result.back() == L'\r' || result.back() == L'\n'))
        result.pop_back();
    return result;
}

static std::wstring DecoderError(const xd3_stream& stream, int code) {
    std::wstring result = L"The integrated xdelta decoder rejected the patch (error ";
    result += std::to_wstring(code);
    result += L")";
    if (stream.msg && *stream.msg) {
        result += L": ";
        for (const unsigned char* p = reinterpret_cast<const unsigned char*>(stream.msg); *p; ++p)
            result.push_back(*p < 0x80 ? static_cast<wchar_t>(*p) : L'?');
    }
    result += L".";
    return result;
}

static bool FileSize(HANDLE file, unsigned long long& size) {
    LARGE_INTEGER value{};
    if (!GetFileSizeEx(file, &value) || value.QuadPart < 0) return false;
    size = static_cast<unsigned long long>(value.QuadPart);
    return true;
}

static int ReadSourceBlock(xd3_stream* stream, xd3_source* source, xoff_t blockNumber) {
    auto* context = static_cast<DecoderContext*>(stream->opaque);
    if (!context || context->source == INVALID_HANDLE_VALUE || source->blksize == 0 ||
        blockNumber > std::numeric_limits<unsigned long long>::max() / source->blksize)
        return EINVAL;

    const unsigned long long offset = static_cast<unsigned long long>(blockNumber) * source->blksize;
    if (offset > context->sourceSize) return EINVAL;
    LARGE_INTEGER position{};
    position.QuadPart = static_cast<LONGLONG>(offset);
    if (!SetFilePointerEx(context->source, position, nullptr, FILE_BEGIN)) return EIO;

    const unsigned long long remaining = context->sourceSize - offset;
    const DWORD requested = static_cast<DWORD>(std::min<unsigned long long>(source->blksize, remaining));
    DWORD total = 0;
    while (total < requested) {
        DWORD got = 0;
        if (!ReadFile(context->source, context->sourceBlock.data() + total,
            requested - total, &got, nullptr)) return EIO;
        if (got == 0) return EIO;
        total += got;
    }
    source->curblk = context->sourceBlock.data();
    source->curblkno = blockNumber;
    source->onblk = total;
    return 0;
}

static bool WriteAll(HANDLE file, const uint8_t* data, usize_t size,
    unsigned long long expectedSize, unsigned long long& total, std::wstring& error) {
    if (total > expectedSize || size > expectedSize - total) {
        error = L"The integrated decoder tried to produce more data than the verified output size.";
        return false;
    }
    while (size != 0) {
        const DWORD requested = static_cast<DWORD>(std::min<usize_t>(
            size, std::numeric_limits<DWORD>::max()));
        DWORD written = 0;
        if (!WriteFile(file, data, requested, &written, nullptr)) {
            error = WindowsError(L"The finished BIN could not be written", GetLastError());
            return false;
        }
        if (written == 0) {
            error = L"The finished BIN could not be written: Windows wrote zero bytes.";
            return false;
        }
        data += written;
        size -= written;
        total += written;
    }
    return true;
}

} // namespace

int DecodeVcdiff(HANDLE source, HANDLE patch, const wchar_t* outputPath,
    unsigned long long expectedOutputSize, std::wstring& error) {
    if (source == INVALID_HANDLE_VALUE || patch == INVALID_HANDLE_VALUE ||
        expectedOutputSize == 0) {
        error = L"The integrated decoder received an invalid verified input.";
        return EINVAL;
    }
    Handle output(CreateFileW(outputPath, GENERIC_WRITE, 0, nullptr,
        CREATE_NEW, FILE_ATTRIBUTE_NORMAL | FILE_FLAG_SEQUENTIAL_SCAN, nullptr));
    if (!output.Valid()) {
        error = WindowsError(L"The finished BIN could not be created", GetLastError());
        return EIO;
    }

    unsigned long long sourceSize = 0;
    if (!FileSize(source, sourceSize)) {
        error = WindowsError(L"The source BIN size could not be read", GetLastError());
        return EIO;
    }
    LARGE_INTEGER beginning{};
    if (!SetFilePointerEx(source, beginning, nullptr, FILE_BEGIN) ||
        !SetFilePointerEx(patch, beginning, nullptr, FILE_BEGIN)) {
        error = WindowsError(L"A verified input could not be rewound", GetLastError());
        return EIO;
    }

    DecoderContext context;
    context.source = source;
    context.sourceSize = sourceSize;
    context.sourceBlock.resize(static_cast<size_t>(kSourceBlockSize));
    std::vector<uint8_t> input(static_cast<size_t>(kInputBufferSize));

    xd3_stream stream{};
    xd3_config config{};
    xd3_source sourceDescriptor{};
    bool configured = false;
    auto cleanup = [&]() {
        if (configured) {
            xd3_abort_stream(&stream);
            xd3_free_stream(&stream);
        }
    };

    xd3_init_config(&config, XD3_ADLER32);
    config.winsize = kInputBufferSize;
    config.getblk = ReadSourceBlock;
    config.opaque = &context;
    int result = xd3_config_stream(&stream, &config);
    if (result != 0) {
        error = DecoderError(stream, result);
        cleanup();
        return result;
    }
    configured = true;

    sourceDescriptor.blksize = kSourceBlockSize;
    sourceDescriptor.max_winsize = std::min<xoff_t>(sourceSize, kSourceWindowSize);
    sourceDescriptor.name = "verified Disc 2 source";
    result = xd3_set_source_and_size(&stream, &sourceDescriptor, sourceSize);
    if (result != 0) {
        error = DecoderError(stream, result);
        cleanup();
        return result;
    }

    bool finished = false;
    unsigned long long totalOutput = 0;
    while (!finished) {
        DWORD inputSize = 0;
        if (!ReadFile(patch, input.data(), static_cast<DWORD>(input.size()),
            &inputSize, nullptr)) {
            error = WindowsError(L"The patch could not be read", GetLastError());
            cleanup();
            return EIO;
        }
        const bool atEnd = inputSize < input.size();
        if (atEnd) xd3_set_flags(&stream, stream.flags | XD3_FLUSH);
        xd3_avail_input(&stream, input.data(), inputSize);

        for (;;) {
            result = xd3_decode_input(&stream);
            if (result == XD3_INPUT) {
                finished = atEnd;
                break;
            }
            if (result == XD3_OUTPUT) {
                if (!WriteAll(output.Get(), stream.next_out, stream.avail_out,
                    expectedOutputSize, totalOutput, error)) {
                    cleanup();
                    return EIO;
                }
                xd3_consume_output(&stream);
                continue;
            }
            if (result == XD3_GOTHEADER || result == XD3_WINSTART ||
                result == XD3_WINFINISH) continue;
            if (result == XD3_GETSRCBLK) {
                result = ReadSourceBlock(&stream, &sourceDescriptor, sourceDescriptor.getblkno);
                if (result == 0) continue;
            }
            error = DecoderError(stream, result);
            cleanup();
            return result;
        }
    }

    result = xd3_close_stream(&stream);
    if (result != 0) {
        error = DecoderError(stream, result);
        cleanup();
        return result;
    }
    xd3_free_stream(&stream);
    configured = false;
    if (totalOutput != expectedOutputSize) {
        error = L"The integrated decoder produced an unexpected output size.";
        return EIO;
    }
    if (!FlushFileBuffers(output.Get())) {
        error = WindowsError(L"The finished BIN could not be finalized", GetLastError());
        return EIO;
    }
    return 0;
}
