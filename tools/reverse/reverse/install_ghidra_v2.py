#!/usr/bin/env python3
"""Install Ghidra and Go plugin"""

import urllib.request
import json
import os
import zipfile
import subprocess
import sys
import ssl

# Create SSL context that doesn't verify certificates (for corporate networks)
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def download_url(url, output):
    """Download file from URL"""
    print(f"  Downloading: {url[:60]}...")
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        urllib.request.urlretrieve(req, output)
        size = os.path.getsize(output)
        print(f"  Downloaded: {size/1024/1024:.1f} MB")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 70)
    print("  GHIDRA INSTALLER WITH GO PLUGIN")
    print("=" * 70)
    print()
    
    base_dir = r"C:\Tools"
    ghidra_dir = os.path.join(base_dir, "ghidra")
    os.makedirs(ghidra_dir, exist_ok=True)
    
    # Step 1: Download Ghidra
    print("[1] Downloading Ghidra...")
    
    # Try different URLs
    urls = [
        "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.1.2_build/ghidra_11.1.2_20240720.zip",
        "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.0.3_build/ghidra_11.0.3_20240216.zip",
    ]
    
    zip_path = os.path.join(base_dir, "ghidra.zip")
    downloaded = False
    
    for url in urls:
        if download_url(url, zip_path):
            downloaded = True
            break
    
    if not downloaded:
        print("  Failed to download Ghidra from known URLs")
        print("  Please download manually from: https://ghidra-sre.org/")
        return False
    
    # Step 2: Extract
    print()
    print("[2] Extracting Ghidra...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Get the top-level folder name
            all_files = z.namelist()
            top_folder = all_files[0].split('/')[0] if all_files else 'ghidra'
            
            # Extract
            for file in all_files:
                z.extract(file, base_dir)
        
        # Rename if needed
        extracted_dir = os.path.join(base_dir, top_folder)
        if os.path.exists(extracted_dir) and extracted_dir != ghidra_dir:
            import shutil
            if os.path.exists(ghidra_dir):
                shutil.rmtree(ghidra_dir)
            os.rename(extracted_dir, ghidra_dir)
        
        print(f"  Extracted to: {ghidra_dir}")
    except Exception as e:
        print(f"  Extraction error: {e}")
        return False
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
    
    # Step 3: Install Java (check if needed)
    print()
    print("[3] Checking Java...")
    java_found = False
    
    # Check common Java locations
    java_paths = [
        r"C:\Program Files\Java",
        r"C:\Program Files (x86)\Java",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Java'),
    ]
    
    for java_base in java_paths:
        if os.path.exists(java_base):
            for item in os.listdir(java_base):
                if 'jdk' in item.lower() or 'java' in item.lower():
                    java_home = os.path.join(java_base, item)
                    java_bin = os.path.join(java_home, 'bin', 'java.exe')
                    if os.path.exists(java_bin):
                        print(f"  Found Java: {java_home}")
                        os.environ['JAVA_HOME'] = java_home
                        os.environ['Path'] = java_home + r'\bin;' + os.environ.get('Path', '')
                        java_found = True
                        break
    
    if not java_found:
        print("  Java not found. Installing via winget...")
        try:
            subprocess.run(
                ['winget', 'install', '--id', 'Microsoft.OpenJDK.17', 
                 '--accept-source-agreements', '--accept-package-agreements'],
                capture_output=True,
                timeout=180
            )
            print("  Java installed")
        except Exception as e:
            print(f"  Java install error: {e}")
            print("  Please install Java 17+ manually from: https://adoptium.net/")
    
    # Step 4: Install Go plugin
    print()
    print("[4] Installing Go plugin...")
    plugin_dir = os.path.join(ghidra_dir, "extensions", "Go")
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Try git clone first
    try:
        print("  Trying git clone...")
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', 'https://github.com/Linesp/ghidra-go.git', plugin_dir],
            capture_output=True,
            timeout=120
        )
        if result.returncode == 0:
            print("  Go plugin cloned successfully")
        else:
            raise Exception(result.stderr.decode() if result.stderr else "Git clone failed")
    except Exception as e:
        print(f"  Git clone failed: {e}")
        print("  Trying direct download...")
        
        # Download ZIP directly
        plugin_zip = os.path.join(base_dir, "ghidra-go.zip")
        if download_url("https://github.com/Linesp/ghidra-go/archive/refs/heads/master.zip", plugin_zip):
            try:
                with zipfile.ZipFile(plugin_zip, 'r') as z:
                    z.extractall(plugin_dir)
                # Move contents up
                extracted = os.path.join(plugin_dir, "ghidra-go-master")
                if os.path.exists(extracted):
                    import shutil
                    for item in os.listdir(extracted):
                        shutil.move(os.path.join(extracted, item), plugin_dir)
                    os.rmdir(extracted)
                print("  Go plugin installed from ZIP")
            except Exception as ex:
                print(f"  ZIP extraction error: {ex}")
            finally:
                if os.path.exists(plugin_zip):
                    os.remove(plugin_zip)
    
    # Step 5: Create startup script
    print()
    print("[5] Creating startup script...")
    
    # Find ghidraRun.bat
    batch_path = None
    for root, dirs, files in os.walk(ghidra_dir):
        if 'ghidraRun.bat' in files:
            batch_path = os.path.join(root, 'ghidraRun.bat')
            break
    
    if not batch_path:
        # Try to find the script location
        scripts_dir = os.path.join(ghidra_dir, "support")
        if os.path.exists(scripts_dir):
            batch_path = os.path.join(scripts_dir, "analyze.bat")
    
    start_script = os.path.join(base_dir, "start_ghidra.bat")
    
    with open(start_script, 'w') as f:
        f.write("@echo off\n")
        f.write(f'echo Starting Ghidra with Go plugin...\n')
        f.write(f'echo.\n')
        f.write(f'echo Ghidra location: {ghidra_dir}\n')
        f.write(f'echo Go plugin location: {plugin_dir}\n')
        f.write(f'echo.\n')
        if batch_path and os.path.exists(batch_path):
            f.write(f'call "{batch_path}"\n')
        else:
            f.write(f'cd /d "{ghidra_dir}"\n')
            f.write(f'start ghidraRun.bat\n')
        f.write(f'pause\n')
    
    print(f"  Created: {start_script}")
    
    # Step 6: Summary
    print()
    print("=" * 70)
    print("  INSTALLATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Ghidra: {ghidra_dir}")
    print(f"Go plugin: {plugin_dir}")
    print(f"Start script: {start_script}")
    print()
    print("To use:")
    print(f'  1. Run: "{start_script}"')
    print("  2. Or manually open Ghidra GUI")
    print("  3. Open agy.exe")
    print("  4. Wait for auto-analysis")
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
