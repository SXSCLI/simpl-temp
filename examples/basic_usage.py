"""
Example usage of simpl-temp library.
"""

from simpl_temp import sTemp

# 1. Configuration (REQUIRED before any operation)
print("=" * 50)
print("1. Configuration")
print("=" * 50)

sTemp.config(
    directory="./demo_temp_data",  # Directory for temporary files
    default_ttl=3600,              # Default TTL: 1 hour
    auto_cleanup=True,             # Auto-cleanup expired data
    create_if_missing=True         # Create directory if not exists
)

print(f"✓ Configured! Directory: {sTemp.directory}")
print(f"  Is configured: {sTemp.is_configured}")

# 2. Basic Operations
print("\n" + "=" * 50)
print("2. Basic Operations")
print("=" * 50)

# Set values
sTemp.set("user:1", {"name": "John", "age": 30})
sTemp.set("session:abc123", {"user_id": 1, "role": "admin"}, ttl=1800)  # 30 min
sTemp.set("api:token", "secret_token_value", ttl=-1)  # Never expires
print("✓ Set 3 values")

# Get values
user = sTemp.get("user:1")
print(f"✓ Get user:1 -> {user}")

# Get with default
missing = sTemp.get("non_existent", default="Not found")
print(f"✓ Get non_existent -> {missing}")

# Check existence
exists = sTemp.exists("user:1")
print(f"✓ Exists user:1 -> {exists}")

# Get TTL
ttl = sTemp.ttl("session:abc123")
print(f"✓ TTL session:abc123 -> {ttl} seconds")

# 3. Tags
print("\n" + "=" * 50)
print("3. Tags")
print("=" * 50)

sTemp.set("cache:products:1", {"name": "Product 1"}, tags=["cache", "products"])
sTemp.set("cache:products:2", {"name": "Product 2"}, tags=["cache", "products"])
sTemp.set("cache:users:1", {"name": "User 1"}, tags=["cache", "users"])
print("✓ Set 3 values with tags")

products = sTemp.get_by_tag("products")
print(f"✓ Get by tag 'products' -> {len(products)} items")

# 4. Bulk Operations
print("\n" + "=" * 50)
print("4. Bulk Operations")
print("=" * 50)

# Set many
count = sTemp.set_many({
    "bulk:1": "value1",
    "bulk:2": "value2",
    "bulk:3": "value3"
}, ttl=600)
print(f"✓ Set many -> {count} items stored")

# Get many
data = sTemp.get_many(["bulk:1", "bulk:2", "bulk:4"])
print(f"✓ Get many -> {data}")

# Delete many
deleted = sTemp.delete_many(["bulk:1", "bulk:2"])
print(f"✓ Delete many -> {deleted} items deleted")

# 5. Key Info and Stats
print("\n" + "=" * 50)
print("5. Key Info and Stats")
print("=" * 50)

# Key info
info = sTemp.info("user:1")
print(f"✓ Info user:1 -> created_at: {info['created_at']}, ttl: {info['ttl']}")

# Stats
stats = sTemp.stats()
print(f"✓ Stats:")
print(f"  - Active keys: {stats['active_keys']}")
print(f"  - Total size: {stats['total_size_bytes']} bytes")
print(f"  - Directory: {stats['directory']}")

# 6. TTL Management
print("\n" + "=" * 50)
print("6. TTL Management")
print("=" * 50)

sTemp.set("short_lived", "data", ttl=100)
initial = sTemp.ttl("short_lived")
print(f"✓ Initial TTL: {initial} seconds")

sTemp.extend_ttl("short_lived", 200)
extended = sTemp.ttl("short_lived")
print(f"✓ After extend_ttl(200): {extended} seconds")

sTemp.touch("short_lived")
touched = sTemp.ttl("short_lived")
print(f"✓ After touch: {touched} seconds")

# 7. List Keys
print("\n" + "=" * 50)
print("7. List Keys")
print("=" * 50)

keys = sTemp.keys()
print(f"✓ All active keys ({len(keys)}): {keys[:5]}{'...' if len(keys) > 5 else ''}")

# 8. Cleanup
print("\n" + "=" * 50)
print("8. Cleanup")
print("=" * 50)

cleaned = sTemp.cleanup()
print(f"✓ Cleanup expired -> {cleaned} items removed")

# Clear all (commented to preserve data)
# cleared = sTemp.clear()
# print(f"✓ Clear all -> {cleared} items removed")

print("\n" + "=" * 50)
print("Demo completed successfully!")
print("=" * 50)
