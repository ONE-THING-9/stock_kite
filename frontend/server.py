#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend files
Run with: python server.py
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 3000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow requests to the FastAPI backend
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to the frontend directory
    frontend_dir = Path(__file__).parent.absolute()
    os.chdir(frontend_dir)
    
    # Create server
    handler = CustomHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    
    print(f"Frontend server starting on http://localhost:{PORT}")
    print(f"Serving files from: {frontend_dir}")
    print("Make sure your FastAPI backend is running on http://localhost:8000")
    print("\nPress Ctrl+C to stop the server")
    
    # Try to open browser
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        pass
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    main()