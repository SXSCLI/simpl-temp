"""
CLI module for simpl-temp API server.
"""

import argparse
import sys


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="simpl-temp API Server",
        prog="simpl-temp-api"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--directory",
        type=str,
        default="./temp_data",
        help="Directory for temporary storage (default: ./temp_data)"
    )
    
    parser.add_argument(
        "--ttl",
        type=int,
        default=3600,
        help="Default TTL in seconds (default: 3600)"
    )
    
    args = parser.parse_args()
    
    try:
        from .api import run_api
        from .core import sTemp
        
        # Pre-configure sTemp
        sTemp.config(
            directory=args.directory,
            default_ttl=args.ttl,
            auto_cleanup=True,
            create_if_missing=True
        )
        
        print(f"Starting simpl-temp API server...")
        print(f"Storage directory: {args.directory}")
        print(f"Default TTL: {args.ttl} seconds")
        print(f"Server: http://{args.host}:{args.port}")
        print(f"Documentation: http://{args.host}:{args.port}/docs")
        
        run_api(host=args.host, port=args.port, reload=args.reload)
        
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install API dependencies: pip install simpl-temp[api]")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
