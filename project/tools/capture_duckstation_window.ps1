$ErrorActionPreference = 'Stop'

Add-Type @'
using System;
using System.Runtime.InteropServices;

public static class WindowCaptureNative {
    [StructLayout(LayoutKind.Sequential)]
    public struct Rect {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out Rect rect);

    [DllImport("user32.dll")]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);
}
'@

Add-Type -AssemblyName System.Drawing

$process = Get-Process | Where-Object {
    $_.ProcessName -like 'duckstation*' -and $_.MainWindowHandle -ne 0
} | Select-Object -First 1

if ($null -eq $process) {
    throw 'No visible DuckStation window was found.'
}

$rect = New-Object WindowCaptureNative+Rect
if (-not [WindowCaptureNative]::GetWindowRect($process.MainWindowHandle, [ref]$rect)) {
    throw 'GetWindowRect failed for DuckStation.'
}

$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) {
    throw "DuckStation returned an invalid window rectangle: ${width}x${height}."
}

$output = Join-Path $PSScriptRoot '..\work\live_duckstation_window.png'
$bitmap = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
try {
    $deviceContext = $graphics.GetHdc()
    try {
        # PW_RENDERFULLCONTENT asks Windows to render the selected window even
        # when another application overlaps it. CopyFromScreen captured the
        # foreground application instead of DuckStation in that situation.
        if (-not [WindowCaptureNative]::PrintWindow(
            $process.MainWindowHandle,
            $deviceContext,
            2
        )) {
            throw 'PrintWindow failed for DuckStation.'
        }
    } finally {
        $graphics.ReleaseHdc($deviceContext)
    }
    $bitmap.Save($output, [System.Drawing.Imaging.ImageFormat]::Png)
} finally {
    $graphics.Dispose()
    $bitmap.Dispose()
}

(Resolve-Path $output).Path
