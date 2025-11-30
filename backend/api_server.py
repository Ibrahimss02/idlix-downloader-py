#!/usr/bin/env python3
"""
FastAPI REST API Server for IDLIX Downloader
Provides HTTP endpoints for Electron frontend integration
"""

import os
import sys
import uuid
import json
import asyncio
import hashlib
import threading
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directory to path to import idlix module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idlix import IDLIXDownloader, extract_base_url
from backend.database import (
    init_database, create_job, update_job, get_job, save_variants, get_variants,
    create_download, update_download, get_download, get_all_downloads, 
    get_downloads_by_job, mark_interrupted_downloads, delete_download,
    get_setting, set_setting
)


# Global state for active downloads
active_downloads: Dict[str, Dict[str, Any]] = {}
download_threads: Dict[str, threading.Thread] = {}
download_locks = {}


# Pydantic models for request/response
class ExtractRequest(BaseModel):
    movie_url: str = Field(..., description="IDLIX movie page URL")


class ExtractResponse(BaseModel):
    job_id: str
    video_title: str
    embed_url: str
    status: str


class VariantResponse(BaseModel):
    quality: str
    label: str
    url: str
    bandwidth: int
    resolution: Optional[list]


class DownloadRequest(BaseModel):
    job_id: str
    quality: str
    output_path: str
    filename: Optional[str] = None
    threads: int = Field(16, ge=1, le=32)
    download_subtitle: bool = Field(False, description="Download subtitle if available")


class DownloadResponse(BaseModel):
    download_id: str
    status: str
    message: str


class ProgressResponse(BaseModel):
    download_id: str
    status: str
    percent: float = 0.0
    downloaded_segments: int = 0
    total_segments: int = 0
    speed_mbps: float = 0.0
    speed_segments: float = 0.0
    eta_seconds: int = 0
    bytes_downloaded: int = 0
    file_size: int = 0
    errors: list = []
    output_path: Optional[str] = None
    filename: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    movie_url: str
    video_title: Optional[str]
    status: str
    created_at: str


class DownloadListItem(BaseModel):
    download_id: str
    job_id: str
    quality: str
    filename: str
    status: str
    progress: Optional[dict]
    created_at: str


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()
    await mark_interrupted_downloads()
    print("✓ API Server initialized")
    yield
    # Shutdown
    print("✓ API Server shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="IDLIX Downloader API",
    version="1.0.0",
    description="REST API for IDLIX video downloading",
    lifespan=lifespan
)

# CORS middleware - allow localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "IDLIX Downloader API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "extract": "POST /api/extract",
            "variants": "GET /api/variants/{job_id}",
            "download": "POST /api/download",
            "progress": "GET /api/progress/{download_id}",
            "resume": "POST /api/resume/{download_id}",
            "cancel": "DELETE /api/cancel/{download_id}",
            "jobs": "GET /api/jobs",
            "downloads": "GET /api/downloads"
        }
    }


@app.post("/api/extract", response_model=ExtractResponse)
async def extract_video_info(request: ExtractRequest):
    """Extract video information from IDLIX URL"""
    try:
        job_id = str(uuid.uuid4())
        base_url = extract_base_url(request.movie_url)
        
        # Create job in database
        await create_job(job_id, request.movie_url, base_url)
        
        # Extract embed URL in thread pool
        downloader = IDLIXDownloader(base_url)
        embed_url, video_title = await asyncio.to_thread(
            downloader.extract_embed_url,
            request.movie_url
        )
        
        # Update job with extracted info
        await update_job(job_id, 
                        video_title=video_title,
                        embed_url=embed_url,
                        status='extracted')
        
        # Get M3U8 variants
        variants = await asyncio.to_thread(downloader.get_m3u8_info, embed_url)
        
        # Save variants to database
        await save_variants(job_id, variants)
        await update_job(job_id, status='ready')
        
        return ExtractResponse(
            job_id=job_id,
            video_title=video_title,
            embed_url=embed_url,
            status='ready'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/variants/{job_id}")
async def get_video_variants(job_id: str):
    """Get available quality variants for a job"""
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    variants = await get_variants(job_id)
    if not variants:
        raise HTTPException(status_code=404, detail="No variants found for this job")
    
    return {
        "job_id": job_id,
        "video_title": job.get('video_title'),
        "variants": variants
    }


@app.get("/api/subtitle/{job_id}")
async def get_subtitle(job_id: str):
    """Get subtitle information for a job"""
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    embed_url = job.get('embed_url')
    if not embed_url:
        raise HTTPException(status_code=400, detail="No embed URL found for this job")
    
    # Get subtitle info (URL only, don't download yet)
    base_url = job.get('base_url')
    downloader = IDLIXDownloader(base_url)
    
    subtitle_info = await asyncio.to_thread(
        downloader.get_subtitle,
        embed_url,
        job.get('video_title', 'video'),
        download=False
    )
    
    return {
        "job_id": job_id,
        "available": subtitle_info['status'],
        "subtitle_url": subtitle_info.get('subtitle') if subtitle_info['status'] else None,
        "message": subtitle_info.get('message', '')
    }


@app.post("/api/download", response_model=DownloadResponse)
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Start a new download"""
    try:
        # Validate job exists
        job = await get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get variants and find matching quality
        variants = await get_variants(request.job_id)
        selected_variant = None
        for variant in variants:
            if request.quality.lower() in variant['quality'].lower():
                selected_variant = variant
                break
        
        if not selected_variant:
            raise HTTPException(status_code=400, detail=f"Quality '{request.quality}' not found")
        
        # Generate download ID and paths
        download_id = str(uuid.uuid4())
        
        # Determine filename
        if request.filename:
            filename = request.filename if request.filename.endswith('.mp4') else f"{request.filename}.mp4"
        else:
            import re
            safe_title = re.sub(r'[<>:"/\\|?*]', '', job.get('video_title', 'video'))
            filename = f"{safe_title}.mp4"
        
        # Validate output directory
        output_dir = os.path.abspath(request.output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Cannot create output directory: {e}")
        
        output_path = os.path.join(output_dir, filename)
        
        # Generate cache directory
        content_hash = hashlib.md5(selected_variant['url'].encode()).hexdigest()[:16]
        cache_base = os.path.expanduser("~/.cache/idlix-downloader")
        cache_dir = os.path.join(cache_base, content_hash)
        
        # Create download entry in database
        await create_download(
            download_id=download_id,
            job_id=request.job_id,
            quality=request.quality,
            output_path=output_dir,
            filename=filename,
            stream_url=selected_variant['url'],
            cache_dir=cache_dir
        )
        
        # Initialize progress tracking
        active_downloads[download_id] = {
            'status': 'starting',
            'percent': 0.0,
            'downloaded_segments': 0,
            'total_segments': 0,
            'speed_mbps': 0.0,
            'speed_segments': 0.0,
            'eta_seconds': 0,
            'bytes_downloaded': 0,
            'errors': [],
            'output_path': output_path,
            'filename': filename
        }
        
        # Start download in background
        background_tasks.add_task(
            run_download_task,
            download_id,
            job.get('base_url'),
            job.get('embed_url'),
            job.get('video_title'),
            selected_variant['url'],
            output_path,
            output_dir,
            request.threads,
            request.download_subtitle
        )
        
        return DownloadResponse(
            download_id=download_id,
            status='starting',
            message=f"Download started: {filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_download_task(download_id: str, base_url: str, embed_url: str,
                            video_title: str, stream_url: str, output_path: str,
                            output_dir: str, threads: int, download_subtitle: bool = False):
    """Run download task in background"""
    try:
        await update_download(download_id, status='downloading')
        
        # Download subtitle if requested
        subtitle_path = None
        if download_subtitle:
            try:
                downloader = IDLIXDownloader(base_url)
                subtitle_result = await asyncio.to_thread(
                    downloader.get_subtitle,
                    embed_url,
                    video_title,
                    download=True
                )
                
                if subtitle_result['status'] and subtitle_result.get('subtitle'):
                    # Move subtitle to output directory
                    import shutil
                    subtitle_file = subtitle_result['subtitle']
                    if os.path.exists(subtitle_file):
                        subtitle_dest = os.path.join(output_dir, os.path.basename(subtitle_file))
                        if subtitle_file != subtitle_dest:
                            shutil.move(subtitle_file, subtitle_dest)
                            subtitle_path = subtitle_dest
                        else:
                            subtitle_path = subtitle_file
                        print(f"✓ Subtitle downloaded: {subtitle_path}")
            except Exception as e:
                print(f"Warning: Subtitle download failed: {e}")
        
        # Create progress callback - using time.time() instead of event loop time
        last_db_update = [0]  # Mutable container for closure
        loop = asyncio.get_event_loop()
        
        def progress_callback(progress_dict):
            # Check for cancellation from API
            if active_downloads[download_id].get('cancelled', False):
                progress_dict['cancelled'] = True
            
            # Update in-memory progress (thread-safe for dict updates)
            active_downloads[download_id].update(progress_dict)
            
            # Update database every 5 seconds or on status change
            import time
            current_time = time.time()
            if (current_time - last_db_update[0] > 5.0 or 
                progress_dict.get('status') in ['completed', 'failed', 'merging']):
                
                last_db_update[0] = current_time
                
                # Schedule database update in a thread-safe manner
                try:
                    asyncio.run_coroutine_threadsafe(
                        update_download(
                            download_id,
                            status=progress_dict.get('status', 'downloading'),
                            downloaded_segments=progress_dict.get('downloaded_segments', 0),
                            total_segments=progress_dict.get('total_segments', 0),
                            failed_segments=progress_dict.get('failed_segments', 0),
                            bytes_downloaded=progress_dict.get('bytes_downloaded', 0),
                            progress_json=json.dumps(progress_dict)
                        ),
                        loop
                    )
                except Exception as e:
                    # Log error but don't stop download
                    print(f"Warning: Failed to update progress in DB: {e}")
        
        # Run download in thread pool
        downloader = IDLIXDownloader(base_url)
        success = await asyncio.to_thread(
            downloader.download_video,
            stream_url,
            output_path,
            threads,
            progress_callback
        )
        
        # Update final status
        final_status = 'completed' if success else 'failed'
        active_downloads[download_id]['status'] = final_status
        
        # Extract error message from progress if failed
        error_message = None
        if not success and active_downloads[download_id].get('errors'):
            error_message = '\n'.join(active_downloads[download_id]['errors'])
            # Log error to stderr for debugging
            import sys
            print(f"Download {download_id} failed: {error_message}", file=sys.stderr)
        
        await update_download(
            download_id,
            status=final_status,
            error_message=error_message,
            progress_json=json.dumps(active_downloads[download_id])
        )
        
        if success:
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            await update_download(download_id, file_size=file_size)
        
    except Exception as e:
        active_downloads[download_id]['status'] = 'failed'
        active_downloads[download_id]['errors'].append(str(e))
        await update_download(
            download_id,
            status='failed',
            error_message=str(e),
            progress_json=json.dumps(active_downloads[download_id])
        )


@app.get("/api/progress/{download_id}", response_model=ProgressResponse)
async def get_download_progress(download_id: str):
    """Get real-time download progress"""
    # Check in-memory first (for active downloads)
    if download_id in active_downloads:
        progress = active_downloads[download_id]
        return ProgressResponse(
            download_id=download_id,
            status=progress.get('status', 'unknown'),
            percent=progress.get('percent', 0.0),
            downloaded_segments=progress.get('downloaded_segments', 0),
            total_segments=progress.get('total_segments', 0),
            speed_mbps=progress.get('speed_mbps', 0.0),
            speed_segments=progress.get('speed_segments', 0.0),
            eta_seconds=progress.get('eta_seconds', 0),
            bytes_downloaded=progress.get('bytes_downloaded', 0),
            file_size=progress.get('file_size', 0),
            errors=progress.get('errors', []),
            output_path=progress.get('output_path'),
            filename=progress.get('filename')
        )
    
    # Otherwise check database
    download = await get_download(download_id)
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    progress = download.get('progress', {})
    return ProgressResponse(
        download_id=download_id,
        status=download.get('status', 'unknown'),
        percent=progress.get('percent', 0.0),
        downloaded_segments=download.get('downloaded_segments', 0),
        total_segments=download.get('total_segments', 0),
        speed_mbps=progress.get('speed_mbps', 0.0),
        speed_segments=progress.get('speed_segments', 0.0),
        eta_seconds=progress.get('eta_seconds', 0),
        bytes_downloaded=download.get('bytes_downloaded', 0),
        file_size=download.get('file_size', 0),
        errors=progress.get('errors', []),
        output_path=os.path.join(download.get('output_path', ''), download.get('filename', '')),
        filename=download.get('filename')
    )


@app.post("/api/resume/{download_id}")
async def resume_download(download_id: str, background_tasks: BackgroundTasks):
    """Resume an interrupted download"""
    download = await get_download(download_id)
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    if download['status'] not in ['interrupted', 'failed']:
        raise HTTPException(status_code=400, detail="Download is not in resumable state")
    
    # Validate cache directory exists and has segments
    cache_dir = download.get('cache_dir')
    if not cache_dir or not os.path.exists(cache_dir):
        raise HTTPException(status_code=400, detail="Cache directory not found, cannot resume. Please start a new download.")
    
    # Count cached segments
    import glob
    cached_segments = glob.glob(os.path.join(cache_dir, "segment_*.ts"))
    if len(cached_segments) == 0:
        raise HTTPException(status_code=400, detail="No cached segments found, cannot resume. Please start a new download.")
    
    # Get job info
    job = await get_job(download['job_id'])
    if not job:
        raise HTTPException(status_code=404, detail="Parent job not found")
    
    # Reset progress and restart download
    output_path = os.path.join(download['output_path'], download['filename'])
    
    # Restore progress from database if available
    restored_progress = {}
    if download.get('progress'):
        try:
            restored_progress = json.loads(download['progress']) if isinstance(download['progress'], str) else download['progress']
        except:
            pass
    
    active_downloads[download_id] = {
        'status': 'resuming',
        'percent': restored_progress.get('percent', 0.0),
        'downloaded_segments': restored_progress.get('downloaded_segments', len(cached_segments)),
        'total_segments': restored_progress.get('total_segments', 0),
        'speed_mbps': 0.0,
        'speed_segments': 0.0,
        'eta_seconds': 0,
        'bytes_downloaded': restored_progress.get('bytes_downloaded', 0),
        'errors': [],
        'output_path': output_path,
        'filename': download['filename']
    }
    
    await update_download(download_id, status='resuming')
    
    # Start download in background (no subtitle on resume)
    background_tasks.add_task(
        run_download_task,
        download_id,
        job['base_url'],
        job.get('embed_url', ''),
        job.get('video_title', 'video'),
        download['stream_url'],
        output_path,
        download['output_path'],
        16,  # Default threads for resume
        False  # Don't re-download subtitle on resume
    )
    
    return {"message": "Download resumed", "download_id": download_id}


@app.delete("/api/cancel/{download_id}")
async def cancel_download(download_id: str):
    """Cancel an active download"""
    if download_id not in active_downloads:
        raise HTTPException(status_code=404, detail="Active download not found")
    
    # Mark as cancelled (the download thread will check this)
    active_downloads[download_id]['cancelled'] = True
    active_downloads[download_id]['status'] = 'cancelled'
    
    await update_download(download_id, status='cancelled')
    
    return {"message": "Download cancelled", "download_id": download_id}


@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    """List all extraction jobs"""
    # This would need a new database function to get all jobs
    # For now, return a simple message
    return {"message": "Jobs listing endpoint - to be implemented"}


@app.get("/api/downloads")
async def list_downloads(status: Optional[str] = None):
    """List all downloads"""
    downloads = await get_all_downloads(status)
    
    return {
        "downloads": [
            DownloadListItem(
                download_id=d['download_id'],
                job_id=d['job_id'],
                quality=d['quality'],
                filename=d['filename'],
                status=d['status'],
                progress=d.get('progress'),
                created_at=d['created_at']
            )
            for d in downloads
        ],
        "total": len(downloads)
    }


@app.delete("/api/downloads/{download_id}")
async def delete_download_record(download_id: str):
    """Delete a download record from database"""
    download = await get_download(download_id)
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    await delete_download(download_id)
    
    # Clean up from active downloads if present
    if download_id in active_downloads:
        del active_downloads[download_id]
    
    return {"message": "Download record deleted", "download_id": download_id}


@app.get("/api/settings/{key}")
async def get_setting_value(key: str):
    """Get a setting value"""
    value = await get_setting(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"key": key, "value": value}


@app.post("/api/settings/{key}")
async def set_setting_value(key: str, value: str):
    """Set a setting value"""
    await set_setting(key, value)
    return {"key": key, "value": value}


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="info"
    )
