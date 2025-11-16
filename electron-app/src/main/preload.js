const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // Backend communication
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  
  // File system operations
  selectDownloadDirectory: () => ipcRenderer.invoke('select-download-directory'),
  getDownloadPath: () => ipcRenderer.invoke('get-download-path'),
  setDownloadPath: (path) => ipcRenderer.invoke('set-download-path', path),
  openFile: (path) => ipcRenderer.invoke('open-file', path),
  showInFolder: (path) => ipcRenderer.invoke('show-in-folder', path),
  
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  updateSettings: (settings) => ipcRenderer.invoke('update-settings', settings),
  
  // Platform info
  platform: process.platform
});
