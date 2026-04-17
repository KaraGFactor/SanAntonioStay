# Airbnb Welcome Screen for Fire TV

This project now has two parts:

- A password-protected admin website for editing guest and property details
- A native Android/Fire TV app that registers itself, shows a pairing code, and then displays the active stay for its assigned property full-screen
- A simple Python backend with SQLite storage and no external dependencies

## Run locally

```powershell
python app.py
```

Optional admin credentials for hosted use:

```powershell
$env:WELCOME_ADMIN_USERNAME="your-admin-name"
$env:WELCOME_ADMIN_PASSWORD="replace-this-with-a-strong-password"
python app.py
```

Then open:

- Login page: `http://127.0.0.1:8000/login.html`
- Admin dashboard: `http://127.0.0.1:8000/admin.html`
- Example browser display: `http://127.0.0.1:8000/display.html?property=lake-house&stay=stay-1001`
- Fire TV API feed: `http://127.0.0.1:8000/api/tv?property=lake-house`
- Health check: `http://127.0.0.1:8000/healthz`

## Fire TV flow

1. Open the desktop admin page.
2. In the Fire TV app, enter the backend server URL once.
3. The TV shows a pairing code.
4. Enter that pairing code in the desktop admin site to assign the TV to a property.
5. Choose a stay and click `Show this stay on Fire TV`.
6. Save changes.
7. The TV app refreshes automatically and always shows that property's active stay.

## Android project

The native Fire TV app lives under `app/src/main/...` and is a standard Android TV project written in Kotlin.

The project now builds from the terminal with the included Gradle wrapper.

## Deploy online

This repo is now prepared for simple container hosting.

Included deployment files:

- `Dockerfile`
- `render.yaml`
- `railway.json`

Minimum production environment variables:

- `WELCOME_ADMIN_USERNAME`
- `WELCOME_ADMIN_PASSWORD`
- `WELCOME_SESSION_SECRET`

Recommended deployment flow:

1. Push this repo to GitHub.
2. Create a new web service on Render or Railway from that repo.
3. Set the three environment variables above.
4. Deploy the service.
5. Update the Fire TV app so its server URL points to your hosted domain instead of your local computer.

Important note about persistence:

- Right now the app stores data in SQLite at `data/app.db`.
- On many simple cloud platforms, container filesystems are ephemeral.
- That means for real production use, you should plan on either attaching persistent disk storage or moving the data layer to a hosted database.
- The current setup is good for first deployment and proof of concept, but the next scalability step is a managed database.

## Build the Fire TV app

Debug build:

```powershell
.\build-firetv.ps1
```

Release build:

1. Copy `release-signing.example.ps1` to a local, private script and fill in your keystore values.
2. Run that script in PowerShell to set the signing environment variables.
3. Build the signed release:

```powershell
.\build-firetv.ps1 -Configuration Release
```

Install debug build to a connected Fire TV:

```powershell
.\install-firetv.ps1 -BuildFirst
```

Install to a Fire TV over Wi-Fi:

```powershell
.\install-firetv.ps1 -ConnectIp 192.168.1.50:5555 -BuildFirst
```

If more than one Android/Fire TV device is connected:

```powershell
.\install-firetv.ps1 -DeviceSerial DEVICE_SERIAL
```

Current debug APK output:

- `app/build/outputs/apk/debug/app-debug.apk`

Required release signing environment variables:

- `FIRETV_STORE_FILE`
- `FIRETV_STORE_PASSWORD`
- `FIRETV_KEY_ALIAS`
- `FIRETV_KEY_PASSWORD`

## Notes

- This repo keeps signing secrets out of source control by using environment variables.
- The build uses local project-scoped Gradle and Android cache folders to avoid Windows profile permission issues.
- `install-firetv.ps1` installs the debug APK with `adb` and launches the app on the selected device.
- The backend migrates seed data from `data/store.json` into `data/app.db` on first run, then uses SQLite after that.
