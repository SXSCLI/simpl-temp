"""
REST API module for simpl-temp library.
Provides a FastAPI-based HTTP interface for temporary data management.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    from fastapi import FastAPI, HTTPException, Query, Body
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .core import sTemp
from .exceptions import ConfigurationError, StorageError, ExpiredDataError


if FASTAPI_AVAILABLE:
    
    class SetDataRequest(BaseModel):
        """Request model for setting data."""
        key: str = Field(..., description="Unique key for the data")
        value: Any = Field(..., description="Data to store")
        ttl: Optional[int] = Field(None, description="Time-to-live in seconds")
        tags: Optional[List[str]] = Field(None, description="Tags for grouping")
    
    class SetManyRequest(BaseModel):
        """Request model for setting multiple data items."""
        data: Dict[str, Any] = Field(..., description="Dictionary of key-value pairs")
        ttl: Optional[int] = Field(None, description="TTL for all items")
    
    class GetManyRequest(BaseModel):
        """Request model for getting multiple data items."""
        keys: List[str] = Field(..., description="List of keys to retrieve")
    
    class DeleteManyRequest(BaseModel):
        """Request model for deleting multiple data items."""
        keys: List[str] = Field(..., description="List of keys to delete")
    
    class ExtendTTLRequest(BaseModel):
        """Request model for extending TTL."""
        key: str = Field(..., description="Key to extend")
        additional_seconds: int = Field(..., description="Seconds to add")
    
    class ConfigRequest(BaseModel):
        """Request model for configuration."""
        directory: str = Field(..., description="Path to storage directory")
        default_ttl: int = Field(3600, description="Default TTL in seconds")
        auto_cleanup: bool = Field(True, description="Enable auto cleanup")
        create_if_missing: bool = Field(True, description="Create directory if missing")


def create_api(
    title: str = "simpl-temp API",
    description: str = "REST API for temporary data management",
    version: str = "1.0.0",
    prefix: str = "/api/v1"
) -> "FastAPI":
    """
    Create a FastAPI application for the simpl-temp API.
    
    Args:
        title: API title.
        description: API description.
        version: API version.
        prefix: URL prefix for all endpoints.
        
    Returns:
        FastAPI application instance.
        
    Raises:
        ImportError: If FastAPI is not installed.
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI is required for API functionality. "
            "Install it with: pip install fastapi uvicorn"
        )
    
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "configured": sTemp.is_configured,
            "version": version
        }
    
    # Configuration
    @app.post(f"{prefix}/config")
    async def configure(config: ConfigRequest):
        """Configure the storage."""
        try:
            sTemp.config(
                directory=config.directory,
                default_ttl=config.default_ttl,
                auto_cleanup=config.auto_cleanup,
                create_if_missing=config.create_if_missing
            )
            return {"status": "configured", "directory": config.directory}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Set data
    @app.post(f"{prefix}/data")
    async def set_data(request: SetDataRequest):
        """Store a value."""
        try:
            success = sTemp.set(
                key=request.key,
                value=request.value,
                ttl=request.ttl,
                tags=request.tags
            )
            return {"status": "ok", "key": request.key, "stored": success}
        except (ConfigurationError, StorageError) as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Get data
    @app.get(f"{prefix}/data/{{key}}")
    async def get_data(key: str, default: Optional[str] = None):
        """Retrieve a value by key."""
        try:
            value = sTemp.get(key, default=default)
            if value is None:
                raise HTTPException(status_code=404, detail=f"Key not found: {key}")
            return {"key": key, "value": value}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Delete data
    @app.delete(f"{prefix}/data/{{key}}")
    async def delete_data(key: str):
        """Delete a value by key."""
        try:
            deleted = sTemp.delete(key)
            if not deleted:
                raise HTTPException(status_code=404, detail=f"Key not found: {key}")
            return {"status": "deleted", "key": key}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Check existence
    @app.get(f"{prefix}/exists/{{key}}")
    async def check_exists(key: str):
        """Check if a key exists."""
        try:
            exists = sTemp.exists(key)
            return {"key": key, "exists": exists}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Get all keys
    @app.get(f"{prefix}/keys")
    async def get_keys(include_expired: bool = False):
        """Get all stored keys."""
        try:
            keys = sTemp.keys(include_expired=include_expired)
            return {"keys": keys, "count": len(keys)}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Get TTL
    @app.get(f"{prefix}/ttl/{{key}}")
    async def get_ttl(key: str):
        """Get remaining TTL for a key."""
        try:
            ttl = sTemp.ttl(key)
            if ttl is None:
                raise HTTPException(status_code=404, detail=f"Key not found: {key}")
            return {"key": key, "ttl": ttl, "never_expires": ttl == -1}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Extend TTL
    @app.post(f"{prefix}/ttl/extend")
    async def extend_ttl(request: ExtendTTLRequest):
        """Extend the TTL of a key."""
        try:
            success = sTemp.extend_ttl(request.key, request.additional_seconds)
            if not success:
                raise HTTPException(status_code=404, detail=f"Key not found: {request.key}")
            return {"status": "extended", "key": request.key}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Touch (refresh TTL)
    @app.post(f"{prefix}/touch/{{key}}")
    async def touch_key(key: str):
        """Refresh the TTL of a key."""
        try:
            success = sTemp.touch(key)
            if not success:
                raise HTTPException(status_code=404, detail=f"Key not found: {key}")
            return {"status": "touched", "key": key}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Get key info
    @app.get(f"{prefix}/info/{{key}}")
    async def get_info(key: str):
        """Get metadata about a key."""
        try:
            info = sTemp.info(key)
            if info is None:
                raise HTTPException(status_code=404, detail=f"Key not found: {key}")
            return {"key": key, "info": info}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Set many
    @app.post(f"{prefix}/data/bulk")
    async def set_many(request: SetManyRequest):
        """Store multiple values."""
        try:
            count = sTemp.set_many(request.data, ttl=request.ttl)
            return {"status": "ok", "stored": count}
        except (ConfigurationError, StorageError) as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Get many
    @app.post(f"{prefix}/data/bulk/get")
    async def get_many(request: GetManyRequest):
        """Retrieve multiple values."""
        try:
            data = sTemp.get_many(request.keys)
            return {"data": data, "found": len(data)}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Delete many
    @app.post(f"{prefix}/data/bulk/delete")
    async def delete_many(request: DeleteManyRequest):
        """Delete multiple values."""
        try:
            count = sTemp.delete_many(request.keys)
            return {"status": "deleted", "count": count}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Get by tag
    @app.get(f"{prefix}/tags/{{tag}}")
    async def get_by_tag(tag: str):
        """Get all values with a specific tag."""
        try:
            data = sTemp.get_by_tag(tag)
            return {"tag": tag, "data": data, "count": len(data)}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Delete by tag
    @app.delete(f"{prefix}/tags/{{tag}}")
    async def delete_by_tag(tag: str):
        """Delete all values with a specific tag."""
        try:
            count = sTemp.delete_by_tag(tag)
            return {"status": "deleted", "tag": tag, "count": count}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Stats
    @app.get(f"{prefix}/stats")
    async def get_stats():
        """Get storage statistics."""
        try:
            stats = sTemp.stats()
            return stats
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Cleanup
    @app.post(f"{prefix}/cleanup")
    async def cleanup():
        """Trigger cleanup of expired data."""
        try:
            count = sTemp.cleanup()
            return {"status": "cleaned", "removed": count}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Clear all
    @app.delete(f"{prefix}/clear")
    async def clear_all():
        """Clear all stored data."""
        try:
            count = sTemp.clear()
            return {"status": "cleared", "removed": count}
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return app


def run_api(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    **kwargs
) -> None:
    """
    Run the API server.
    
    Args:
        host: Host to bind to.
        port: Port to bind to.
        reload: Enable auto-reload for development.
        **kwargs: Additional arguments for uvicorn.
    """
    try:
        import uvicorn
    except ImportError:
        raise ImportError(
            "uvicorn is required to run the API server. "
            "Install it with: pip install uvicorn"
        )
    
    app = create_api()
    uvicorn.run(app, host=host, port=port, reload=reload, **kwargs)
