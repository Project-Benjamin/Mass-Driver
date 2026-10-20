param(
    [Parameter(Mandatory = $true)]
    [string[]] $Keys,
    [int] $HoldMilliseconds = 140,
    [int] $GapMilliseconds = 120
)

$ErrorActionPreference = 'Stop'

Add-Type @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class DuckStationInputNative {
    [StructLayout(LayoutKind.Explicit, Size = 40)]
    public struct Input {
        [FieldOffset(0)] public uint Type;
        [FieldOffset(8)] public KeyboardInput Keyboard;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct KeyboardInput {
        public ushort VirtualKey;
        public ushort ScanCode;
        public uint Flags;
        public uint Time;
        public UIntPtr ExtraInfo;
    }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint SendInput(uint count, Input[] inputs, int size);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr window);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool PostMessage(
        IntPtr window,
        uint message,
        UIntPtr wParam,
        IntPtr lParam
    );

    [DllImport("user32.dll")]
    private static extern uint MapVirtualKey(uint code, uint mapType);

    public static void SendScanCode(ushort scanCode, bool extended, bool released) {
        Input input = new Input();
        input.Type = 1;
        input.Keyboard.ScanCode = scanCode;
        input.Keyboard.Flags = 0x0008u;
        if (extended) input.Keyboard.Flags |= 0x0001u;
        if (released) input.Keyboard.Flags |= 0x0002u;
        Input[] inputs = new Input[] { input };
        if (SendInput(1, inputs, Marshal.SizeOf(typeof(Input))) != 1) {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }

    public static void PostScanCode(
        IntPtr window,
        ushort scanCode,
        bool extended,
        bool released
    ) {
        uint virtualKey = MapVirtualKey(scanCode, 3);
        long flags = 1L | ((long)scanCode << 16);
        if (extended) flags |= 1L << 24;
        if (released) flags |= (1L << 30) | (1L << 31);
        uint message = released ? 0x0101u : 0x0100u;
        if (!PostMessage(
            window,
            message,
            new UIntPtr(virtualKey),
            new IntPtr(flags)
        )) {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }
}
'@

$scanCodes = @{
    Cross = @(0x25, $false) # K
    Circle = @(0x26, $false) # L
    Square = @(0x24, $false) # J
    Triangle = @(0x17, $false) # I
    Up = @(0x48, $true)
    Down = @(0x50, $true)
    Left = @(0x4B, $true)
    Right = @(0x4D, $true)
    Start = @(0x1C, $false) # Enter
    Select = @(0x0E, $false) # Backspace
    Pause = @(0x39, $false) # Space
    FastForward = @(0x0F, $false) # Tab
    SaveState = @(0x3C, $false) # F2
    LoadState = @(0x3B, $false) # F1
    Screenshot = @(0x44, $false) # F10
}

$process = Get-Process | Where-Object {
    $_.ProcessName -like 'duckstation*' -and $_.MainWindowHandle -ne 0
} | Select-Object -First 1

if ($null -eq $process) {
    throw 'No visible DuckStation window was found.'
}

$directWindowInput = (
    -not [DuckStationInputNative]::SetForegroundWindow($process.MainWindowHandle) -and
    [DuckStationInputNative]::GetForegroundWindow() -ne $process.MainWindowHandle
)
Start-Sleep -Milliseconds 250

foreach ($key in $Keys) {
    if (-not $scanCodes.ContainsKey($key)) {
        throw "Unknown DuckStation input: $key"
    }
    $binding = $scanCodes[$key]
    if ($directWindowInput) {
        [DuckStationInputNative]::PostScanCode(
            $process.MainWindowHandle,
            $binding[0],
            $binding[1],
            $false
        )
    } else {
        [DuckStationInputNative]::SendScanCode($binding[0], $binding[1], $false)
    }
    Start-Sleep -Milliseconds $HoldMilliseconds
    if ($directWindowInput) {
        [DuckStationInputNative]::PostScanCode(
            $process.MainWindowHandle,
            $binding[0],
            $binding[1],
            $true
        )
    } else {
        [DuckStationInputNative]::SendScanCode($binding[0], $binding[1], $true)
    }
    Start-Sleep -Milliseconds $GapMilliseconds
}
