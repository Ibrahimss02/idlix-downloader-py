// App state
let backendUrl = null;
let currentJobId = null;
let selectedQuality = null;
let activeDownloads = new Map();
let pollingIntervals = new Map();

// Initialize app
async function init() {
  try {
    // Get backend URL
    backendUrl = await window.electronAPI.getBackendUrl();
    if (!backendUrl) {
      showError('Backend not ready. Please restart the application.');
      return;
    }
    
    console.log('Backend URL:', backendUrl);
    
    // Load download path
    const downloadPath = await window.electronAPI.getDownloadPath();
    document.getElementById('downloadPath').value = downloadPath;
    
    // Set up event listeners
    setupEventListeners();
    
    // Load existing downloads
    await loadExistingDownloads();
    
  } catch (error) {
    console.error('Initialization error:', error);
    showError('Failed to initialize app: ' + error.message);
  }
}

// Setup event listeners
function setupEventListeners() {
  document.getElementById('extractBtn').addEventListener('click', handleExtract);
  document.getElementById('videoUrl').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleExtract();
  });
  
  document.getElementById('browseBtn').addEventListener('click', async () => {
    const path = await window.electronAPI.selectDownloadDirectory();
    if (path) {
      document.getElementById('downloadPath').value = path;
    }
  });
  
  document.getElementById('downloadBtn').addEventListener('click', handleDownload);
}

// Show error message
function showError(message) {
  const statusEl = document.getElementById('extractStatus');
  statusEl.textContent = message;
  statusEl.className = 'status-message error';
  statusEl.style.display = 'block';
}

// Show success message
function showSuccess(message) {
  const statusEl = document.getElementById('extractStatus');
  statusEl.textContent = message;
  statusEl.className = 'status-message success';
  statusEl.style.display = 'block';
}

// Show loading message
function showLoading(message) {
  const statusEl = document.getElementById('extractStatus');
  statusEl.textContent = message;
  statusEl.className = 'status-message loading';
  statusEl.style.display = 'block';
}

// Handle video URL extraction
async function handleExtract() {
  const urlInput = document.getElementById('videoUrl');
  const movieUrl = urlInput.value.trim();
  
  if (!movieUrl) {
    showError('Please enter a video URL');
    return;
  }
  
  const extractBtn = document.getElementById('extractBtn');
  extractBtn.disabled = true;
  extractBtn.textContent = 'Extracting...';
  
  showLoading('Extracting video information...');
  
  try {
    const response = await fetch(`${backendUrl}/api/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ movie_url: movieUrl })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Extraction failed');
    }
    
    const data = await response.json();
    currentJobId = data.job_id;
    
    showSuccess(`Video found: ${data.video_title}`);
    
    // Load variants
    await loadVariants(data.job_id, data.video_title);
    
  } catch (error) {
    console.error('Extraction error:', error);
    showError('Extraction failed: ' + error.message);
  } finally {
    extractBtn.disabled = false;
    extractBtn.textContent = 'Extract';
  }
}

// Load quality variants
async function loadVariants(jobId, videoTitle) {
  try {
    const response = await fetch(`${backendUrl}/api/variants/${jobId}`);
    if (!response.ok) {
      throw new Error('Failed to load quality options');
    }
    
    const data = await response.json();
    
    // Show quality section
    const qualitySection = document.getElementById('qualitySection');
    qualitySection.style.display = 'block';
    
    // Display video info
    const videoInfo = document.getElementById('videoInfo');
    videoInfo.innerHTML = `<strong>${data.video_title}</strong>`;
    
    // Display quality options
    const qualityOptions = document.getElementById('qualityOptions');
    qualityOptions.innerHTML = '';
    
    data.variants.forEach((variant, index) => {
      const card = document.createElement('div');
      card.className = 'quality-card';
      card.innerHTML = `
        <div class="quality-label">${variant.quality}</div>
        <div class="quality-detail">${variant.label}</div>
      `;
      card.addEventListener('click', () => selectQuality(variant, card));
      qualityOptions.appendChild(card);
      
      // Auto-select first (highest) quality
      if (index === 0) {
        selectQuality(variant, card);
      }
    });
    
    // Scroll to quality section
    qualitySection.scrollIntoView({ behavior: 'smooth' });
    
  } catch (error) {
    console.error('Load variants error:', error);
    showError('Failed to load quality options: ' + error.message);
  }
}

// Select quality
function selectQuality(variant, cardElement) {
  // Remove previous selection
  document.querySelectorAll('.quality-card').forEach(card => {
    card.classList.remove('selected');
  });
  
  // Add selection to clicked card
  cardElement.classList.add('selected');
  
  selectedQuality = variant;
  document.getElementById('downloadBtn').disabled = false;
}

// Handle download start
async function handleDownload() {
  if (!currentJobId || !selectedQuality) {
    showError('Please select a quality first');
    return;
  }
  
  const downloadPath = document.getElementById('downloadPath').value;
  const customFilename = document.getElementById('customFilename').value.trim();
  
  const downloadBtn = document.getElementById('downloadBtn');
  downloadBtn.disabled = true;
  downloadBtn.textContent = 'Starting...';
  
  try {
    const response = await fetch(`${backendUrl}/api/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: currentJobId,
        quality: selectedQuality.quality,
        output_path: downloadPath,
        filename: customFilename || null,
        threads: 16
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Download start failed');
    }
    
    const data = await response.json();
    
    showSuccess('Download started!');
    
    // Add to downloads list
    addDownloadToList(data.download_id, selectedQuality.quality);
    
    // Start polling for progress
    startProgressPolling(data.download_id);
    
    // Reset form
    document.getElementById('videoUrl').value = '';
    document.getElementById('customFilename').value = '';
    document.getElementById('qualitySection').style.display = 'none';
    currentJobId = null;
    selectedQuality = null;
    
  } catch (error) {
    console.error('Download start error:', error);
    showError('Failed to start download: ' + error.message);
  } finally {
    downloadBtn.disabled = false;
    downloadBtn.textContent = 'Start Download';
  }
}

// Add download to list
function addDownloadToList(downloadId, quality) {
  const downloadsList = document.getElementById('downloadsList');
  
  // Remove empty state
  const emptyState = downloadsList.querySelector('.empty-state');
  if (emptyState) {
    emptyState.remove();
  }
  
  const downloadItem = document.createElement('div');
  downloadItem.className = 'download-item';
  downloadItem.id = `download-${downloadId}`;
  downloadItem.innerHTML = `
    <div class="download-header">
      <span class="download-quality">${quality}</span>
      <span class="download-status">Starting...</span>
    </div>
    <div class="download-filename">Loading...</div>
    <div class="progress-bar">
      <div class="progress-fill" style="width: 0%"></div>
    </div>
    <div class="download-stats">
      <span class="stat">0%</span>
      <span class="stat">0 / 0 segments</span>
      <span class="stat">0.00 MB/s</span>
      <span class="stat">ETA: --</span>
    </div>
    <div class="download-actions">
      <button class="btn-icon btn-cancel" title="Cancel" data-id="${downloadId}">❌</button>
    </div>
  `;
  
  downloadsList.insertBefore(downloadItem, downloadsList.firstChild);
  
  // Add cancel handler
  downloadItem.querySelector('.btn-cancel').addEventListener('click', () => {
    cancelDownload(downloadId);
  });
}

// Start progress polling
function startProgressPolling(downloadId) {
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`${backendUrl}/api/progress/${downloadId}`);
      if (!response.ok) {
        console.warn('Failed to fetch progress');
        return;
      }
      
      const progress = await response.json();
      updateDownloadProgress(downloadId, progress);
      
      // Stop polling if completed or failed
      if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'cancelled') {
        clearInterval(interval);
        pollingIntervals.delete(downloadId);
      }
      
    } catch (error) {
      console.error('Progress polling error:', error);
    }
  }, 500);
  
  pollingIntervals.set(downloadId, interval);
}

// Update download progress
function updateDownloadProgress(downloadId, progress) {
  const downloadItem = document.getElementById(`download-${downloadId}`);
  if (!downloadItem) return;
  
  // Update status
  const statusEl = downloadItem.querySelector('.download-status');
  statusEl.textContent = progress.status.charAt(0).toUpperCase() + progress.status.slice(1);
  statusEl.className = `download-status status-${progress.status}`;
  
  // Update filename
  if (progress.filename) {
    downloadItem.querySelector('.download-filename').textContent = progress.filename;
  }
  
  // Update progress bar
  const progressFill = downloadItem.querySelector('.progress-fill');
  progressFill.style.width = `${progress.percent}%`;
  
  // Update stats
  const stats = downloadItem.querySelectorAll('.download-stats .stat');
  stats[0].textContent = `${progress.percent.toFixed(1)}%`;
  stats[1].textContent = `${progress.downloaded_segments} / ${progress.total_segments} segments`;
  stats[2].textContent = `${progress.speed_mbps.toFixed(2)} MB/s`;
  stats[3].textContent = progress.eta_seconds > 0 ? `ETA: ${formatTime(progress.eta_seconds)}` : 'ETA: --';
  
  // Update actions based on status
  const actionsEl = downloadItem.querySelector('.download-actions');
  if (progress.status === 'completed') {
    actionsEl.innerHTML = `
      <button class="btn-icon btn-open" title="Open File" data-path="${progress.output_path}">📂</button>
      <button class="btn-icon btn-folder" title="Show in Folder" data-path="${progress.output_path}">📁</button>
    `;
    
    // Add event listeners
    actionsEl.querySelector('.btn-open').addEventListener('click', function() {
      window.electronAPI.openFile(this.dataset.path);
    });
    actionsEl.querySelector('.btn-folder').addEventListener('click', function() {
      window.electronAPI.showInFolder(this.dataset.path);
    });
  } else if (progress.status === 'failed') {
    actionsEl.innerHTML = `
      <button class="btn-icon btn-retry" title="Retry" data-id="${downloadId}">🔄</button>
      <button class="btn-icon btn-remove" title="Remove" data-id="${downloadId}">🗑️</button>
    `;
    
    // Add event listeners
    actionsEl.querySelector('.btn-retry').addEventListener('click', function() {
      retryDownload(this.dataset.id);
    });
    actionsEl.querySelector('.btn-remove').addEventListener('click', function() {
      removeDownload(this.dataset.id);
    });
  }
}

// Cancel download
async function cancelDownload(downloadId) {
  try {
    await fetch(`${backendUrl}/api/cancel/${downloadId}`, { method: 'DELETE' });
    console.log('Download cancelled:', downloadId);
  } catch (error) {
    console.error('Cancel error:', error);
  }
}

// Retry download
async function retryDownload(downloadId) {
  try {
    const response = await fetch(`${backendUrl}/api/resume/${downloadId}`, { method: 'POST' });
    if (response.ok) {
      console.log('Download resumed:', downloadId);
      startProgressPolling(downloadId);
    }
  } catch (error) {
    console.error('Retry error:', error);
  }
}

// Remove download from list
function removeDownload(downloadId) {
  const downloadItem = document.getElementById(`download-${downloadId}`);
  if (downloadItem) {
    downloadItem.remove();
  }
  
  // Show empty state if no downloads
  const downloadsList = document.getElementById('downloadsList');
  if (downloadsList.children.length === 0) {
    downloadsList.innerHTML = '<p class="empty-state">No active downloads</p>';
  }
}

// Load existing downloads
async function loadExistingDownloads() {
  try {
    const response = await fetch(`${backendUrl}/api/downloads`);
    if (!response.ok) return;
    
    const data = await response.json();
    
    // Load incomplete downloads
    data.downloads.filter(d => 
      d.status !== 'completed' && d.status !== 'cancelled'
    ).forEach(download => {
      addDownloadToList(download.download_id, download.quality);
      startProgressPolling(download.download_id);
    });
    
  } catch (error) {
    console.error('Load downloads error:', error);
  }
}

// Format time (seconds to MM:SS)
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
