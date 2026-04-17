param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_SDK_ROOT = "C:\Users\Server4\AppData\Local\Android\Sdk"
$env:GRADLE_USER_HOME = Join-Path $projectRoot ".gradle-user-clean"
$env:ANDROID_USER_HOME = Join-Path $projectRoot ".android-user"

New-Item -ItemType Directory -Force -Path $env:GRADLE_USER_HOME | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $env:ANDROID_USER_HOME "cache") | Out-Null

Push-Location $projectRoot
try {
    if ($Configuration -eq "Release") {
        foreach ($name in @("FIRETV_STORE_FILE", "FIRETV_STORE_PASSWORD", "FIRETV_KEY_ALIAS", "FIRETV_KEY_PASSWORD")) {
            if (-not (Get-Item "Env:$name" -ErrorAction SilentlyContinue)) {
                throw "Missing required environment variable for release signing: $name"
            }
        }
        & ".\gradlew.bat" --no-daemon verifyReleaseSigning assembleRelease
    }
    else {
        & ".\gradlew.bat" --no-daemon assembleDebug
    }
}
finally {
    Pop-Location
}
