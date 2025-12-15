# simpl-temp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/simpl-temp.svg)](https://badge.fury.io/py/simpl-temp)

**Professional Python library for temporary data management with API support.**

Developer: **Kozosvyst Stas (StasX)** | **2025** | **MIT**

---

## 🚀 Features

- ✅ Simple and intuitive API
- ✅ TTL (Time-To-Live) support for automatic data expiration
- ✅ Tag-based data organization
- ✅ Automatic cleanup of expired data
- ✅ Thread-safe operations
- ✅ Built-in REST API (FastAPI)
- ✅ Bulk operations (set_many, get_many, delete_many)
- ✅ Storage statistics
- ✅ CLI for API server

---

## 📦 Installation

```bash
# Basic installation
pip install simpl-temp

# With API support
pip install simpl-temp[api]

# Full installation (with dev tools)
pip install simpl-temp[all]
```

---

## 🔧 Quick Start

### Basic Usage

```python
from simpl_temp import sTemp

# Configuration (required before use)
sTemp.config(
    directory="./temp_data",  # Storage directory
    default_ttl=3600,         # Default TTL: 1 hour
    auto_cleanup=True         # Automatic cleanup
)

# Store data
sTemp.set("user_session", {"user_id": 123, "name": "John"})

# Store with custom TTL (30 minutes)
sTemp.set("temp_token", "abc123", ttl=1800)

# Store with tags
sTemp.set("cache_item", {"data": "value"}, tags=["cache", "api"])

# Never expire
sTemp.set("permanent_key", "value", ttl=-1)

# Retrieve data
session = sTemp.get("user_session")
print(session)  # {'user_id': 123, 'name': 'John'}

# Get with default value
value = sTemp.get("non_existent", default="fallback")

# Check existence
if sTemp.exists("user_session"):
    print("Session exists!")

# Delete data
sTemp.delete("temp_token")

# Get remaining TTL
remaining = sTemp.ttl("user_session")
print(f"Expires in {remaining} seconds")
```

### Advanced Features

```python
from simpl_temp import sTemp

sTemp.config(directory="./data")

# Bulk operations
sTemp.set_many({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}, ttl=600)

data = sTemp.get_many(["key1", "key2", "key3"])
print(data)  # {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}

sTemp.delete_many(["key1", "key2"])

# Tag-based operations
sTemp.set("item1", "data1", tags=["group_a"])
sTemp.set("item2", "data2", tags=["group_a"])
sTemp.set("item3", "data3", tags=["group_b"])

group_a_data = sTemp.get_by_tag("group_a")
print(group_a_data)  # {'item1': 'data1', 'item2': 'data2'}

deleted_count = sTemp.delete_by_tag("group_a")
print(f"Deleted {deleted_count} items")

# TTL management
sTemp.extend_ttl("key3", 3600)  # Add 1 hour
sTemp.touch("key3")  # Reset TTL to original value

# Get key info
info = sTemp.info("key3")
print(info)
# {
#     'file': '/path/to/file.tmp',
#     'created_at': 1702654321.123,
#     'ttl': 3600,
#     'expires_at': 1702657921.123,
#     'tags': [],
#     'size': 45,
#     'is_expired': False,
#     'remaining_ttl': 3599
# }

# Storage statistics
stats = sTemp.stats()
print(stats)
# {
#     'directory': '/path/to/data',
#     'total_keys': 10,
#     'active_keys': 8,
#     'expired_keys': 2,
#     'total_size_bytes': 2048,
#     'total_size_mb': 0.0,
#     'default_ttl': 3600,
#     'auto_cleanup': True,
#     'encryption_enabled': False
# }

# Manual cleanup
cleaned = sTemp.cleanup()
print(f"Cleaned {cleaned} expired items")

# Clear all data
cleared = sTemp.clear()
print(f"Cleared {cleared} items")

# Get all keys
all_keys = sTemp.keys()
all_keys_including_expired = sTemp.keys(include_expired=True)
```

### Error Handling

```python
from simpl_temp import sTemp, ConfigurationError, StorageError, ExpiredDataError

try:
    # Will raise ConfigurationError if not configured
    sTemp.get("key")
except ConfigurationError as e:
    print(f"Configuration error: {e}")

sTemp.config(directory="./data")

try:
    # Will raise if key not found or expired
    value = sTemp.get_or_raise("non_existent_key")
except StorageError as e:
    print(f"Storage error: {e}")
except ExpiredDataError as e:
    print(f"Data expired: {e}")
```

---

## 🌐 REST API

### Start API Server

```bash
# Using CLI
simpl-temp-api --host 0.0.0.0 --port 8000 --directory ./temp_data

# Or programmatically
```

```python
from simpl_temp import sTemp
from simpl_temp.api import create_api, run_api

# Configure storage first
sTemp.config(directory="./temp_data")

# Run API server
run_api(host="0.0.0.0", port=8000)
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/config` | Configure storage |
| POST | `/api/v1/data` | Store data |
| GET | `/api/v1/data/{key}` | Get data |
| DELETE | `/api/v1/data/{key}` | Delete data |
| GET | `/api/v1/exists/{key}` | Check existence |
| GET | `/api/v1/keys` | Get all keys |
| GET | `/api/v1/ttl/{key}` | Get TTL |
| POST | `/api/v1/ttl/extend` | Extend TTL |
| POST | `/api/v1/touch/{key}` | Refresh TTL |
| GET | `/api/v1/info/{key}` | Get key info |
| POST | `/api/v1/data/bulk` | Store multiple |
| POST | `/api/v1/data/bulk/get` | Get multiple |
| POST | `/api/v1/data/bulk/delete` | Delete multiple |
| GET | `/api/v1/tags/{tag}` | Get by tag |
| DELETE | `/api/v1/tags/{tag}` | Delete by tag |
| GET | `/api/v1/stats` | Storage stats |
| POST | `/api/v1/cleanup` | Cleanup expired |
| DELETE | `/api/v1/clear` | Clear all |

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📚 API Reference

### `sTemp.config()`

Configure the temporary storage.

```python
sTemp.config(
    directory: str,           # Required: Storage directory path
    default_ttl: int = 3600,  # Default TTL in seconds
    auto_cleanup: bool = True,  # Auto-cleanup expired data
    encryption: bool = False,   # Enable encryption (future)
    secret_key: str = None,     # Encryption key
    create_if_missing: bool = True  # Create directory if missing
)
```

### `sTemp.set()`

Store a value.

```python
sTemp.set(
    key: str,              # Unique key
    value: Any,            # JSON-serializable value
    ttl: int = None,       # TTL in seconds (-1 = never expires)
    tags: List[str] = None  # Optional tags
) -> bool
```

### `sTemp.get()`

Retrieve a value.

```python
sTemp.get(
    key: str,           # Key to retrieve
    default: Any = None  # Default if not found
) -> Any
```

### `sTemp.delete()`

Delete a value.

```python
sTemp.delete(key: str) -> bool
```

### `sTemp.exists()`

Check if key exists and is not expired.

```python
sTemp.exists(key: str) -> bool
```

### `sTemp.keys()`

Get all stored keys.

```python
sTemp.keys(include_expired: bool = False) -> List[str]
```

### `sTemp.ttl()`

Get remaining TTL for a key.

```python
sTemp.ttl(key: str) -> Optional[int]  # -1 = never expires, None = not found
```

### `sTemp.extend_ttl()`

Extend the TTL of a key.

```python
sTemp.extend_ttl(key: str, additional_seconds: int) -> bool
```

### `sTemp.touch()`

Reset TTL to original value.

```python
sTemp.touch(key: str) -> bool
```

### `sTemp.info()`

Get metadata about a key.

```python
sTemp.info(key: str) -> Optional[Dict[str, Any]]
```

### `sTemp.stats()`

Get storage statistics.

```python
sTemp.stats() -> Dict[str, Any]
```

### `sTemp.cleanup()`

Manually trigger cleanup.

```python
sTemp.cleanup() -> int  # Returns number of items cleaned
```

### `sTemp.clear()`

Clear all data.

```python
sTemp.clear() -> int  # Returns number of items cleared
```

---

## 🧪 Development

```bash
# Clone repository
git clone https://github.com/StasX/simpl-temp.git
cd simpl-temp

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black simpl_temp
isort simpl_temp

# Type checking
mypy simpl_temp
```

---

### ⚠️ When NOT to use simpl-temp
- High-concurrency distributed systems
- Multi-node clusters
- Sub-millisecond latency requirements


## 📄 License

MIT License

Copyright (c) 2025 Kozosvyst Stas (StasX)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.