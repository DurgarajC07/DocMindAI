"""Advanced file upload handling with streaming and chunked processing."""

import asyncio
import hashlib
import mimetypes
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import HTTPException, UploadFile, status
from loguru import logger

from backend.config import get_settings

settings = get_settings()


class StreamingFileHandler:
    """Handle large file uploads with streaming and progress tracking."""

    def __init__(self, max_chunk_size: int = 1024 * 1024):  # 1MB chunks
        self.max_chunk_size = max_chunk_size

    async def save_file_streaming(
        self,
        file: UploadFile,
        destination: Path,
        max_size: int = None,
    ) -> dict[str, Any]:
        """
        Save uploaded file with streaming to handle large files.
        
        Args:
            file: FastAPI UploadFile object
            destination: Path to save file
            max_size: Maximum allowed file size in bytes
            
        Returns:
            dict with file_path, file_size, content_hash
        """
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        total_bytes = 0
        hasher = hashlib.sha256()
        
        try:
            with open(destination, "wb") as f:
                while True:
                    # Read chunk
                    chunk = await file.read(self.max_chunk_size)
                    if not chunk:
                        break
                    
                    # Check size limit
                    total_bytes += len(chunk)
                    if max_size and total_bytes > max_size:
                        # Clean up partial file
                        f.close()
                        destination.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File size exceeds limit of {max_size} bytes",
                        )
                    
                    # Write chunk
                    f.write(chunk)
                    hasher.update(chunk)
            
            content_hash = hasher.hexdigest()
            
            logger.info(f"File saved: {destination.name} ({total_bytes} bytes)")
            
            return {
                "file_path": str(destination),
                "file_size": total_bytes,
                "content_hash": content_hash,
                "mime_type": self._get_mime_type(destination),
            }
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up on error
            destination.unlink(missing_ok=True)
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File save failed: {str(e)}",
            )

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file."""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"

    async def validate_file(
        self,
        file: UploadFile,
        allowed_extensions: list[str] = None,
        max_size: int = None,
    ) -> tuple[bool, str]:
        """
        Validate file before processing.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check filename
        if not file.filename:
            return False, "Filename is required"
        
        # Check extension
        file_ext = Path(file.filename).suffix.lower()
        allowed = allowed_extensions or settings.allowed_extensions
        
        if file_ext not in allowed:
            return False, f"File type {file_ext} not allowed. Allowed: {', '.join(allowed)}"
        
        # Check file size (if we can get it from headers)
        if hasattr(file, "size") and file.size:
            if max_size and file.size > max_size:
                return False, f"File size ({file.size} bytes) exceeds limit ({max_size} bytes)"
        
        return True, ""

    async def check_duplicate(self, file_hash: str, business_id: str) -> bool:
        """Check if file with same hash already exists."""
        # This would query database for existing files with same hash
        # For now, return False (no duplicate)
        return False


class ChunkedFileProcessor:
    """Process large files in chunks to avoid memory issues."""

    def __init__(self, chunk_size: int = 10 * 1024 * 1024):  # 10MB
        self.chunk_size = chunk_size

    async def process_large_pdf(
        self,
        file_path: Path,
    ) -> AsyncGenerator[tuple[int, str], None]:
        """
        Process large PDF in chunks.
        
        Yields:
            tuple: (page_number, text_content)
        """
        try:
            from pypdf import PdfReader
            
            # Open PDF
            reader = await asyncio.to_thread(PdfReader, str(file_path))
            total_pages = len(reader.pages)
            
            logger.info(f"Processing PDF: {total_pages} pages")
            
            # Process pages in batches
            batch_size = 10
            for i in range(0, total_pages, batch_size):
                batch_end = min(i + batch_size, total_pages)
                
                for page_num in range(i, batch_end):
                    try:
                        page = reader.pages[page_num]
                        text = await asyncio.to_thread(page.extract_text)
                        
                        if text.strip():
                            yield (page_num + 1, text)
                            
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_num + 1}: {e}")
                        continue
                
                # Allow other tasks to run
                await asyncio.sleep(0)
                
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            raise Exception(f"PDF processing failed: {str(e)}")

    async def process_large_text(
        self,
        file_path: Path,
    ) -> AsyncGenerator[str, None]:
        """
        Process large text file in chunks.
        
        Yields:
            str: Text chunk
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    yield chunk
                    await asyncio.sleep(0)  # Allow other tasks
                    
        except Exception as e:
            logger.error(f"Failed to process text file: {e}")
            raise Exception(f"Text processing failed: {str(e)}")


class FileDeduplicator:
    """Detect and handle duplicate file uploads."""

    def __init__(self):
        self.hash_cache: dict[str, str] = {}

    async def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        hasher = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                hasher.update(chunk)
        
        return hasher.hexdigest()

    def is_duplicate(self, file_hash: str, business_id: str) -> bool:
        """Check if file hash is duplicate for this business."""
        cache_key = f"{business_id}:{file_hash}"
        return cache_key in self.hash_cache

    def mark_processed(self, file_hash: str, business_id: str, doc_id: str):
        """Mark file as processed."""
        cache_key = f"{business_id}:{file_hash}"
        self.hash_cache[cache_key] = doc_id


class UploadProgressTracker:
    """Track upload progress for large files."""

    def __init__(self):
        self.uploads: dict[str, dict[str, Any]] = {}

    def start_upload(self, upload_id: str, total_size: int, filename: str):
        """Start tracking an upload."""
        self.uploads[upload_id] = {
            "filename": filename,
            "total_size": total_size,
            "uploaded_size": 0,
            "status": "uploading",
            "progress": 0.0,
        }

    def update_progress(self, upload_id: str, uploaded_size: int):
        """Update upload progress."""
        if upload_id in self.uploads:
            upload = self.uploads[upload_id]
            upload["uploaded_size"] = uploaded_size
            upload["progress"] = (uploaded_size / upload["total_size"]) * 100 if upload["total_size"] > 0 else 0

    def complete_upload(self, upload_id: str):
        """Mark upload as complete."""
        if upload_id in self.uploads:
            self.uploads[upload_id]["status"] = "complete"
            self.uploads[upload_id]["progress"] = 100.0

    def fail_upload(self, upload_id: str, error: str):
        """Mark upload as failed."""
        if upload_id in self.uploads:
            self.uploads[upload_id]["status"] = "failed"
            self.uploads[upload_id]["error"] = error

    def get_progress(self, upload_id: str) -> dict[str, Any] | None:
        """Get upload progress."""
        return self.uploads.get(upload_id)

    def cleanup_old_uploads(self, max_age_seconds: int = 3600):
        """Clean up old upload records."""
        import time
        current_time = time.time()
        
        to_delete = []
        for upload_id, data in self.uploads.items():
            if data.get("status") in ["complete", "failed"]:
                # Check if we should clean up (this is simplified)
                to_delete.append(upload_id)
        
        for upload_id in to_delete:
            del self.uploads[upload_id]


# Global instances
file_handler = StreamingFileHandler()
file_processor = ChunkedFileProcessor()
file_deduplicator = FileDeduplicator()
progress_tracker = UploadProgressTracker()


async def handle_large_file_upload(
    file: UploadFile,
    business_id: str,
    upload_dir: Path,
    max_size: int,
) -> dict[str, Any]:
    """
    Main function to handle large file upload with all optimizations.
    
    Returns:
        dict with file info and metadata
    """
    import uuid
    from datetime import datetime
    
    upload_id = str(uuid.uuid4())
    
    try:
        # Validate file
        is_valid, error_msg = await file_handler.validate_file(
            file,
            max_size=max_size,
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        destination = upload_dir / unique_filename
        
        # Start progress tracking
        file_size = getattr(file, "size", 0)
        progress_tracker.start_upload(upload_id, file_size, file.filename)
        
        # Save file with streaming
        file_info = await file_handler.save_file_streaming(
            file,
            destination,
            max_size=max_size,
        )
        
        # Check for duplicates
        file_hash = file_info["content_hash"]
        if file_deduplicator.is_duplicate(file_hash, business_id):
            logger.info(f"Duplicate file detected: {file_hash}")
            # Could return existing document instead
        
        # Complete progress
        progress_tracker.complete_upload(upload_id)
        
        return {
            **file_info,
            "upload_id": upload_id,
            "filename": file.filename,
            "unique_filename": unique_filename,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        
    except HTTPException:
        progress_tracker.fail_upload(upload_id, "Validation failed")
        raise
    except Exception as e:
        progress_tracker.fail_upload(upload_id, str(e))
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )
