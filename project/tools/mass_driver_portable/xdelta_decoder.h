#pragma once

#include <windows.h>

#include <string>
#include <atomic>

// Applies a VCDIFF patch in this process. The decoder never launches a helper
// program and never changes the source file.
int DecodeVcdiff(HANDLE source, HANDLE patch, const wchar_t* outputPath,
    unsigned long long expectedOutputSize, std::wstring& error,
    const std::atomic<bool>* cancel = nullptr);
