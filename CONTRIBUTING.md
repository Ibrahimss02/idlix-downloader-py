# Contributing to IDLIX Downloader

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🏗️ Project Structure

```
idlix-downloader-py/
├── backend/                 # Python FastAPI backend
│   ├── api_server.py       # REST API endpoints
│   ├── database.py         # SQLite async database
│   └── requirements-api.txt
├── electron-app/           # Electron desktop application
│   ├── src/
│   │   ├── main/          # Electron main process
│   │   └── renderer/      # UI (HTML/CSS/JS)
│   ├── assets/            # App icons
│   └── package.json
├── idlix.py               # Core downloader class
├── crypto_helper.py       # AES decryption utilities
├── build_backend.sh       # Backend build script
├── idlix_windows_api.spec # PyInstaller configuration
├── archive/               # Old CLI-specific code
└── docs/                  # Additional documentation
```

## 🔧 Development Setup

### Prerequisites
- Python 3.10+ with pip
- Node.js 20+ with npm
- FFmpeg installed on system
- Git

### Setup Steps

1. **Clone and setup Python environment:**
```bash
git clone https://github.com/Ibrahimss02/idlix-downloader-py.git
cd idlix-downloader-py
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r backend/requirements-api.txt
```

2. **Build backend:**
```bash
pyinstaller --clean idlix_windows_api.spec
```

3. **Setup Electron:**
```bash
cd electron-app
npm install
```

4. **Run in development:**
```bash
# Terminal 1: Backend already built (./dist/idlix-downloader)
# Terminal 2: Electron
cd electron-app
npm start
```

## 🧪 Testing

### Test Backend API
```bash
# Start backend
./dist/idlix-downloader --api-server --port 8000

# Test in another terminal
curl http://localhost:8000/api/health
```

### Test Electron App
```bash
cd electron-app
npm start
```

## 🏗️ Building

### Backend (PyInstaller)
```bash
pyinstaller --clean idlix_windows_api.spec
# Output: dist/idlix-downloader (Linux/macOS) or dist/idlix-downloader.exe (Windows)
```

### Electron Apps
```bash
cd electron-app
npm run build:linux    # .AppImage + .deb
npm run build:win      # .exe installer
npm run build:mac      # .dmg
```

## 📝 Code Style

### Python
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings for functions
- Use async/await for I/O operations

### JavaScript
- Use modern ES6+ syntax
- Use async/await instead of callbacks
- Add JSDoc comments for complex functions
- Use meaningful variable names

### File Organization
- Backend code in `backend/`
- Core downloader logic in `idlix.py`
- Electron code in `electron-app/src/`
- Documentation in `docs/`

## 🔀 Git Workflow

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes and commit:**
```bash
git add .
git commit -m "feat: add amazing feature"
```

3. **Push and create PR:**
```bash
git push origin feature/your-feature-name
```

### Commit Message Format
```
<type>: <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build/tooling changes

## 🐛 Reporting Issues

When reporting issues, please include:

1. **Environment:**
   - OS and version
   - Python version
   - Node.js version
   - FFmpeg version

2. **Steps to reproduce:**
   - Clear step-by-step instructions
   - Expected vs actual behavior

3. **Logs:**
   - Backend terminal output
   - Electron developer console logs
   - Error messages

## 🔐 Security

If you discover a security vulnerability, please email directly instead of opening a public issue.

## 📄 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## 🙏 Questions?

Feel free to open a discussion or issue on GitHub!
