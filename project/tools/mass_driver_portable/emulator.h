#pragma once

#include <windows.h>
#include <filesystem>
#include <string>

enum class EmulatorKind { None, DuckStation, RetroArch, Standalone };

struct Emulator {
    EmulatorKind kind = EmulatorKind::None;
    std::filesystem::path path;
    std::filesystem::path core;
    std::wstring name;
};

Emulator DetectEmulator();
Emulator DescribeEmulatorForDiagnostics(const std::filesystem::path& path);
Emulator ChooseEmulator(HWND owner, bool& canceled, std::wstring& error);
bool LaunchGame(const Emulator& emulator, const std::filesystem::path& cue, std::wstring& error);
void OpenDuckStationPage(HWND owner);
void OpenRetroArchPage(HWND owner);
