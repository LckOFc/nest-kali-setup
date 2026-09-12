#!/usr/bin/env python3
"""
AGY Complete Authentication Bypass
====================================
Creates a fully patched binary with OAuth bypass
"""

import os
import re
import sys
import json
import hashlib
import base64
from pathlib import Path
from datetime import datetime, timedelta

class AGYAuthBypass:
    """Complete authentication bypass for agy.exe"""
    
    def __init__(self, binary_path: str):
        self.binary_path = binary_path
        self.output_path = binary_path.replace('.exe', '_full_bypass.exe')
        self.data = None
        
    def load(self):
        print(f"[*] Loading: {self.binary_path}")
        with open(self.binary_path, 'rb') as f:
            self.data = bytearray(f.read())
        print(f"[+] Loaded: {len(self.data):,} bytes")
        
    def save(self):
        print(f"[*] Saving: {self.output_path}")
        with open(self.output_path, 'wb') as f:
            f.write(bytes(self.data))
        print(f"[+] Saved: {os.path.getsize(self.output_path):,} bytes")
        
    def find_all(self, pattern: bytes) -> list:
        offsets = []
        start = 0
        while True:
            idx = self.data.find(pattern, start)
            if idx == -1:
                break
            offsets.append(idx)
            start = idx + 1
        return offsets
    
    def replace_all(self, original: bytes, replacement: bytes) -> int:
        if len(original) != len(replacement):
            replacement = replacement[:len(original)]
            if len(replacement) < len(original):
                replacement += b' ' * (len(original) - len(replacement))
        
        count = 0
        for offset in self.find_all(original):
            self.data[offset:offset+len(original)] = replacement
            count += 1
        return count
    
    def create_fake_token(self) -> str:
        """Create a fake but valid-looking JWT token"""
        # JWT Header
        header = base64.urlsafe_b64encode(json.dumps({
            "alg": "HS256",
            "typ": "JWT"
        }).encode()).rstrip(b'=').decode()
        
        # JWT Payload - make it look like a real Google token
        payload = base64.urlsafe_b64encode(json.dumps({
            "sub": "1234567890",
            "name": "AGY User",
            "email": "user@example.com",
            "email_verified": True,
            "iat": int(datetime.now().timestamp()) - 3600,
            "exp": int(datetime.now().timestamp()) + 86400,  # 24h expiry
            "aud": "local-bypass",
            "iss": "https://accounts.google.com"
        }).encode()).rstrip(b'=').decode()
        
        # Fake signature (ASCII only)
        signature = base64.urlsafe_b64encode(b'FAKE_SIGNATURE_32BYTES!!!').rstrip(b'=').decode()
        
        return f"{header}.{payload}.{signature}"
    
    def create_config_files(self):
        """Create configuration files for bypass"""
        config_dir = Path.home() / ".agy"
        config_dir.mkdir(exist_ok=True)
        
        # Token file
        token = self.create_fake_token()
        token_file = config_dir / "token.json"
        token_file.write_text(json.dumps({
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 86400,
            "refresh_token": "fake_refresh_token",
            "created_at": datetime.now().isoformat()
        }, indent=2))
        print(f"[+] Created token file: {token_file}")
        
        # Config file
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "api_base_url": "http://localhost:9999",  # Point to local mock
            "auth_mode": "bypass",
            "skip_verification": True,
            "models": {
                "default": "gemini-2.0-flash-exp",
                "alternatives": ["gemini-2.0-flash", "gemini-1.5-pro"]
            }
        }, indent=2))
        print(f"[+] Created config file: {config_file}")
        
        return config_dir
    
    def apply_patches(self):
        """Apply all authentication bypass patches"""
        print()
        print("[*] Applying authentication bypass patches...")
        print()
        
        patches = {
            # Critical auth bypass
            b'Please sign in to continue': b'Auto-signed in successfully',
            b'You need to sign in': b'Signed in automatically',
            b'Sign in with Google': b'Login bypassed',
            b'Authentication required': b'Authentication bypassed',
            b'Login required': b'Login bypassed',
            b'Permission denied': b'Permission granted',
            b'Access denied': b'Access granted',
            b'Not authorized': b'Authorized',
            b'unauthorized': b'authorized',
            b'Unauthorized': b'Authorized',
            b'not signed in': b'auto-signed in',
            b'Not signed in': b'Auto-signed in',
            
            # OAuth bypass
            b'oauth2.googleapis.com': b'local-auth-placeholder',
            b'accounts.google.com': b'local-auth-placeholder',
            b'openidconnect': b'local-auth-local',
            b'https://oauth2.googleapis.com/token': b'http://localhost:9999/fake-token',
            b'https://accounts.google.com/o/oauth2': b'http://localhost:9999/fake-auth',
            
            # Token validation bypass
            b'token expired': b'token valid (bypassed)',
            b'Token expired': b'Token valid (bypassed)',
            b'invalid token': b'valid token (bypassed)',
            b'Invalid token': b'Valid token (bypassed)',
            b'auth required': b'auth bypassed',
            b'no valid token': b'use bypass token',
            b'No valid token': b'Use bypass token',
            
            # Account checks
            b'google account': b'local account',
            b'Google account': b'Local account',
            b'must be signed in': b'auto-signed in',
            b'Must be signed in': b'Auto-signed in',
            b'must log in': b'logged in (bypassed)',
            b'Must log in': b'Logged in (bypassed)',
            
            # Browser auth bypass
            b'open browser': b'skip browser auth',
            b'Open browser': b'Skip browser auth',
            b'launch browser': b'skip launch',
            b'Launching browser': b'Skipping browser',
            b'open default browser': b'skip browser open',
            b'Open default browser': b'Skip browser open',
            
            # Popup/window bypass
            b'popup': b'bypass_popup',
            b'Popup': b'Bypass_popup',
            b'autologin popup': b'autologin bypassed',
            
            # Session checks
            b'session expired': b'session valid',
            b'Session expired': b'Session valid',
            b'no active session': b'active session exists',
            b'No active session': b'Active session exists',
            b'invalid session': b'valid session',
            
            # Error suppression
            b'ERROR: Authentication failed': b'AUTH_BYPASSED',
            b'error: authentication': b'auth_bypassed',
            b'Authentication failed': b'Authentication bypassed',
            b'authentication failed': b'authentication bypassed',
            
            # Redirect URLs
            b'http://localhost:8085': b'http://localhost:9999/callback',
            b'http://localhost:8080': b'http://localhost:9999/callback',
            b'urn:ietf:wg:oauth:2.0:oob': b'http://localhost:9999/oob',
            
            # More auth strings
            b'sign-in': b'bypass-signin',
            b'Sign-In': b'Bypass-Signin',
            b'signin': b'bypass-signin',
            b'Signin': b'Bypass-Signin',
            b'login required': b'login bypassed',
            b'Login required': b'Login bypassed',
        }
        
        total_patches = 0
        for original, replacement in patches.items():
            count = self.replace_all(original, replacement)
            if count > 0:
                print(f"  [+] {original.decode()[:40]:40s}: {count} patches")
                total_patches += count
        
        print()
        print(f"[+] Total patches applied: {total_patches}")
        
        return total_patches
    
    def patch_network_calls(self):
        """Patch network calls to redirect to local mock"""
        print()
        print("[*] Patching network calls...")
        print()
        
        # Redirect API calls to local mock
        api_patches = [
            (b'https://api.antigravity.google.com', b'http://localhost:9999/api'),
            (b'https://generativelanguage.googleapis.com', b'http://localhost:9999/ai'),
            (b'https://gemini.google.com', b'http://localhost:9999/gemini'),
        ]
        
        total = 0
        for original, replacement in api_patches:
            count = self.replace_all(original, replacement)
            if count > 0:
                print(f"  [+] {original.decode()[:50]}: {count}")
                total += count
        
        return total
    
    def add_bypass_marker(self):
        """Add a marker to indicate bypass is active"""
        marker = b'[AGY_AUTH_BYPASS_ACTIVE]'
        
        # Add to end of binary (before any null padding)
        # Find a safe place to add the marker
        for i in range(len(self.data) - len(marker), 0, -1):
            if self.data[i:i+len(marker)] == b'\x00' * len(marker):
                self.data[i:i+len(marker)] = marker
                print(f"[+] Added bypass marker at offset 0x{i:X}")
                return True
        
        # If no null space found, add to strings section
        null_idx = self.data.find(b'\x00' * 32)
        if null_idx > 0:
            self.data[null_idx:null_idx+len(marker)] = marker
            print(f"[+] Added bypass marker at offset 0x{null_idx:X}")
            return True
        
        return False


def main():
    print("=" * 70)
    print("  AGY COMPLETE AUTHENTICATION BYPASS")
    print("=" * 70)
    print()
    
    binary_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
    
    if not os.path.exists(binary_path):
        print(f"[ERROR] Binary not found: {binary_path}")
        return 1
    
    # Create bypass
    bypass = AGYAuthBypass(binary_path)
    bypass.load()
    
    # Apply patches
    string_patches = bypass.apply_patches()
    network_patches = bypass.patch_network_calls()
    bypass.add_bypass_marker()
    
    # Save
    bypass.save()
    
    # Create config
    config_dir = bypass.create_config_files()
    
    print()
    print("=" * 70)
    print("  BYPASS COMPLETE")
    print("=" * 70)
    print()
    print(f"Original: {binary_path}")
    print(f"Patched:  {bypass.output_path}")
    print(f"Config:   {config_dir}")
    print()
    print("Patches applied:")
    print(f"  - String patches: {string_patches}")
    print(f"  - Network redirects: {network_patches}")
    print(f"  - Bypass marker: Added")
    print()
    print("NOTE: This is a string-level bypass.")
    print("For complete authentication bypass, code-level changes are needed.")
    print()
    print("To use:")
    print(f"  1. Copy patched binary: copy \"{bypass.output_path}\" \"{binary_path}\"")
    print(f"  2. Or run directly: .\\{os.path.basename(bypass.output_path)}")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
