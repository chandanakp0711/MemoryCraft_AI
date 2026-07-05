"""Central configuration: paths, media constraints and render defaults."""

from pathlib import Path

# ---------------------------------------------------------------- paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "memorycraft.db"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
SAMPLE_DIR = BASE_DIR / "assets" / "samples"

for _d in (DATA_DIR, UPLOAD_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- media ---
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}

MAX_UPLOAD_MB = 200          # per-file guard rail
MAX_PHOTOS = 500             # supported without degrading

# --------------------------------------------------------------- render ---
VIDEO_SIZE = (1920, 1080)    # full-HD output
VIDEO_FPS = 30
PHOTO_DURATION = 4.0         # seconds each photo is on screen
CROSSFADE = 0.9              # seconds of overlap between slides
TITLE_DURATION = 5.0         # opening / closing scenes
KEN_BURNS_ZOOM = 1.12        # max zoom factor for pan & zoom effect

PREVIEW_SIZE = (854, 480)    # fast draft renders
PREVIEW_FPS = 24

# ------------------------------------------------------------------ pdf ---
PDF_PAGE_SIZE = "A4"
PDF_PHOTOS_PER_PAGE = 2

# Windows font fallbacks used by the title-card renderer. The first file
# that exists on the machine wins; Pillow's built-in font is the final net.
FONT_CANDIDATES = {
    "serif": ["georgia.ttf", "times.ttf", "constan.ttf"],
    "serif-bold": ["georgiab.ttf", "timesbd.ttf", "constanb.ttf"],
    "sans": ["segoeui.ttf", "arial.ttf", "calibri.ttf"],
    "sans-bold": ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"],
    "script": ["segoesc.ttf", "ITCKRIST.TTF", "comic.ttf"],
}
SYSTEM_FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts"), Path("~/.fonts").expanduser()]
