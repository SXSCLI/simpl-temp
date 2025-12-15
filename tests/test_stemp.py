"""
Tests for simpl-temp library.
"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path

from simpl_temp import sTemp, ConfigurationError, StorageError, ExpiredDataError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def configured_stemp(temp_dir):
    """Provide a configured sTemp instance."""
    # Reset sTemp state
    sTemp._configured = False
    sTemp._metadata = {}
    
    sTemp.config(directory=str(temp_dir), default_ttl=60)
    yield sTemp
    
    # Cleanup
    sTemp._configured = False
    sTemp._metadata = {}


class TestConfiguration:
    """Test configuration."""
    
    def test_config_creates_directory(self, temp_dir):
        """Test that config creates the directory if missing."""
        new_dir = temp_dir / "new_subdir"
        sTemp.config(directory=str(new_dir), create_if_missing=True)
        assert new_dir.exists()
    
    def test_config_raises_without_directory(self):
        """Test that config raises error without directory."""
        with pytest.raises(ConfigurationError):
            sTemp.config(directory="")
    
    def test_operations_require_config(self):
        """Test that operations require configuration."""
        sTemp._configured = False
        with pytest.raises(ConfigurationError):
            sTemp.get("key")


class TestBasicOperations:
    """Test basic set/get/delete operations."""
    
    def test_set_and_get(self, configured_stemp):
        """Test basic set and get."""
        configured_stemp.set("key1", "value1")
        assert configured_stemp.get("key1") == "value1"
    
    def test_set_complex_data(self, configured_stemp):
        """Test storing complex data types."""
        data = {
            "string": "value",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"a": 1, "b": 2}
        }
        configured_stemp.set("complex", data)
        assert configured_stemp.get("complex") == data
    
    def test_get_nonexistent_returns_default(self, configured_stemp):
        """Test get returns default for non-existent key."""
        assert configured_stemp.get("nonexistent") is None
        assert configured_stemp.get("nonexistent", "default") == "default"
    
    def test_delete(self, configured_stemp):
        """Test delete operation."""
        configured_stemp.set("to_delete", "value")
        assert configured_stemp.exists("to_delete")
        
        configured_stemp.delete("to_delete")
        assert not configured_stemp.exists("to_delete")
    
    def test_exists(self, configured_stemp):
        """Test exists operation."""
        assert not configured_stemp.exists("key")
        configured_stemp.set("key", "value")
        assert configured_stemp.exists("key")


class TestTTL:
    """Test TTL functionality."""
    
    def test_custom_ttl(self, configured_stemp):
        """Test custom TTL."""
        configured_stemp.set("short_lived", "value", ttl=1)
        assert configured_stemp.exists("short_lived")
        
        time.sleep(1.1)
        assert not configured_stemp.exists("short_lived")
    
    def test_never_expires(self, configured_stemp):
        """Test never expires with ttl=-1."""
        configured_stemp.set("permanent", "value", ttl=-1)
        assert configured_stemp.ttl("permanent") == -1
    
    def test_extend_ttl(self, configured_stemp):
        """Test extending TTL."""
        configured_stemp.set("key", "value", ttl=10)
        initial_ttl = configured_stemp.ttl("key")
        
        configured_stemp.extend_ttl("key", 60)
        extended_ttl = configured_stemp.ttl("key")
        
        assert extended_ttl > initial_ttl


class TestTags:
    """Test tag functionality."""
    
    def test_set_with_tags(self, configured_stemp):
        """Test setting data with tags."""
        configured_stemp.set("item1", "v1", tags=["group_a"])
        configured_stemp.set("item2", "v2", tags=["group_a"])
        configured_stemp.set("item3", "v3", tags=["group_b"])
        
        group_a = configured_stemp.get_by_tag("group_a")
        assert "item1" in group_a
        assert "item2" in group_a
        assert "item3" not in group_a
    
    def test_delete_by_tag(self, configured_stemp):
        """Test deleting by tag."""
        configured_stemp.set("item1", "v1", tags=["delete_me"])
        configured_stemp.set("item2", "v2", tags=["delete_me"])
        configured_stemp.set("item3", "v3", tags=["keep"])
        
        deleted = configured_stemp.delete_by_tag("delete_me")
        assert deleted == 2
        assert not configured_stemp.exists("item1")
        assert configured_stemp.exists("item3")


class TestBulkOperations:
    """Test bulk operations."""
    
    def test_set_many(self, configured_stemp):
        """Test setting multiple values."""
        data = {"k1": "v1", "k2": "v2", "k3": "v3"}
        count = configured_stemp.set_many(data)
        
        assert count == 3
        assert configured_stemp.get("k1") == "v1"
        assert configured_stemp.get("k2") == "v2"
    
    def test_get_many(self, configured_stemp):
        """Test getting multiple values."""
        configured_stemp.set("a", 1)
        configured_stemp.set("b", 2)
        configured_stemp.set("c", 3)
        
        result = configured_stemp.get_many(["a", "b", "d"])
        assert result == {"a": 1, "b": 2}
    
    def test_delete_many(self, configured_stemp):
        """Test deleting multiple values."""
        configured_stemp.set_many({"x": 1, "y": 2, "z": 3})
        deleted = configured_stemp.delete_many(["x", "y"])
        
        assert deleted == 2
        assert not configured_stemp.exists("x")
        assert configured_stemp.exists("z")


class TestStats:
    """Test statistics and info."""
    
    def test_stats(self, configured_stemp):
        """Test stats output."""
        configured_stemp.set("key1", "value1")
        configured_stemp.set("key2", "value2")
        
        stats = configured_stemp.stats()
        
        assert stats["active_keys"] >= 2
        assert "total_size_bytes" in stats
        assert "directory" in stats
    
    def test_info(self, configured_stemp):
        """Test key info."""
        configured_stemp.set("info_key", "value", tags=["test"])
        info = configured_stemp.info("info_key")
        
        assert info is not None
        assert "created_at" in info
        assert "tags" in info
        assert "test" in info["tags"]


class TestCleanup:
    """Test cleanup operations."""
    
    def test_manual_cleanup(self, configured_stemp):
        """Test manual cleanup."""
        configured_stemp.set("expire_soon", "value", ttl=1)
        time.sleep(1.1)
        
        cleaned = configured_stemp.cleanup()
        assert cleaned >= 1
    
    def test_clear(self, configured_stemp):
        """Test clear all data."""
        configured_stemp.set_many({"a": 1, "b": 2, "c": 3})
        cleared = configured_stemp.clear()
        
        assert cleared == 3
        assert len(configured_stemp.keys()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
