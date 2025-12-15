"""
Core module for simpl-temp library.
Provides the main sTemp class for temporary data management.
"""

import os
import json
import time
import hashlib
import threading
import shutil
from pathlib import Path
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta

from .exceptions import ConfigurationError, StorageError, ExpiredDataError


class _SimplTemp:
    """
    Main class for temporary data management.
    
    Usage:
        from simpl_temp import sTemp
        
        sTemp.config(directory="./temp_data")
        sTemp.set("key", "value", ttl=3600)
        value = sTemp.get("key")
    """
    
    def __init__(self):
        self._configured = False
        self._directory: Optional[Path] = None
        self._default_ttl: int = 3600  # 1 hour default
        self._auto_cleanup: bool = True
        self._encryption: bool = False
        self._secret_key: Optional[str] = None
        self._metadata_file: str = "_metadata.json"
        self._lock = threading.Lock()
        self._metadata: Dict[str, Dict] = {}
    
    def config(
        self,
        directory: str,
        default_ttl: int = 3600,
        auto_cleanup: bool = True,
        encryption: bool = False,
        secret_key: Optional[str] = None,
        create_if_missing: bool = True
    ) -> "_SimplTemp":
        """
        Configure the temporary storage.
        
        Args:
            directory: Path to the directory for storing temporary data.
            default_ttl: Default time-to-live in seconds (default: 3600).
            auto_cleanup: Automatically clean expired data (default: True).
            encryption: Enable data encryption (default: False).
            secret_key: Secret key for encryption (required if encryption=True).
            create_if_missing: Create directory if it doesn't exist (default: True).
            
        Returns:
            self for method chaining.
            
        Raises:
            ConfigurationError: If configuration is invalid.
        """
        if not directory:
            raise ConfigurationError("Directory path is required")
        
        self._directory = Path(directory).resolve()
        
        if create_if_missing:
            self._directory.mkdir(parents=True, exist_ok=True)
        elif not self._directory.exists():
            raise ConfigurationError(f"Directory does not exist: {self._directory}")
        
        if not self._directory.is_dir():
            raise ConfigurationError(f"Path is not a directory: {self._directory}")
        
        if encryption and not secret_key:
            raise ConfigurationError("Secret key is required when encryption is enabled")
        
        self._default_ttl = default_ttl
        self._auto_cleanup = auto_cleanup
        self._encryption = encryption
        self._secret_key = secret_key
        self._configured = True
        
        self._load_metadata()
        
        if self._auto_cleanup:
            self._cleanup_expired()
        
        return self
    
    def _ensure_configured(self) -> None:
        """Ensure the library is configured before use."""
        if not self._configured:
            raise ConfigurationError(
                "sTemp is not configured. Call sTemp.config(directory='...') first."
            )
    
    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a given key."""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self._directory / f"{safe_key}.tmp"
    
    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        metadata_path = self._directory / self._metadata_file
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._metadata = {}
        else:
            self._metadata = {}
    
    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        metadata_path = self._directory / self._metadata_file
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2)
    
    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key not in self._metadata:
            return True
        
        meta = self._metadata[key]
        if meta.get("ttl") == -1:  # Never expires
            return False
        
        expires_at = meta.get("expires_at", 0)
        return time.time() > expires_at
    
    def _cleanup_expired(self) -> int:
        """Remove expired data. Returns number of items cleaned."""
        with self._lock:
            cleaned = 0
            expired_keys = []
            
            for key in list(self._metadata.keys()):
                if self._is_expired(key):
                    expired_keys.append(key)
            
            for key in expired_keys:
                try:
                    file_path = self._get_file_path(key)
                    if file_path.exists():
                        file_path.unlink()
                    del self._metadata[key]
                    cleaned += 1
                except Exception:
                    pass
            
            if cleaned > 0:
                self._save_metadata()
            
            return cleaned
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Store a value with the given key.
        
        Args:
            key: Unique identifier for the data.
            value: Data to store (must be JSON serializable).
            ttl: Time-to-live in seconds. Use -1 for never expires.
                 None uses default_ttl from config.
            tags: Optional list of tags for grouping data.
            
        Returns:
            True if stored successfully.
            
        Raises:
            StorageError: If storage operation fails.
        """
        self._ensure_configured()
        
        if ttl is None:
            ttl = self._default_ttl
        
        with self._lock:
            try:
                file_path = self._get_file_path(key)
                
                # Prepare data
                data = {
                    "value": value,
                    "created_at": time.time(),
                    "key": key
                }
                
                # Write to file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                
                # Update metadata
                self._metadata[key] = {
                    "file": str(file_path),
                    "created_at": time.time(),
                    "ttl": ttl,
                    "expires_at": time.time() + ttl if ttl != -1 else -1,
                    "tags": tags or [],
                    "size": file_path.stat().st_size
                }
                self._save_metadata()
                
                return True
                
            except Exception as e:
                raise StorageError(f"Failed to store data: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value by key.
        
        Args:
            key: The key to retrieve.
            default: Default value if key not found or expired.
            
        Returns:
            The stored value or default.
        """
        self._ensure_configured()
        
        with self._lock:
            if key not in self._metadata:
                return default
            
            if self._is_expired(key):
                if self._auto_cleanup:
                    self._delete_internal(key)
                return default
            
            try:
                file_path = self._get_file_path(key)
                if not file_path.exists():
                    return default
                
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                return data.get("value", default)
                
            except Exception:
                return default
    
    def get_or_raise(self, key: str) -> Any:
        """
        Retrieve a value by key or raise an exception.
        
        Args:
            key: The key to retrieve.
            
        Returns:
            The stored value.
            
        Raises:
            StorageError: If key not found.
            ExpiredDataError: If data has expired.
        """
        self._ensure_configured()
        
        with self._lock:
            if key not in self._metadata:
                raise StorageError(f"Key not found: {key}")
            
            if self._is_expired(key):
                raise ExpiredDataError(f"Data has expired: {key}")
            
            try:
                file_path = self._get_file_path(key)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("value")
            except Exception as e:
                raise StorageError(f"Failed to retrieve data: {e}")
    
    def _delete_internal(self, key: str) -> bool:
        """Internal delete without lock."""
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
            if key in self._metadata:
                del self._metadata[key]
                self._save_metadata()
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a stored value.
        
        Args:
            key: The key to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        self._ensure_configured()
        
        with self._lock:
            return self._delete_internal(key)
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists and is not expired.
        
        Args:
            key: The key to check.
            
        Returns:
            True if exists and not expired.
        """
        self._ensure_configured()
        
        with self._lock:
            if key not in self._metadata:
                return False
            return not self._is_expired(key)
    
    def keys(self, include_expired: bool = False) -> List[str]:
        """
        Get all stored keys.
        
        Args:
            include_expired: Include expired keys (default: False).
            
        Returns:
            List of keys.
        """
        self._ensure_configured()
        
        with self._lock:
            if include_expired:
                return list(self._metadata.keys())
            return [k for k in self._metadata.keys() if not self._is_expired(k)]
    
    def get_by_tag(self, tag: str) -> Dict[str, Any]:
        """
        Get all values with a specific tag.
        
        Args:
            tag: The tag to filter by.
            
        Returns:
            Dictionary of key-value pairs.
        """
        self._ensure_configured()
        
        result = {}
        with self._lock:
            for key, meta in self._metadata.items():
                if tag in meta.get("tags", []) and not self._is_expired(key):
                    value = self.get(key)
                    if value is not None:
                        result[key] = value
        return result
    
    def delete_by_tag(self, tag: str) -> int:
        """
        Delete all values with a specific tag.
        
        Args:
            tag: The tag to filter by.
            
        Returns:
            Number of items deleted.
        """
        self._ensure_configured()
        
        deleted = 0
        with self._lock:
            keys_to_delete = [
                key for key, meta in self._metadata.items()
                if tag in meta.get("tags", [])
            ]
            for key in keys_to_delete:
                if self._delete_internal(key):
                    deleted += 1
        return deleted
    
    def ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key in seconds.
        
        Args:
            key: The key to check.
            
        Returns:
            Remaining seconds, -1 for never expires, None if not found.
        """
        self._ensure_configured()
        
        with self._lock:
            if key not in self._metadata:
                return None
            
            meta = self._metadata[key]
            if meta.get("ttl") == -1:
                return -1
            
            remaining = meta.get("expires_at", 0) - time.time()
            return max(0, int(remaining))
    
    def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """
        Extend the TTL of a key.
        
        Args:
            key: The key to extend.
            additional_seconds: Seconds to add.
            
        Returns:
            True if extended successfully.
        """
        self._ensure_configured()
        
        with self._lock:
            if key not in self._metadata:
                return False
            
            meta = self._metadata[key]
            if meta.get("ttl") == -1:
                return True  # Already never expires
            
            meta["expires_at"] = meta.get("expires_at", time.time()) + additional_seconds
            meta["ttl"] = meta.get("ttl", 0) + additional_seconds
            self._save_metadata()
            return True
    
    def clear(self) -> int:
        """
        Clear all stored data.
        
        Returns:
            Number of items cleared.
        """
        self._ensure_configured()
        
        with self._lock:
            count = len(self._metadata)
            
            for key in list(self._metadata.keys()):
                self._delete_internal(key)
            
            self._metadata = {}
            self._save_metadata()
            
            return count
    
    def cleanup(self) -> int:
        """
        Manually trigger cleanup of expired data.
        
        Returns:
            Number of items cleaned.
        """
        self._ensure_configured()
        return self._cleanup_expired()
    
    def stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats.
        """
        self._ensure_configured()
        
        with self._lock:
            total_keys = len(self._metadata)
            active_keys = len([k for k in self._metadata if not self._is_expired(k)])
            expired_keys = total_keys - active_keys
            
            total_size = sum(
                meta.get("size", 0) 
                for meta in self._metadata.values()
            )
            
            return {
                "directory": str(self._directory),
                "total_keys": total_keys,
                "active_keys": active_keys,
                "expired_keys": expired_keys,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "default_ttl": self._default_ttl,
                "auto_cleanup": self._auto_cleanup,
                "encryption_enabled": self._encryption
            }
    
    def info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata information about a key.
        
        Args:
            key: The key to get info for.
            
        Returns:
            Dictionary with key metadata or None.
        """
        self._ensure_configured()
        
        with self._lock:
            if key not in self._metadata:
                return None
            
            meta = self._metadata[key].copy()
            meta["is_expired"] = self._is_expired(key)
            meta["remaining_ttl"] = self.ttl(key)
            return meta
    
    def touch(self, key: str) -> bool:
        """
        Reset TTL to the original value (refresh expiration).
        
        Args:
            key: The key to touch.
            
        Returns:
            True if successful.
        """
        self._ensure_configured()
        
        with self._lock:
            if key not in self._metadata:
                return False
            
            meta = self._metadata[key]
            if meta.get("ttl") != -1:
                meta["expires_at"] = time.time() + meta.get("ttl", self._default_ttl)
                self._save_metadata()
            return True
    
    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> int:
        """
        Store multiple key-value pairs.
        
        Args:
            data: Dictionary of key-value pairs.
            ttl: Optional TTL for all items.
            
        Returns:
            Number of items stored.
        """
        self._ensure_configured()
        
        count = 0
        for key, value in data.items():
            if self.set(key, value, ttl=ttl):
                count += 1
        return count
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Retrieve multiple values.
        
        Args:
            keys: List of keys to retrieve.
            
        Returns:
            Dictionary of found key-value pairs.
        """
        self._ensure_configured()
        
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple keys.
        
        Args:
            keys: List of keys to delete.
            
        Returns:
            Number of items deleted.
        """
        self._ensure_configured()
        
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count
    
    @property
    def is_configured(self) -> bool:
        """Check if sTemp is configured."""
        return self._configured
    
    @property
    def directory(self) -> Optional[Path]:
        """Get the configured directory."""
        return self._directory


# Singleton instance
sTemp = _SimplTemp()
