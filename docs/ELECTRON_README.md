# IDLIX Downloader - Electron Desktop App

Complete implementation of the HTTP REST API backend with Electron desktop frontend.

## Project Structure

```
idlix-downloader-py/
├── idlix.py                    # Main CLI/API application
├── crypto_helper.py            # AES decryption utilities
├── backend/
│   ├── __init__.py
│   ├── database.py             # SQLite async database layer
│   ├── api_server.py           # FastAPI REST API server
│   └── requirements-api.txt    # API dependencies
├── electron-app/
│   ├── package.json            # Electron app configuration
│   ├── src/
│   │   ├── main/
│   │   │   ├── index.js        # Electron main process
│   │   │   └── preload.js      # Electron preload script
│   │   └── renderer/
│   │       ├── index.html      # Frontend UI
│   │       ├── app.js          # Frontend JavaScript
│   │       └── style.css       # Frontend styles
│   └── assets/
│       └── icon.png            # App icon
└── create_spec_api.py          # PyInstaller spec generator with API support
```

## Features

### Backend (Python + FastAPI)
- ✅ Async REST API with FastAPI
- ✅ SQLite persistence for downloads and jobs
- ✅ Resume interrupted downloads
- ✅ Real-time progress tracking
- ✅ Multi-threaded segment downloading
- ✅ Background task processing
- ✅ Automatic cache management

### Frontend (Electron + Vanilla JS)
- ✅ Modern, responsive UI
- ✅ URL input and video extraction
- ✅ Quality selector with visual cards
- ✅ Custom download path selection
- ✅ Real-time progress bars
- ✅ Download queue management
- ✅ Resume/retry failed downloads
- ✅ Open completed files

## Installation & Setup

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **FFmpeg** (downloaded automatically by build script)

### Quick Start

**Step 1: Build Python Backend**
```bash
chmod +x build_backend.sh
./build_backend.sh
```

This creates `./dist/idlix-downloader` with API support.

**Step 2: Install Electron Dependencies**

⚠️ **Important for WSL Users**: Run from native WSL terminal (Ubuntu app), NOT from Windows Terminal accessing WSL via UNC path.

```bash
cd electron-app
rm -rf node_modules package-lock.json  # Clean if previous install failed
npm install
cd ..
```

**Common npm install issues:**
- **WSL/Windows UNC path error**: Open native WSL terminal (Ubuntu app), not Windows Terminal
- **ENOTEMPTY error**: Run `rm -rf electron-app/node_modules` first
- **Permission errors**: Don't use `sudo`, ensure proper file ownership

**Step 3: Run Development Mode**
```bash
cd electron-app
npm start
```

### Alternative: Test Backend Without Electron

```bash
# Start API server
./dist/idlix-downloader --api-server --port 8765

# Test endpoints
curl http://127.0.0.1:8765/
```

## Installation & Usage

### 1. Development Testing

Already done if you followed Quick Start above. Skip to step 2.

### 2. Build for Production

```bash
# Build Electron app (Python backend must be built first)
cd electron-app
npm run build           # Auto-detect platform
npm run build:win       # Windows NSIS installer
npm run build:linux     # Linux AppImage/deb
npm run build:mac       # macOS dmg
```

Output in `electron-app/dist-electron/`

### Alternative Build Methods

**Method 1: Custom PyInstaller spec (already done by build_backend.sh)**
```bash
python3 create_spec_api.py
python3 -m PyInstaller --clean idlix_windows_api.spec
```

**Method 2: Direct uvicorn (development only)**
```bash
cd backend
uvicorn api_server:app --reload --port 8765
```

## Troubleshooting

### npm install fails with UNC path error
**Solution**: Run from native WSL terminal, not Windows Terminal accessing WSL
```bash
# Open Ubuntu app (not Windows Terminal)
cd ~/idlix-downloader-py/electron-app
rm -rf node_modules package-lock.json
npm install
```

### Backend won't start in Electron
1. Test manually: `./dist/idlix-downloader --api-server --port 8765`
2. Should output: `{"status": "ready", "port": 8765}`
3. Check for errors in terminal

### Electron shows "Backend not ready"
- Verify backend executable exists: `ls -lh dist/idlix-downloader`
- Check Electron logs in DevTools (Ctrl+Shift+I)
- Ensure port 8765 is not in use: `lsof -i :8765`

### Downloads not persisting after restart
- Database location: `~/.local/share/idlix-downloader/downloads.db` (Linux)
- Check file permissions on database directory

### 1. Install Dependencies

## API Endpoints

### Video Extraction
```http
POST /api/extract
Content-Type: application/json

{
  "movie_url": "https://idlix.example.com/movie/..."
}

Response:
{
  "job_id": "uuid",
  "video_title": "Movie Title",
  "embed_url": "https://...",
  "status": "ready"
}
```

### Get Quality Variants
```http
GET /api/variants/{job_id}

Response:
{
  "job_id": "uuid",
  "video_title": "Movie Title",
  "variants": [
    {
      "quality": "1080p",
      "label": "1920x1080 (1080p) - 3.2 Mbps",
      "url": "https://...",
      "bandwidth": 3200000,
      "resolution": [1920, 1080]
    }
  ]
}
```

### Start Download
```http
POST /api/download
Content-Type: application/json

{
  "job_id": "uuid",
  "quality": "1080p",
  "output_path": "/path/to/downloads",
  "filename": "movie.mp4",
  "threads": 16
}

Response:
{
  "download_id": "uuid",
  "status": "starting",
  "message": "Download started: movie.mp4"
}
```

### Get Progress
```http
GET /api/progress/{download_id}

Response:
{
  "download_id": "uuid",
  "status": "downloading",
  "percent": 45.5,
  "downloaded_segments": 123,
  "total_segments": 270,
  "speed_mbps": 5.2,
  "speed_segments": 15.3,
  "eta_seconds": 180,
  "bytes_downloaded": 45000000,
  "errors": []
}
```

### Resume Download
```http
POST /api/resume/{download_id}

Response:
{
  "message": "Download resumed",
  "download_id": "uuid"
}
```

### Cancel Download
```http
DELETE /api/cancel/{download_id}

Response:
{
  "message": "Download cancelled",
  "download_id": "uuid"
}
```

### List Downloads
```http
GET /api/downloads?status=downloading

Response:
{
  "downloads": [...],
  "total": 3
}
```

## Database Schema

### Jobs Table
Stores video extraction information:
- `job_id` (PRIMARY KEY)
- `movie_url`
- `video_title`
- `embed_url`
- `base_url`
- `status`
- `created_at`, `updated_at`

### Variants Table
Stores quality options for each job:
- `id` (PRIMARY KEY)
- `job_id` (FOREIGN KEY)
- `quality`, `label`, `stream_url`
- `bandwidth`, `resolution`

### Downloads Table
Stores download progress and state:
- `download_id` (PRIMARY KEY)
- `job_id` (FOREIGN KEY)
- `quality`, `output_path`, `filename`
- `cache_dir`, `stream_url`
- `total_segments`, `downloaded_segments`, `failed_segments`
- `bytes_downloaded`, `file_size`
- `status`, `progress_json`, `error_message`
- `created_at`, `updated_at`

### Settings Table
Stores app configuration:
- `key` (PRIMARY KEY)
- `value`
- `updated_at`

**Database Location:**
- Windows: `%APPDATA%\idlix-downloader\downloads.db`
- Linux: `~/.local/share/idlix-downloader/downloads.db`
- macOS: `~/Library/Application Support/idlix-downloader/downloads.db`

## Architecture

### Backend Flow
1. User provides IDLIX URL → Extract video info
2. Get M3U8 variants → Store in database
3. User selects quality → Start download task
4. Background thread downloads segments with progress callbacks
5. Progress updates → In-memory dict + periodic DB writes
6. Frontend polls `/api/progress/{id}` every 500ms
7. On completion → Merge segments with FFmpeg → Cleanup cache

### Electron Integration
1. Main process spawns Python backend with `--api-server --port 0`
2. Backend outputs `{"status":"ready","port":8765}` to stdout
3. Main process parses port, provides to renderer via IPC
4. Renderer uses `fetch()` to communicate with `http://127.0.0.1:PORT/api/*`
5. File dialogs handled via IPC (`selectDownloadDirectory`)
6. Settings stored with `electron-store`

### Progress Tracking
- **In-memory**: Fast access for active downloads (polling every 500ms)
- **Database**: Persistent storage for resume capability
- **Callback mechanism**: Thread-safe progress updates from download workers
- **States**: `pending` → `downloading` → `merging` → `completed`/`failed`
- **Interrupted downloads**: Marked on app restart, can be resumed

## Development Tips

### Backend Development
```bash
# Run API server with auto-reload
cd backend
uvicorn api_server:app --reload --port 8765

# Test endpoints with curl
curl http://localhost:8765/
curl -X POST http://localhost:8765/api/extract \
  -H "Content-Type: application/json" \
  -d '{"movie_url":"https://..."}'
```

### Frontend Development
```bash
# Run Electron with DevTools
cd electron-app
npm start

# The app will use the built Python executable from ../dist/
```

### Debugging
- Backend logs: Check terminal output when running API server
- Frontend logs: Open DevTools in Electron (Ctrl+Shift+I)
- Database inspection: Use any SQLite browser to view `downloads.db`
- Crash logs: Check `idlix_crash.log` next to executable

## Build Configurations

### PyInstaller Spec (API-enabled)
- Includes FastAPI, Uvicorn, Pydantic, aiosqlite
- Bundles backend modules (database.py, api_server.py)
- Hidden imports for all API dependencies
- Runtime hooks for SSL certificates and crash handling

### Electron Builder
- Packages Electron app with Python backend embedded
- Copies built executable to `resources/backend/`
- Creates installers for Windows (NSIS), Linux (AppImage/deb), macOS (dmg)
- Auto-update support can be added via `electron-updater`

## Troubleshooting

### Backend won't start
- Check if port is already in use
- Ensure all API dependencies are installed
- Look for error messages in stdout/stderr

### Frontend can't connect
- Verify backend is running and ready
- Check backend URL in DevTools console
- Ensure no firewall blocking localhost connections

### Downloads fail
- Check internet connection
- Verify M3U8 URL hasn't expired (30min TTL)
- Check cache directory permissions
- Look at error details in progress response

### Resume doesn't work
- Ensure cache directory exists
- Check database for download record
- Verify status is 'interrupted' or 'failed'

## License

Apache License 2.0
