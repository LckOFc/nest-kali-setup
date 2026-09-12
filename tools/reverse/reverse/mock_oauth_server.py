#!/usr/bin/env python3
"""
Mock OAuth Server for AGY Bypass
=================================
Runs a local server to simulate Google OAuth
"""

import http.server
import json
import socketserver
import threading
import webbrowser
import sys
import os
from datetime import datetime, timedelta

PORT = 9999
ACCESS_TOKEN = "mock_agy_token_" + datetime.now().strftime("%Y%m%d%H%M%S")

class MockOAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if "/token" in self.path:
            # Return mock token
            response = {
                "access_token": ACCESS_TOKEN,
                "token_type": "Bearer",
                "expires_in": 3600
            }
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif "/authorize" in self.path:
            # Redirect with auth code
            redirect_url = f"http://localhost:{PORT}/callback?code=mock_auth_code_12345"
            self.send_response(302)
            self.send_header("Location", redirect_url)
            self.end_headers()
            
        elif "/callback" in self.path:
            # Success page
            html = f"""
            <html>
            <body style="font-family: Arial; text-align: center; margin-top: 50px;">
                <h1 style="color: green;">Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <p>Token: {ACCESS_TOKEN[:20]}...</p>
                <script>window.close()</script>
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        self.do_GET()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def run_server():
    with socketserver.TCPServer(("localhost", PORT), MockOAuthHandler) as httpd:
        print(f"Mock OAuth Server running on http://localhost:{PORT}")
        print(f"Access Token: {ACCESS_TOKEN}")
        print("Opening browser for authentication...")
        webbrowser.open(f"http://localhost:{PORT}/authorize")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
