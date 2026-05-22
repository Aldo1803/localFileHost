# LocalShare

A simple Python FastAPI web app to share files from a local folder to devices on your local network through a mobile-friendly dark-mode web interface.

## Features

- Browse folders and files in a clean UI
- Download files
- Preview images, videos, and audio in browser
- Upload files to the current folder
- Create new folders
- Password protection (optional)
- Mobile-friendly (works on iPhone, Android, and desktop)
- Dark-mode interface
- Image thumbnails

## Requirements

- Python 3.8+
-Works on Windows, Linux, macOS, and Android (via Termux)

## Quick Start (Windows)

### 1. Clone from GitHub

```powershell
git clone https://github.com/Aldo1803/localFileHost.git
cd localFileHost
```

### 2. Create a virtual environment (recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
copy .env.example .env
```

Open `.env` and set your password and shared folder path:

```
LOCALSHARE_PASSWORD=changeme
LOCALSHARE_SHARED_DIR=C:\Xx
MAX_UPLOAD_MB=3072
```

### 5. Run

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Get your PC IP (Windows)

```powershell
ipconfig
```

Look for `IPv4 Address` under your active adapter (e.g. `192.168.1.72`).

### 7. Access from your phone

Open your phone browser and go to:

```
http://192.168.1.72:8000
```

Replace the IP with your actual one.

---

## Quick Start (Android via Termux)

### 1. In Termux, install dependencies

```bash
pkg update
pkg install python git
```

### 2. Clone the project from GitHub

```bash
git clone https://github.com/Aldo1803/localFileHost.git
cd localFileHost
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note:** If `pip install` appears stuck while building `pydantic-core`, just wait -- it takes 5-15 minutes to compile on a phone. It is not frozen. A workaround is to install `clang` and `rust` first via `pkg install clang rust`.

### 4. Set up shared folder

Termux has its own filesystem. After `termux-setup-storage`, these paths are available:

```bash
termux-setup-storage  # Only needed once
ls ~/storage/shared/  # Android internal storage (/sdcard)
ls ~/storage/dcim/    # Camera photos
ls ~/storage/downloads/
```

Copy `.env.example` to `.env` and set the path you want to share:

```bash
cp .env.example .env
nano .env
```

Example for sharing your Downloads folder:

```
LOCALSHARE_PASSWORD=changeme
LOCALSHARE_SHARED_DIR=/data/data/com.termux/files/home/storage/shared/Download
MAX_UPLOAD_MB=3072
```

### 5. Run the app

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If port 8000 is already in use, pick another:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 6. Get your phone's IP

```bash
ifconfig
```

Or:

```bash
ip addr
```

Look for the `inet` address on your Wi-Fi interface (usually `wlan0`), e.g. `192.168.0.15`.

### 7. Access from other devices

From any device on the same Wi-Fi network:

```
http://192.168.0.15:8000
```

Use the port you actually chose (8000, 8001, etc.).

---

## Environment Variables

| Variable                | Default          | Description                          |
|-------------------------|------------------|--------------------------------------|
| `LOCALSHARE_PASSWORD`   | `changeme`       | Password to protect the app          |
| `LOCALSHARE_SHARED_DIR` | `./shared`       | Folder to share                      |
| `MAX_UPLOAD_MB`         | `500`            | Maximum upload size in MB            |

---

## Security Notes

- The shared folder path is resolved to an absolute path at startup to prevent traversal attacks.
- Every file request validates that the path stays inside the shared directory.
- Upload filenames are sanitized to remove dangerous characters.
- Files cannot be overwritten; duplicates get a suffix like `file (1).txt`.
- Password is stored in a cookie (HTTP-only for security).
- If no password is set, a warning is shown on startup.

## Supported Media Previews

**Images:** jpg, jpeg, png, gif, webp, svg, bmp

**Video:** mp4, m4v, webm, mov, avi, mkv

**Audio:** mp3, wav, ogg, m4a, flac

## Troubleshooting

### App won't start

**Windows:**
Make sure you're in the project directory and the virtual environment is activated.

```powershell
cd localFileHost
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Termux:**
Ensure you are inside the project folder before running uvicorn.

```bash
cd ~/localFileHost
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Can't access from another device

1. Make sure both devices are on the **same Wi-Fi network**.
2. **Windows only:** Check your PC's firewall allows the port.
3. Try accessing via `http://localhost:8000` from the host device to verify the app is running.
4. On Termux, the Android device itself handles network access -- no extra firewall rules are needed.

### Upload fails

- Check if the file size exceeds `MAX_UPLOAD_MB`.
- Make sure the shared folder is writable.
- On Termux, shared storage paths (`~/storage/...`) are writable, but you might need to grant storage permission if files are missing.

### Password not working

Make sure you set `LOCALSHARE_PASSWORD` in the `.env` file (not `.env.example`) and restart the app.

### IP address is not reachable

- Some mobile hotspots create an isolated network where the host device is not accessible.
- Use a traditional router Wi-Fi network instead of mobile hotspot.
- On Windows, if using a VPN, disconnect it briefly to verify local access works.
