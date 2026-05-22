import os
import re
import io
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, Form
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from PIL import Image
import uvicorn

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SHARED_DIR = Path(os.getenv("LOCALSHARE_SHARED_DIR", "./shared")).resolve()
PASSWORD = os.getenv("LOCALSHARE_PASSWORD")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "500"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"}
VIDEO_EXTS = {".mp4", ".m4v", ".webm", ".mov", ".avi", ".mkv"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
MEDIA_PREVIEW_EXTS = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS

app = FastAPI(title="LocalShare")

templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")


def check_auth(request: Request) -> bool:
    if PASSWORD is None:
        return True
    return request.cookies.get("auth") == PASSWORD


def validate_path(requested_path: str) -> Path:
    # Normalize backslashes to forward slashes for cross-platform support
    requested_path = requested_path.replace("\\", "/").strip("/")
    if not requested_path:
        return SHARED_DIR
    target = (SHARED_DIR / requested_path).resolve()
    if not target.is_relative_to(SHARED_DIR):
        raise HTTPException(403, "Access denied: path outside shared directory")
    return target


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\-.]", "_", filename)
    filename = re.sub(r"\.+", ".", filename)
    filename = filename.strip(". ")
    if not filename:
        filename = "unnamed"
    return filename


def get_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while path.exists():
        path = parent / f"{stem} ({counter}){suffix}"
        counter += 1
    return path


def get_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if path.is_dir():
        return "folder"
    elif ext in IMAGE_EXTS:
        return "image"
    elif ext in VIDEO_EXTS:
        return "video"
    elif ext in AUDIO_EXTS:
        return "audio"
    else:
        return "file"


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    authenticated = check_auth(request)
    show_login = PASSWORD and not authenticated
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "shared_dir": str(SHARED_DIR),
            "show_login": show_login,
            "has_password": bool(PASSWORD),
            "MAX_UPLOAD_MB": MAX_UPLOAD_MB,
        }
    )


@app.post("/api/auth")
async def auth(request: Request, password: str = Form(...)):
    if password == PASSWORD:
        response = JSONResponse({"success": True})
        response.set_cookie(key="auth", value=password, httponly=True, max_age=3600 * 24)
        return response
    return JSONResponse({"success": False, "error": "Invalid password"}, status_code=401)


@app.get("/api/files")
async def list_files(request: Request, path: str = ""):
    if not check_auth(request):
        raise HTTPException(401, "Unauthorized")
    target = validate_path(path)
    if not target.is_dir():
        raise HTTPException(404, "Not a directory")
    items = []
    for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        relative = item.relative_to(SHARED_DIR)
        item_type = get_file_type(item)
        can_preview = item_type in ("image", "video", "audio")
        has_thumbnail = item_type == "image"
        items.append({
            "name": item.name,
            "path": relative.as_posix(),
            "type": item_type,
            "can_preview": can_preview,
            "has_thumbnail": has_thumbnail,
        })
    parent_path = None
    if target != SHARED_DIR:
        try:
            parent = target.parent
            if parent != SHARED_DIR:
                parent_path = target.relative_to(SHARED_DIR).parent.as_posix()
            else:
                parent_path = ""
        except ValueError:
            parent_path = None
    return JSONResponse({"items": items, "parent": parent_path, "path": str(target.relative_to(SHARED_DIR))})


@app.get("/api/download/{path:path}")
async def download(request: Request, path: str):
    if not check_auth(request):
        raise HTTPException(401, "Unauthorized")
    target = validate_path(path)
    if target.is_dir():
        raise HTTPException(400, "Cannot download a directory")
    if not target.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(target, filename=target.name)


@app.get("/api/preview/{path:path}")
async def preview(request: Request, path: str):
    if not check_auth(request):
        raise HTTPException(401, "Unauthorized")
    target = validate_path(path)
    if not target.exists():
        raise HTTPException(404, "File not found")
    ext = target.suffix.lower()
    if ext not in MEDIA_PREVIEW_EXTS:
        raise HTTPException(400, "File type not supported for preview")
    if ext in IMAGE_EXTS:
        return FileResponse(target)
    elif ext in VIDEO_EXTS:
        if ext == ".m4v":
            return FileResponse(target, media_type="video/x-m4v")
        return FileResponse(target, media_type=f"video/{ext[1:]}")
    elif ext in AUDIO_EXTS:
        return FileResponse(target, media_type=f"audio/{ext[1:]}")


@app.get("/api/thumbnail/{path:path}")
async def thumbnail(request: Request, path: str):
    if not check_auth(request):
        raise HTTPException(401, "Unauthorized")
    target = validate_path(path)
    if not target.exists():
        raise HTTPException(404, "File not found")
    ext = target.suffix.lower()
    if ext not in IMAGE_EXTS:
        raise HTTPException(400, "Not an image")
    try:
        img = Image.open(target)
        img.thumbnail((200, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception:
        raise HTTPException(500, "Could not generate thumbnail")


@app.post("/api/upload")
async def upload(request: Request, path: str = ""):
    if not check_auth(request):
        raise HTTPException(401, "Unauthorized")
    target = validate_path(path)
    if not target.is_dir():
        raise HTTPException(400, "Target must be a directory")
    form = await request.form()
    file = form.get("file")
    if not file:
        raise HTTPException(400, "No file provided")
    original_name = sanitize_filename(file.filename)
    safe_name = sanitize_filename(original_name)
    dest = target / safe_name
    dest = get_unique_path(dest)
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f"File exceeds maximum size of {MAX_UPLOAD_MB}MB")
    with open(dest, "wb") as f:
        f.write(content)
    return JSONResponse({"success": True, "filename": dest.name})


@app.post("/api/create_folder")
async def create_folder(request: Request, path: str = ""):
    if not check_auth(request):
        raise HTTPException(401, "Unauthorized")
    form = await request.form()
    name = sanitize_filename(form.get("name", ""))
    if not name:
        raise HTTPException(400, "Invalid folder name")
    target = validate_path(path)
    if not target.is_dir():
        raise HTTPException(400, "Target must be a directory")
    new_folder = get_unique_path(target / name)
    new_folder.mkdir()
    return JSONResponse({"success": True, "folder": new_folder.name})


if __name__ == "__main__":
    if PASSWORD is None:
        print("\n" + "=" * 60)
        print(" WARNING: No LOCALSHARE_PASSWORD set!")
        print(" Anyone on your network can access your files.")
        print(" Set the LOCALSHARE_PASSWORD environment variable.")
        print("=" * 60 + "\n")

    if not SHARED_DIR.exists():
        SHARED_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created shared directory: {SHARED_DIR}")
    else:
        print(f"Sharing directory: {SHARED_DIR}")

    print(f"Access the app at http://<your-ip>:8000")
    print(f"Max upload size: {MAX_UPLOAD_MB}MB\n")

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)