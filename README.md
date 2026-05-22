# LocalShare

A simple Python FastAPI web app to share files from a local folder to devices on your local network through a mobile-friendly dark-mode web interface.

## Features

- Browse folders and files in a clean UI
- Download files
- Preview images, videos, and audio in browser
- Upload files to the current folder
- Create new folders
- Password protection (optional)
- Mobile-friendly (works on iPhone and Android)
- Dark-mode interface

## Requirements

- Python 3.8+
- Windows (or any OS with Python installed)

## Setup

### 1. Clone or download the project

Place the project folder anywhere on your PC.

### 2. Create a virtual environment (recommended)

```powershell
cd localFileSharing
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and edit if needed:

```powershell
copy .env.example .env
```

Open `.env` in a text editor. The defaults:

```
LOCALSHARE_PASSWORD=changeme
LOCALSHARE_SHARED_DIR=C:\Xx
MAX_UPLOAD_MB=500
```

**Environment variables:**

| Variable           | Default      | Description                     |
|--------------------|--------------|---------------------------------|
| `LOCALSHARE_PASSWORD` | `changeme`   | Password to protect the app    |
| `LOCALSHARE_SHARED_DIR` | `C:\Xx`     | Folder to share                 |
| `MAX_UPLOAD_MB`    | `500`        | Maximum upload size in MB        |

### 5. The shared folder

The `shared` folder will be created automatically if it doesn't exist. In our case, we're using `C:\Xx` as configured in `.env`.

## Running the App

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You should see output like:

```
Sharing directory: C:\Xx
Access the app at http://<your-ip>:8000
Max upload size: 500MB
```

## Finding Your PC IP Address

To access the app from your phone or other devices, you need your PC's IP address on the local network.

### Using ipconfig (Windows)

Open Command Prompt or PowerShell and run:

```powershell
ipconfig
```

Look for **IPv4 Address** under your active network adapter (Wi-Fi or Ethernet). It will look something like `192.168.1.100`.

Example output:

```
Wireless LAN adapter Wi-Fi:

   Connection-specific DNS Suffix  . : home
   IPv4 Address. . . . . . . . . . . : 192.168.1.100
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.1.1
```

### Accessing from Other Devices

On your phone or tablet, open a browser and go to:

```
http://192.168.1.100:8000
```

(Replace `192.168.1.100` with your actual IP address.)

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

Make sure you're in the project directory and the virtual environment is activated.

```powershell
cd localFileSharing
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Can't access from phone

1. Make sure your phone is on the same Wi-Fi network as your PC.
2. Check your PC's firewall allows port 8000.
3. Try accessing from a different browser.
4. Try accessing via `http://localhost:8000` from your PC to verify the app is running.

### Upload fails

- Check if the file size exceeds `MAX_UPLOAD_MB`.
- Make sure the shared folder is writable.

### Password not working

Make sure you set `LOCALSHARE_PASSWORD` in the `.env` file (not `.env.example`) and restart the app.