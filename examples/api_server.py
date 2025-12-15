"""
Example: Running simpl-temp REST API server.
"""

from simpl_temp import sTemp
from simpl_temp.api import create_api, run_api

# Configure storage first
sTemp.config(
    directory="./api_temp_data",
    default_ttl=3600,
    auto_cleanup=True,
    create_if_missing=True
)

print("=" * 50)
print("simpl-temp API Server")
print("=" * 50)
print(f"Storage: {sTemp.directory}")
print("Documentation: http://localhost:8000/docs")
print("=" * 50)

# Run the API server
if __name__ == "__main__":
    run_api(host="0.0.0.0", port=8000)
