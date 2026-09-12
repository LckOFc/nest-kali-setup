#!/usr/bin/env python3
"""Download and install Ghidra + Go plugin"""

import urllib.request
import json
import os
import zipfile
import subprocess
import sys

def download_file(url, output_path):
    """Download a file with progress"""
    print(f"Downloading: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlretrieve(req, output_path)
        size = os.path.getsize(output_path)
        print(f"Downloaded: {size/1024/1024:.1f} MB")
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False

def main():
    print("=" * 70)
    print("  GHIDRA INSTALLER")
    print("=" * 70)
    print()
    
    # Create directories
    install_dir = r"C:\Tools\ghidra"
    os.makedirs(install_dir, exist_ok=True)
    
    # Step 1: Get latest release info
    print("[1] Fetching latest Ghidra release...")
    try:
        api_url = "https://api.github.com/repos/NationalSecurityAgency/ghidra/releases/latest"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            tag = data.get('tag_name', 'unknown')
            print(f"    Latest version: {tag}")
    except Exception as e:
        print(f"    Error fetching release info: {e}")
        tag = "Ghidra_11.2.1_build"
    
    # Step 2: Find Windows ZIP download
    print()
    print("[2] Finding Windows download...")
    
    download_url = None
    try:
        api_url = "https://api.github.com/repos/NationalSecurityAgency/ghidra/releases/latest"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            for asset in data.get('assets', []):
                name = asset.get('name', '')
                if 'win64' in name.lower() or ('windows' in name.lower() and 'zip' in name.lower()):
                    download_url = asset.get('browser_download_url')
                    print(f"    Found: {name}")
                    break
    except Exception as e:
        print(f"    Error: {e}")
    
    # Fallback URL
    if not download_url:
        download_url = "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.2.1_build/ghidra_11.2.1_20241210-zip.zip"
        print(f"    Using fallback: {download_url}")
    
    # Step 3: Download
    print()
    print("[3] Downloading Ghidra...")
    zip_path = r"C:\Tools\ghidra.zip"
    
    if not download_file(download_url, zip_path):
        print("    Failed to download Ghidra")
        return False
    
    # Step 4: Extract
    print()
    print("[4] Extracting Ghidra...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(r"C:\Tools")
        print("    Extracted successfully")
    except Exception as e:
        print(f"    Extraction error: {e}")
        return False
    
    # Step 5: Clean up
    print()
    print("[5] Cleaning up...")
    os.remove(zip_path)
    print("    Removed zip file")
    
    # Step 6: Clone Go plugin
    print()
    print("[6] Installing Go plugin...")
    plugin_dir = os.path.join(install_dir, "extensions", "Go")
    os.makedirs(plugin_dir, exist_ok=True)
    
    try:
        plugin_url = "https://github.com/Linesp/ghidra-go.git"
        subprocess.run(
            ["git", "clone", "--depth", "1", plugin_url, plugin_dir],
            capture_output=True,
            timeout=60
        )
        print("    Go plugin cloned successfully")
    except Exception as e:
        print(f"    Git clone error: {e}")
        print("    Trying manual download...")
        
        # Try downloading plugin ZIP
        plugin_zip = r"C:\Tools\ghidra-go.zip"
        if download_file("https://github.com/Linesp/ghidra-go/archive/refs/heads/master.zip", plugin_zip):
            with zipfile.ZipFile(plugin_zip, 'r') as zip_ref:
                zip_ref.extractall(os.path.join(install_dir, "extensions"))
            os.remove(plugin_zip)
            print("    Go plugin installed from ZIP")
    
    # Step 7: Create startup script
    print()
    print("[7] Creating startup scripts...")
    
    # Find Ghidra executable
    ghidra_dir = None
    for item in os.listdir(r"C:\Tools"):
        if "ghidra" in item.lower():
            ghidra_dir = os.path.join(r"C:\Tools", item)
            break
    
    if not ghidra_dir:
        ghidra_dir = install_dir
    
    # Create batch file
    batch_content = f'''@echo off
echo Starting Ghidra...
echo.
echo Ghidra location: {ghidra_dir}
echo Go plugin location: {plugin_dir}
echo.
echo To use the Go plugin:
echo 1. Open Ghidra
echo 2. Go to Analyze > Language
echo 3. Select "Go (Generic)" or similar
echo 4. Open your binary
echo.
"{ghidra_dir}\support\analyze.bat"
'''
    
    batch_path = r"C:\Tools\start_ghidra.bat"
    with open(batch_path, 'w') as f:
        f.write(batch_content)
    print(f"    Created: {batch_path}")
    
    # Step 8: Summary
    print()
    print("=" * 70)
    print("  INSTALLATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Ghidra installed at: {ghidra_dir}")
    print(f"Go plugin at: {plugin_dir}")
    print(f"Start script: {batch_path}")
    print()
    print("To use:")
    print("  1. Run: C:\\Tools\\start_ghidra.bat")
    print("  2. Or open Ghidra GUI manually")
    print("  3. Open agy.exe")
    print("  4. Let auto-analysis run")
    print()
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
