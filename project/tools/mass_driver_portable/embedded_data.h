#pragma once
#include <windows.h>
#include <filesystem>
#include <string>

// Optional, data-only native resource. No executable is extracted or launched.
bool HasEmbeddedData(HINSTANCE instance);
bool PrepareEmbeddedData(HINSTANCE instance, std::filesystem::path& dataRoot,
    std::filesystem::path& defaultGame, std::wstring& error);
