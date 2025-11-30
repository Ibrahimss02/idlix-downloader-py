const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const Store = require('electron-store');

const store = new Store();

let mainWindow;
let backendProcess;
let backendPort;
let backendReady = false;

// Get backend executable path
function getBackendPath() {
  if (app.isPackaged) {
    // Production: backend is in resources/backend/
    const ext = process.platform === 'win32' ? '.exe' : '';
    return path.join(process.resourcesPath, 'backend', `idlix-downloader${ext}`);
  } else {
    // Development: use the built executable from parent directory
    const ext = process.platform === 'win32' ? '.exe' : '';
    return path.join(__dirname, '..', '..', '..', 'dist', `idlix-downloader${ext}`);
  }
}

// Start Python backend server
function startBackend() {
  return new Promise((resolve, reject) => {
    const backendPath = getBackendPath();
    
    console.log('Starting backend:', backendPath);
    
    // Spawn backend process with --api-server flag
    backendProcess = spawn(backendPath, ['--api-server', '--port', '0'], {
      stdio: ['ignore', 'pipe', 'pipe']
    });
    
    // Buffer to accumulate stdout data
    let stdoutBuffer = '';
    
    // Parse stdout for port info
    backendProcess.stdout.on('data', (data) => {
      const output = data.toString();
      stdoutBuffer += output;
      
      // Log each line
      const lines = output.split('\n');
      lines.forEach(line => {
        if (line.trim()) {
          console.log('Backend stdout:', line.trim());
        }
      });
      
      // Try to find JSON in the buffer
      const jsonMatch = stdoutBuffer.match(/\{[^}]*"status"[^}]*\}/);
      if (jsonMatch) {
        try {
          const json = JSON.parse(jsonMatch[0]);
          if (json.status === 'ready' && json.port) {
            backendPort = json.port;
            backendReady = true;
            console.log(`Backend ready on port ${backendPort}`);
            resolve(backendPort);
          } else if (json.status === 'error') {
            reject(new Error(json.message));
          }
        } catch (e) {
          // JSON parsing failed, continue waiting
        }
      }
    });
    
    backendProcess.stderr.on('data', (data) => {
      console.error('Backend stderr:', data.toString());
    });
    
    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
      backendReady = false;
      if (!backendReady) {
        reject(new Error(`Backend process exited with code ${code}`));
      }
    });
    
    backendProcess.on('error', (err) => {
      console.error('Failed to start backend:', err);
      reject(err);
    });
    
    // Timeout after 10 seconds
    setTimeout(() => {
      if (!backendReady) {
        reject(new Error('Backend startup timeout'));
      }
    }, 10000);
  });
}

// Stop backend server
function stopBackend() {
  if (backendProcess) {
    console.log('Stopping backend...');
    backendProcess.kill();
    backendProcess = null;
  }
}

// Create main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    autoHideMenuBar: true,
    icon: path.join(__dirname, '..', '..', 'assets', 'icon.png')
  });
  
  // Load the app
  mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));
  
  // Open DevTools in development
  if (!app.isPackaged) {
    mainWindow.webContents.openDevTools();
  }
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(async () => {
  try {
    // Start backend first
    await startBackend();
    
    // Create window after backend is ready
    createWindow();
    
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  } catch (error) {
    console.error('Failed to start app:', error);
    dialog.showErrorBox('Startup Error', `Failed to start backend: ${error.message}`);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

// IPC Handlers

// Get backend URL
ipcMain.handle('get-backend-url', () => {
  if (backendReady && backendPort) {
    return `http://127.0.0.1:${backendPort}`;
  }
  return null;
});

// Select download directory
ipcMain.handle('select-download-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory', 'createDirectory'],
    title: 'Select Download Directory',
    defaultPath: store.get('downloadPath', app.getPath('downloads'))
  });
  
  if (!result.canceled && result.filePaths.length > 0) {
    const selectedPath = result.filePaths[0];
    store.set('downloadPath', selectedPath);
    return selectedPath;
  }
  
  return null;
});

// Get saved download path
ipcMain.handle('get-download-path', () => {
  return store.get('downloadPath', app.getPath('downloads'));
});

// Set download path
ipcMain.handle('set-download-path', (event, path) => {
  store.set('downloadPath', path);
  return path;
});

// Get all settings
ipcMain.handle('get-settings', () => {
  return {
    downloadPath: store.get('downloadPath', app.getPath('downloads')),
    defaultQuality: store.get('defaultQuality', 'highest'),
    downloadThreads: store.get('downloadThreads', 16),
    theme: store.get('theme', 'system')
  };
});

// Update settings
ipcMain.handle('update-settings', (event, settings) => {
  Object.keys(settings).forEach(key => {
    store.set(key, settings[key]);
  });
  return true;
});

// Open file in system default app
ipcMain.handle('open-file', async (event, filePath) => {
  const { shell } = require('electron');
  await shell.openPath(filePath);
});

// Show file in folder
ipcMain.handle('show-in-folder', (event, filePath) => {
  const { shell } = require('electron');
  shell.showItemInFolder(filePath);
});
