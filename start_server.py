#!/usr/bin/env python3
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from app.main import app
    import uvicorn.config
    import uvicorn.server
    
    config = uvicorn.config.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True
    )
    server = uvicorn.server.Server(config)
    server.run()
