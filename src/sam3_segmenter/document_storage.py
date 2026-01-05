"""
Document storage management for SAM3 Drawing Segmenter.

Folder structure per document:
    storage/
    └── {YYYYMMDD_HHMMSS}_{sanitized_filename}/
        ├── metadata.json       # Document metadata
        ├── original/           # Original uploaded image
        │   └── image.{ext}
        ├── viewer/            # Auto-run segmentation results
        │   ├── zones.json     # Zone detection results
        │   └── masks/         # Individual mask images
        └── playground/        # Interactive session data
            ├── sessions/      # Session snapshots
            └── exports/       # User exports

Based on docling-interactive storage patterns.
"""

import json
import logging
import os
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DocumentStorage:
    """Manages document folder structure and file operations."""

    # Subfolder names
    ORIGINAL_DIR = "original"
    VIEWER_DIR = "viewer"
    PLAYGROUND_DIR = "playground"
    MASKS_DIR = "masks"
    SESSIONS_DIR = "sessions"
    EXPORTS_DIR = "exports"

    def __init__(self, storage_base_dir: str = "./storage"):
        """
        Initialize document storage manager.

        Args:
            storage_base_dir: Base directory for all document storage.
        """
        self._base_dir = self._resolve_storage_path(storage_base_dir)
        self._ensure_base_dir()

    def _resolve_storage_path(self, storage_path: str) -> Path:
        """Resolve storage base directory to absolute path."""
        path = Path(storage_path)
        if not path.is_absolute():
            # Resolve relative to current working directory
            path = Path.cwd() / path
        return path.resolve()

    def _ensure_base_dir(self) -> None:
        """Ensure base storage directory exists with secure permissions."""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self._base_dir, 0o700)  # rwx for owner only
        except OSError as e:
            logger.warning(f"Could not set directory permissions for {self._base_dir}: {e}")

    def generate_doc_id(self, original_filename: str) -> str:
        """
        Generate a document ID from timestamp and filename.

        Format: YYYYMMDD_HHMMSS_{sanitized_name}

        Args:
            original_filename: Original filename from upload.

        Returns:
            Unique document ID string.
        """
        # Use UTC timezone for consistency
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Get filename without extension
        name = Path(original_filename).stem

        # Normalize Unicode to NFC form
        name = unicodedata.normalize("NFC", name)

        # Sanitize: keep only alphanumeric, hyphen, underscore
        # Replace spaces and other chars with underscore
        name = re.sub(r"[^\w\-]", "_", name)
        name = re.sub(r"_+", "_", name)  # Collapse multiple underscores
        name = name.strip("_")

        # Limit length to prevent filesystem issues
        name = name[:50]

        # Ensure we have a name
        if not name:
            name = "document"

        return f"{timestamp}_{name}"

    def sanitize_doc_id(self, doc_id: str) -> str:
        """
        Sanitize document ID to prevent path traversal attacks.

        Args:
            doc_id: Document ID to sanitize.

        Returns:
            Sanitized document ID.

        Raises:
            ValueError: If doc_id contains invalid characters.
        """
        # Only allow alphanumeric, underscore, and hyphen
        if not re.match(r"^[\w\-]+$", doc_id):
            raise ValueError(f"Invalid document ID: {doc_id}")
        return doc_id

    def get_document_dir(self, doc_id: str, create: bool = False) -> Path:
        """
        Get the base directory for a document.

        Args:
            doc_id: Document ID.
            create: If True, create directory if it doesn't exist.

        Returns:
            Path to document directory.
        """
        safe_doc_id = self.sanitize_doc_id(doc_id)
        path = self._base_dir / safe_doc_id

        if create and not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(path, 0o700)  # rwx for owner only
            except OSError as e:
                logger.warning(f"Could not set directory permissions for {path}: {e}")

        return path

    def get_original_dir(self, doc_id: str, create: bool = False) -> Path:
        """Get the 'original' subdirectory for storing the uploaded image."""
        doc_dir = self.get_document_dir(doc_id, create=create)
        path = doc_dir / self.ORIGINAL_DIR
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_original_image_path(self, doc_id: str) -> Optional[Path]:
        """
        Get path to the original image file.

        Returns None if no image file exists.
        """
        original_dir = self.get_original_dir(doc_id)
        if not original_dir.exists():
            return None

        # Find image file (could be various extensions)
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"]:
            for name in ["image", "original"]:
                path = original_dir / f"{name}{ext}"
                if path.exists():
                    return path

        # Try to find any image file
        for f in original_dir.iterdir():
            if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"]:
                return f

        return None

    def get_viewer_dir(self, doc_id: str, create: bool = False) -> Path:
        """Get the 'viewer' subdirectory for auto-run segmentation results."""
        doc_dir = self.get_document_dir(doc_id, create=create)
        path = doc_dir / self.VIEWER_DIR
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_viewer_masks_dir(self, doc_id: str, create: bool = False) -> Path:
        """Get the 'viewer/masks' subdirectory for mask images."""
        viewer_dir = self.get_viewer_dir(doc_id, create=create)
        path = viewer_dir / self.MASKS_DIR
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_playground_dir(self, doc_id: str, create: bool = False) -> Path:
        """Get the 'playground' subdirectory for interactive sessions."""
        doc_dir = self.get_document_dir(doc_id, create=create)
        path = doc_dir / self.PLAYGROUND_DIR
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_playground_sessions_dir(self, doc_id: str, create: bool = False) -> Path:
        """Get the 'playground/sessions' subdirectory."""
        playground_dir = self.get_playground_dir(doc_id, create=create)
        path = playground_dir / self.SESSIONS_DIR
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_playground_exports_dir(self, doc_id: str, create: bool = False) -> Path:
        """Get the 'playground/exports' subdirectory."""
        playground_dir = self.get_playground_dir(doc_id, create=create)
        path = playground_dir / self.EXPORTS_DIR
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_metadata_path(self, doc_id: str) -> Path:
        """Get path to document metadata.json file."""
        doc_dir = self.get_document_dir(doc_id)
        return doc_dir / "metadata.json"

    def get_viewer_zones_path(self, doc_id: str) -> Path:
        """Get path to viewer zones.json file."""
        viewer_dir = self.get_viewer_dir(doc_id)
        return viewer_dir / "zones.json"

    def save_metadata(self, doc_id: str, metadata: dict[str, Any]) -> Path:
        """
        Save document metadata to JSON file (atomic write).

        Args:
            doc_id: Document ID.
            metadata: Metadata dictionary to save.

        Returns:
            Path to saved metadata file.
        """
        doc_dir = self.get_document_dir(doc_id, create=True)
        metadata_path = doc_dir / "metadata.json"

        # Atomic write: write to temp file, then rename
        temp_path = metadata_path.with_suffix(".json.tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(metadata, f, indent=2)
            os.replace(temp_path, metadata_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        return metadata_path

    def load_metadata(self, doc_id: str) -> Optional[dict[str, Any]]:
        """
        Load document metadata from JSON file.

        Returns None if metadata file doesn't exist.
        """
        metadata_path = self.get_metadata_path(doc_id)
        if not metadata_path.exists():
            return None

        with open(metadata_path, "r") as f:
            return json.load(f)

    def save_viewer_zones(self, doc_id: str, zones_data: dict[str, Any]) -> Path:
        """
        Save viewer zones data to JSON file.

        Args:
            doc_id: Document ID.
            zones_data: Zones data to save.

        Returns:
            Path to saved zones file.
        """
        viewer_dir = self.get_viewer_dir(doc_id, create=True)
        zones_path = viewer_dir / "zones.json"

        # Atomic write
        temp_path = zones_path.with_suffix(".json.tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(zones_data, f, indent=2)
            os.replace(temp_path, zones_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        return zones_path

    def load_viewer_zones(self, doc_id: str) -> Optional[dict[str, Any]]:
        """Load viewer zones data from JSON file."""
        zones_path = self.get_viewer_zones_path(doc_id)
        if not zones_path.exists():
            return None

        with open(zones_path, "r") as f:
            return json.load(f)

    def save_playground_session(
        self, doc_id: str, session_id: str, session_data: dict[str, Any]
    ) -> Path:
        """Save a playground session snapshot."""
        sessions_dir = self.get_playground_sessions_dir(doc_id, create=True)
        session_path = sessions_dir / f"{session_id}.json"

        # Atomic write
        temp_path = session_path.with_suffix(".json.tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(session_data, f, indent=2)
            os.replace(temp_path, session_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        return session_path

    def document_exists(self, doc_id: str) -> bool:
        """Check if a document exists (has metadata file)."""
        try:
            metadata_path = self.get_metadata_path(doc_id)
            return metadata_path.exists()
        except ValueError:
            return False

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and all its files/folders.

        Args:
            doc_id: Document ID to delete.

        Returns:
            True if document was deleted, False if it didn't exist.

        Raises:
            ValueError: If doc_id is invalid.
        """
        doc_dir = self.get_document_dir(doc_id)

        if not doc_dir.exists():
            return False

        # Security check: ensure path is within storage directory
        try:
            doc_dir.resolve().relative_to(self._base_dir)
        except ValueError:
            raise ValueError(f"Invalid document directory: {doc_dir}")

        # Security check: prevent symlink attacks
        if doc_dir.is_symlink():
            raise ValueError("Cannot delete symlink directory")

        # Delete entire directory tree
        shutil.rmtree(doc_dir)
        logger.info(f"Deleted document folder: {doc_id}")

        return True

    def list_documents(self) -> list[dict[str, Any]]:
        """
        List all documents with their metadata.

        Returns:
            List of document metadata dictionaries, sorted by upload date (newest first).
        """
        documents = []

        if not self._base_dir.exists():
            return documents

        for doc_dir in self._base_dir.iterdir():
            if not doc_dir.is_dir():
                continue
            if doc_dir.name.startswith("."):
                continue

            # Try to load metadata
            metadata_path = doc_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    documents.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to load metadata for {doc_dir.name}: {e}")

        # Sort by upload date (newest first)
        documents.sort(key=lambda d: d.get("upload_date", ""), reverse=True)

        return documents

    def migrate_flat_storage(self, old_storage_dir: Optional[Path] = None) -> int:
        """
        Migrate from flat storage (doc_id.json + doc_id.ext) to folder structure.

        Args:
            old_storage_dir: Directory with old flat storage. If None, uses base dir.

        Returns:
            Number of documents migrated.
        """
        old_dir = old_storage_dir or self._base_dir
        migrated = 0

        if not old_dir.exists():
            return migrated

        # Find all metadata JSON files in root (flat structure)
        for json_file in old_dir.glob("*.json"):
            if json_file.parent != old_dir:
                continue  # Skip files in subdirectories

            try:
                with open(json_file, "r") as f:
                    metadata = json.load(f)

                old_doc_id = metadata.get("doc_id", json_file.stem)
                old_filename = metadata.get("filename", "")
                original_filename = metadata.get("original_filename", old_filename)

                # Find corresponding image file
                old_image_path = None
                for ext in [".png", ".jpg", ".jpeg"]:
                    candidate = old_dir / f"{json_file.stem}{ext}"
                    if candidate.exists():
                        old_image_path = candidate
                        break

                if not old_image_path:
                    logger.warning(f"No image found for {json_file}, skipping")
                    continue

                # Generate new folder-based doc_id
                new_doc_id = self.generate_doc_id(original_filename or old_doc_id)

                # Create new folder structure
                doc_dir = self.get_document_dir(new_doc_id, create=True)
                original_dir = self.get_original_dir(new_doc_id, create=True)

                # Move image file
                new_image_path = original_dir / f"image{old_image_path.suffix}"
                shutil.copy2(old_image_path, new_image_path)

                # Update metadata with new doc_id
                metadata["doc_id"] = new_doc_id
                metadata["filename"] = new_image_path.name
                metadata["migrated_from"] = old_doc_id
                metadata["migration_date"] = datetime.now(timezone.utc).isoformat()

                # Save new metadata
                self.save_metadata(new_doc_id, metadata)

                # Delete old files
                old_image_path.unlink()
                json_file.unlink()

                logger.info(f"Migrated {old_doc_id} -> {new_doc_id}")
                migrated += 1

            except Exception as e:
                logger.error(f"Failed to migrate {json_file}: {e}", exc_info=True)

        return migrated


# Global instance (initialized in main.py)
document_storage: Optional[DocumentStorage] = None


def get_document_storage() -> DocumentStorage:
    """Get the global document storage instance."""
    global document_storage
    if document_storage is None:
        from .config import settings
        document_storage = DocumentStorage(settings.documents_dir)
    return document_storage
