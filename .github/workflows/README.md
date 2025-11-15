# GitHub Actions Workflows

## Automated Builds

This repository uses GitHub Actions to automatically build executables for Windows and Linux.

### 🚀 Build Triggers

The workflow runs automatically on:
- ✅ **Push to main/master** - Builds and uploads artifacts
- ✅ **Pull requests** - Tests builds before merging
- ✅ **Tag creation** (`v*`) - Creates GitHub release
- ✅ **Manual trigger** - Run from Actions tab

### 📦 Build Jobs

#### 1. Windows Build (`build-windows`)
- Runs on: `windows-latest`
- Python: 3.10
- Output: `dist/idlix-downloader.exe`
- Artifact: `idlix-downloader-windows`

#### 2. Linux Build (`build-linux`)
- Runs on: `ubuntu-latest`
- Python: 3.10
- Output: `dist/idlix-downloader`
- Artifact: `idlix-downloader-linux`

#### 3. Release Creation (`create-release`)
- Only runs on tag push (`v1.0.0`, `v2.1.3`, etc.)
- Downloads both Windows & Linux builds
- Creates GitHub Release with both executables

### 📥 Downloading Builds

#### From Workflow Run:
1. Go to **Actions** tab
2. Click on workflow run
3. Download artifacts from bottom of page

#### From Release (tagged builds only):
1. Go to **Releases** page
2. Download `idlix-downloader.exe` (Windows)
3. Download `idlix-downloader` (Linux)

### 🏷️ Creating a Release

To trigger automatic release creation:

```bash
# Tag your commit
git tag v1.0.0
git push origin v1.0.0
```

This will:
1. Build Windows executable
2. Build Linux executable
3. Create GitHub Release
4. Attach both executables to release
5. Generate release notes automatically

### 🔧 Manual Trigger

1. Go to **Actions** tab
2. Select "Build Executables"
3. Click **Run workflow**
4. Choose branch
5. Click **Run workflow** button

### 📋 Build Process

**Windows:**
```
Install Python 3.10
↓
Install dependencies (curl-cffi, beautifulsoup4, etc.)
↓
Download FFmpeg binary
↓
Generate PyInstaller spec
↓
Build with PyInstaller
↓
Upload artifact (30 days retention)
```

**Linux:**
```
Install Python 3.10
↓
Install dependencies
↓
Download FFmpeg static binary
↓
Run build_executable.sh
↓
Upload artifact (30 days retention)
```

### ⚙️ Configuration

Edit `.github/workflows/build.yml` to:
- Change Python version
- Add/remove dependencies
- Modify retention days
- Add macOS builds
- Customize release settings

### 🐛 Troubleshooting

**Build fails:**
- Check Actions logs for errors
- Verify all files are committed (hooks/, crypto_helper.py, etc.)
- Ensure dependencies are correct

**Release not created:**
- Make sure tag starts with `v` (e.g., `v1.0.0`)
- Check GITHUB_TOKEN permissions
- Verify workflow completed successfully

**Missing artifacts:**
- Check if job succeeded (green checkmark)
- Artifacts expire after 30 days
- Re-run workflow if needed

### 🎯 Best Practices

1. **Test locally first** - Run build scripts before pushing
2. **Use semantic versioning** - `v1.0.0`, `v1.1.0`, `v2.0.0`
3. **Write release notes** - Auto-generated but can be edited
4. **Check artifacts** - Download and test before releasing

### 📊 Workflow Status

Add badge to README.md:

```markdown
[![Build](https://github.com/Ibrahimss02/idlix-downloader-py/actions/workflows/build.yml/badge.svg)](https://github.com/Ibrahimss02/idlix-downloader-py/actions/workflows/build.yml)
```
