param(
    [string]$DeviceSerial = "",
    [string]$ConnectIp = "",
    [switch]$BuildFirst
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$adbPath = "C:\Users\Server4\AppData\Local\Android\Sdk\platform-tools\adb.exe"
$apkPath = Join-Path $projectRoot "app\build\outputs\apk\debug\app-debug.apk"
$packageName = "com.example.firetvwelcome"

if (-not (Test-Path $adbPath)) {
    throw "adb was not found at $adbPath"
}

Push-Location $projectRoot
try {
    if ($BuildFirst) {
        powershell -ExecutionPolicy Bypass -File ".\build-firetv.ps1"
    }

    if (-not (Test-Path $apkPath)) {
        throw "Debug APK not found at $apkPath. Run .\build-firetv.ps1 first or pass -BuildFirst."
    }

    if ($ConnectIp) {
        & $adbPath connect $ConnectIp
    }

    $deviceLines = & $adbPath devices
    $connectedDevices = $deviceLines |
        Select-Object -Skip 1 |
        Where-Object { $_ -match "\S+\s+device$" } |
        ForEach-Object { ($_ -split "\s+")[0] }

    if (-not $connectedDevices -or $connectedDevices.Count -eq 0) {
        throw "No connected Fire TV or Android TV device was found. Enable ADB debugging and connect the device first."
    }

    $targetDevice = $DeviceSerial
    if (-not $targetDevice) {
        if ($connectedDevices.Count -gt 1) {
            throw "Multiple devices are connected. Re-run with -DeviceSerial and choose one of: $($connectedDevices -join ', ')"
        }
        $targetDevice = $connectedDevices[0]
    }

    Write-Host "Installing debug APK to $targetDevice..."
    & $adbPath -s $targetDevice install -r $apkPath

    Write-Host "Launching app on $targetDevice..."
    & $adbPath -s $targetDevice shell monkey -p $packageName -c android.intent.category.LAUNCHER 1
}
finally {
    Pop-Location
}
