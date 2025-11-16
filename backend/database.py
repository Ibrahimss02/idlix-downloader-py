#!/usr/bin/env python3
"""
SQLite Database Module for IDLIX Downloader API
Handles job persistence, download state, and resume capabilities
"""

import os
import json
import aiosqlite
from datetime import datetime
from pathlib import Path


def get_database_path():
    """Get database file path in user data directory"""
    if os.name == 'nt':  # Windows
        base_dir = os.path.join(os.environ['APPDATA'], 'idlix-downloader')
    elif os.name == 'posix':  # Linux/macOS
        base_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'idlix-downloader')
    else:
        base_dir = os.path.join(os.path.expanduser('~'), '.idlix-downloader')
    
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, 'downloads.db')


DATABASE_PATH = get_database_path()


async def init_database():
    """Initialize database schema"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Jobs table - stores video extraction info
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                movie_url TEXT NOT NULL,
                video_title TEXT,
                embed_url TEXT,
                base_url TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Variants table - stores quality options for each job
        await db.execute("""
            CREATE TABLE IF NOT EXISTS variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                quality TEXT,
                label TEXT,
                stream_url TEXT,
                bandwidth INTEGER,
                resolution TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            )
        """)
        
        # Downloads table - stores download progress and state
        await db.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                download_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                quality TEXT,
                output_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                cache_dir TEXT,
                stream_url TEXT,
                total_segments INTEGER DEFAULT 0,
                downloaded_segments INTEGER DEFAULT 0,
                failed_segments INTEGER DEFAULT 0,
                bytes_downloaded INTEGER DEFAULT 0,
                file_size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                progress_json TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            )
        """)
        
        # Settings table - stores app configuration
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for faster queries
        await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_downloads_job_id ON downloads(job_id)")
        
        await db.commit()
        print(f"✓ Database initialized: {DATABASE_PATH}")


async def create_job(job_id: str, movie_url: str, base_url: str):
    """Create a new job entry"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO jobs (job_id, movie_url, base_url, status)
            VALUES (?, ?, ?, 'extracting')
        """, (job_id, movie_url, base_url))
        await db.commit()


async def update_job(job_id: str, **kwargs):
    """Update job fields"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        set_clause += ', updated_at = CURRENT_TIMESTAMP'
        values = list(kwargs.values()) + [job_id]
        
        await db.execute(f"""
            UPDATE jobs SET {set_clause}
            WHERE job_id = ?
        """, values)
        await db.commit()


async def get_job(job_id: str):
    """Get job by ID"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def save_variants(job_id: str, variants: list):
    """Save quality variants for a job"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Clear existing variants
        await db.execute("DELETE FROM variants WHERE job_id = ?", (job_id,))
        
        # Insert new variants
        for variant in variants:
            await db.execute("""
                INSERT INTO variants (job_id, quality, label, stream_url, bandwidth, resolution)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                variant['quality'],
                variant['label'],
                variant['url'],
                variant['bandwidth'],
                json.dumps(variant['resolution']) if variant['resolution'] else None
            ))
        await db.commit()


async def get_variants(job_id: str):
    """Get variants for a job"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT quality, label, stream_url, bandwidth, resolution
            FROM variants WHERE job_id = ?
            ORDER BY bandwidth DESC
        """, (job_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{
                'quality': row['quality'],
                'label': row['label'],
                'url': row['stream_url'],
                'bandwidth': row['bandwidth'],
                'resolution': json.loads(row['resolution']) if row['resolution'] else None
            } for row in rows]


async def create_download(download_id: str, job_id: str, quality: str, output_path: str, 
                          filename: str, stream_url: str, cache_dir: str):
    """Create a new download entry"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO downloads (download_id, job_id, quality, output_path, filename, 
                                   stream_url, cache_dir, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (download_id, job_id, quality, output_path, filename, stream_url, cache_dir))
        await db.commit()


async def update_download(download_id: str, **kwargs):
    """Update download fields"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        set_clause += ', updated_at = CURRENT_TIMESTAMP'
        values = list(kwargs.values()) + [download_id]
        
        await db.execute(f"""
            UPDATE downloads SET {set_clause}
            WHERE download_id = ?
        """, values)
        await db.commit()


async def get_download(download_id: str):
    """Get download by ID"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM downloads WHERE download_id = ?", (download_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            download = dict(row)
            if download['progress_json']:
                download['progress'] = json.loads(download['progress_json'])
            return download


async def get_all_downloads(status_filter: str = None):
    """Get all downloads, optionally filtered by status"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        if status_filter:
            query = "SELECT * FROM downloads WHERE status = ? ORDER BY created_at DESC"
            params = (status_filter,)
        else:
            query = "SELECT * FROM downloads ORDER BY created_at DESC"
            params = ()
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            downloads = []
            for row in rows:
                download = dict(row)
                if download['progress_json']:
                    download['progress'] = json.loads(download['progress_json'])
                downloads.append(download)
            return downloads


async def get_downloads_by_job(job_id: str):
    """Get all downloads for a specific job"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM downloads WHERE job_id = ? ORDER BY created_at DESC
        """, (job_id,)) as cursor:
            rows = await cursor.fetchall()
            downloads = []
            for row in rows:
                download = dict(row)
                if download['progress_json']:
                    download['progress'] = json.loads(download['progress_json'])
                downloads.append(download)
            return downloads


async def mark_interrupted_downloads():
    """Mark all 'downloading' status jobs as 'interrupted' on server start"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE downloads 
            SET status = 'interrupted', updated_at = CURRENT_TIMESTAMP
            WHERE status IN ('downloading', 'pending', 'extracting', 'merging')
        """)
        await db.commit()


async def delete_download(download_id: str):
    """Delete a download entry"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM downloads WHERE download_id = ?", (download_id,))
        await db.commit()


async def get_setting(key: str, default=None):
    """Get a setting value"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default


async def set_setting(key: str, value: str):
    """Set a setting value"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
        """, (key, value, value))
        await db.commit()
