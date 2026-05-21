#!/usr/bin/env python3
"""
===========================================
   INSTAGRAM OSINT SCANNER v2.0
   Fully Working - Kali Linux Compatible
   Author: HackerAI
===========================================
Legal: Collects ONLY publicly available information.
       Use only for authorized security testing.
===========================================
"""

import os
import sys
import json
import time
import requests
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

# ================= CONFIG =================
BANNER_TEXT = """
╔══════════════════════════════════════════════╗
║        INSTAGRAM OSINT SCANNER v2.0          ║
║      Automated Instagram Investigation Tool   ║
╚══════════════════════════════════════════════╝
"""

# ================= COLOR CODES =================
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
END = '\033[0m'

def print_color(color, text):
    print(f"{color}{text}{END}")

# ================= MAIN SCANNER CLASS =================
class InstagramOSINT:
    def __init__(self, username):
        self.username = username
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = f"instagram_osint_{username}_{self.timestamp}"
        self.results = {
            "username": username,
            "scan_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "profile_info": {},
            "cross_platform": [],
            "reverse_image": [],
            "metadata": {},
            "dorks": []
        }
        
    def setup_directories(self):
        """Create output directory structure"""
        print_color(CYAN, "\n[+] Setting up directories...")
        Path(f"{self.output_dir}/photos").mkdir(parents=True, exist_ok=True)
        Path(f"{self.output_dir}/reports").mkdir(parents=True, exist_ok=True)
        Path(f"{self.output_dir}/instaloader_data").mkdir(parents=True, exist_ok=True)
        print_color(GREEN, f"    ✓ Output folder: {self.output_dir}/")

    def run_instaloader(self):
        """Download all public profile data using Instaloader"""
        print_color(CYAN, "\n═══ [1/5] INSTALOADER - Downloading Profile Data ═══")
        
        try:
            # Check if instaloader is installed
            subprocess.run(["which", "instaloader"], check=True, capture_output=True)
            
            print_color(YELLOW, f"    Downloading profile: {self.username}")
            cmd = [
                "instaloader", 
                "profile", 
                self.username,
                "--dirname-pattern", 
                f"{self.output_dir}/instaloader_data/{self.username}",
                "--no-captions",
                "--no-compress-json",
                "--no-video-thumbnails",
                "--count", "50"  # Limit to 50 posts for speed
            ]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Show progress
            for line in process.stdout:
                if line.strip():
                    print(f"    {line.strip()}")
            
            process.wait()
            
            if process.returncode == 0:
                print_color(GREEN, "    ✓ Profile data downloaded successfully!")
                
                # Try to find JSON file with profile info
                json_files = list(Path(f"{self.output_dir}/instaloader_data/{self.username}").glob("*.json"))
                if json_files:
                    with open(json_files[0], 'r') as f:
                        data = json.load(f)
                        self.results["profile_info"] = {
                            "bio": data.get("biography", "N/A"),
                            "followers": data.get("edge_followed_by", {}).get("count", "N/A"),
                            "following": data.get("edge_follow", {}).get("count", "N/A"),
                            "posts": data.get("edge_owner_to_timeline_media", {}).get("count", "N/A"),
                            "full_name": data.get("full_name", "N/A"),
                            "is_private": data.get("is_private", "N/A"),
                            "is_business": data.get("is_business_account", "N/A"),
                            "is_verified": data.get("is_verified", "N/A"),
                            "external_url": data.get("external_url", "N/A"),
                            "profile_pic_url": data.get("profile_pic_url_hd", "N/A"),
                        }
                return True
            else:
                print_color(RED, f"    ✗ Instaloader failed. Error: {process.stderr.read()}")
                return False
                
        except subprocess.CalledProcessError:
            print_color(RED, "\n    ✗ Instaloader not installed. Installing now...")
            os.system("pip3 install instaloader")
            print_color(GREEN, "    ✓ Installed. Please run the script again.")
            return False
        except Exception as e:
            print_color(RED, f"    ✗ Error: {str(e)}")
            return False

    def run_sherlock(self):
        """Check username on 300+ platforms"""
        print_color(CYAN, "\n═══ [2/5] SHERLOCK - Cross-Platform Username Search ═══")
        
        try:
            subprocess.run(["which", "sherlock"], check=True, capture_output=True)
            
            output_file = f"{self.output_dir}/reports/sherlock_results.txt"
            print_color(YELLOW, f"    Searching '{self.username}' on 300+ sites...")
            
            cmd = [
                "sherlock",
                self.username,
                "--output", output_file,
                "--timeout", "30"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            for line in process.stdout:
                if line.strip():
                    # Check if it found something (Sherlock shows URLs in output)
                    if "http" in line.lower():
                        self.results["cross_platform"].append(line.strip())
                        print_color(GREEN, f"    🔗 {line.strip()}")
                    else:
                        print(f"    {line.strip()}")
            
            process.wait()
            
            if os.path.exists(output_file):
                print_color(GREEN, f"    ✓ Results saved to: {output_file}")
                return True
            else:
                print_color(RED, "    ✗ Sherlock didn't produce output file")
                return False
                
        except subprocess.CalledProcessError:
            print_color(RED, "\n    ✗ Sherlock not installed. Installing now...")
            os.system("sudo apt install -y sherlock 2>/dev/null || pip3 install sherlock")
            print_color(GREEN, "    ✓ Installed. Please run the script again.")
            return False
        except Exception as e:
            print_color(RED, f"    ✗ Sherlock Error: {str(e)}")
            return False

    def reverse_image_search(self):
        """Find profile photo and open reverse image search"""
        print_color(CYAN, "\n═══ [3/5] REVERSE IMAGE SEARCH ═══")
        
        # Find profile photo
        photo_path = None
        search_dir = Path(f"{self.output_dir}/instaloader_data/{self.username}")
        
        if search_dir.exists():
            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                photos = list(search_dir.glob(f"**/{ext}"))
                for photo in photos:
                    if "profile" in photo.name.lower() or "profpic" in photo.name.lower():
                        photo_path = photo
                        break
                    if photo.stat().st_size < 50000:  # Profile pics are usually smaller
                        photo_path = photo
        
        if photo_path and photo_path.exists():
            print_color(GREEN, f"    ✓ Profile photo found: {photo_path}")
            
            # Copy to photos folder
            os.system(f"cp '{photo_path}' {self.output_dir}/photos/profile_pic.jpg")
            
            # Open reverse image search in browser
            print_color(YELLOW, "\n    Opening reverse image searches in browser...")
            time.sleep(1)
            
            # Google Images
            print_color(BLUE, "\n    📸 Google Images: Upload manually")
            print(f"        URL: https://images.google.com")
            print(f"        Click camera icon → Upload photo from: {self.output_dir}/photos/profile_pic.jpg")
            
            # TinEye
            print_color(BLUE, "\n    📸 TinEye: Upload manually")
            print(f"        URL: https://tineye.com")
            print(f"        Upload photo from: {self.output_dir}/photos/profile_pic.jpg")
            
            # Yandex
            print_color(BLUE, "\n    📸 Yandex: Upload manually")
            print(f"        URL: https://yandex.com/images/")
            
            # Save the URLs for the report
            self.results["reverse_image"] = [
                f"Google Images: https://images.google.com",
                f"TinEye: https://tineye.com",
                f"Yandex: https://yandex.com/images/",
                f"Photo path: {photo_path}"
            ]
            
            print_color(GREEN, "\n    ✓ Photo saved for manual reverse image search")
            return True
        else:
            print_color(RED, "    ✗ Profile photo not found in downloaded data")
            print_color(YELLOW, "    Alternative: Right-click profile pic on Instagram → Save image")
            print(f"    Then upload to: https://images.google.com")
            return False

    def check_metadata(self):
        """Check EXIF metadata in downloaded photos"""
        print_color(CYAN, "\n═══ [4/5] METADATA ANALYSIS ═══")
        
        try:
            # Check if exiftool is available
            subprocess.run(["which", "exiftool"], check=True, capture_output=True)
            
            output_file = f"{self.output_dir}/reports/metadata.txt"
            cmd = f"exiftool {self.output_dir}/instaloader_data/{self.username}/ -r > {output_file} 2>&1"
            os.system(cmd)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, 'r') as f:
                    content = f.read()
                
                # Check for GPS data
                if any(x in content for x in ["GPS", "Latitude", "Longitude", "Location"]):
                    print_color(RED, "    🔥 [CRITICAL] GPS DATA FOUND!")
                    print_color(YELLOW, "    Location might be embedded in photos!")
                    
                    # Extract GPS lines
                    for line in content.split('\n'):
                        if any(x in line for x in ["GPS", "Latitude", "Longitude"]):
                            print(f"        {line}")
                            self.results["metadata"]["gps_found"] = True
                            self.results["metadata"]["gps_data"] = line
                else:
                    print_color(YELLOW, "    📌 No GPS data found (Instagram strips metadata)")
                    self.results["metadata"]["gps_found"] = False
                
                # Check for other useful info
                info_checks = {
                    "Camera": "Camera Model",
                    "Date": "Date/Time",
                    "Software": "Software Used",
                    "Make": "Camera Make"
                }
                
                for key, label in info_checks.items():
                    if key in content:
                        val = [l for l in content.split('\n') if key in l]
                        if val:
                            print_color(CYAN, f"    Found: {val[0].strip()}")
                            self.results["metadata"][label] = val[0].strip()
                
                print_color(GREEN, f"    ✓ Metadata saved to: {output_file}")
                return True
            else:
                print_color(YELLOW, "    No photos with metadata found")
                return False
                
        except subprocess.CalledProcessError:
            print_color(RED, "\n    ✗ ExifTool not installed. Installing now...")
            os.system("sudo apt install -y exiftool")
            print_color(GREEN, "    ✓ Installed. Please run the script again.")
            return False
        except Exception as e:
            print_color(RED, f"    ✗ Error: {str(e)}")
            return False

    def generate_google_dorks(self):
        """Generate Google dork queries"""
        print_color(CYAN, "\n═══ [5/5] GOOGLE DORK GENERATOR ═══")
        
        dorks = [
            f'site:instagram.com "{self.username}"',
            f'site:facebook.com "{self.username}"',
            f'site:twitter.com "{self.username}"',
            f'site:reddit.com "{self.username}"',
            f'site:tiktok.com "{self.username}"',
            f'site:telegram.me "{self.username}"',
            f'site:linkedin.com "{self.username}"',
            f'site:github.com "{self.username}"',
            f'site:youtube.com "{self.username}"',
            f'site:pinterest.com "{self.username}"',
            f'inurl:"{self.username}" instagram',
            f'"{self.username}" "contact" OR "email" OR "phone"',
            f'"{self.username}" "location" OR "city" OR "address"',
            f'intitle:"{self.username}"',
        ]
        
        output_file = f"{self.output_dir}/reports/google_dorks.txt"
        
        with open(output_file, 'w') as f:
            f.write("="*60 + "\n")
            f.write(f"GOOGLE DORKS FOR: {self.username}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            f.write("Copy-paste these queries into Google:\n\n")
            
            for i, dork in enumerate(dorks, 1):
                f.write(f"{i}. {dork}\n")
                print_color(CYAN, f"    {i}. 🔍 {dork}")
                self.results["dorks"].append(dork)
        
        print_color(GREEN, f"\n    ✓ {len(dorks)} dorks saved to: {output_file}")
        return True

    def generate_final_report(self):
        """Create comprehensive HTML report"""
        print_color(CYAN, "\n═══ GENERATING FINAL REPORT ═══")
        
        html_report = f"""<!DOCTYPE html>
<html>
<head>
    <title>Instagram OSINT Report - {self.username}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #0a0a0a; color: #fff; }}
        .container {{ max-width: 1000px; margin: auto; }}
        h1 {{ color: #e1306c; border-bottom: 3px solid #e1306c; padding-bottom: 10px; }}
        h2 {{ color: #8a3ab9; margin-top: 30px; }}
        .section {{ background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 10px 0; }}
        .info {{ color: #ddd; line-height: 1.6; }}
        .label {{ color: #8a3ab9; font-weight: bold; }}
        .found {{ color: #4caf50; }}
        .not-found {{ color: #f44336; }}
        .url {{ color: #64b5f6; word-break: break-all; }}
        .dork {{ background: #2a2a2a; padding: 8px; border-radius: 4px; font-family: monospace; margin: 5px 0; }}
        .footer {{ margin-top: 40px; padding: 20px; background: #111; border-radius: 8px; text-align: center; color: #888; }}
        .gps-alert {{ background: #ff5722; color: white; padding: 15px; border-radius: 8px; font-weight: bold; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 Instagram OSINT Report</h1>
        <div class="section">
            <p><span class="label">Username:</span> @{self.username}</p>
            <p><span class="label">Scan Date:</span> {self.results['scan_time']}</p>
            <p><span class="label">Output Folder:</span> {self.output_dir}</p>
        </div>

        <h2>📊 Profile Information</h2>
        <div class="section">
            <p><span class="label">Full Name:</span> {self.results['profile_info'].get('full_name', 'N/A')}</p>
            <p><span class="label">Bio:</span> {self.results['profile_info'].get('bio', 'N/A')}</p>
            <p><span class="label">Followers:</span> {self.results['profile_info'].get('followers', 'N/A')}</p>
            <p><span class="label">Following:</span> {self.results['profile_info'].get('following', 'N/A')}</p>
            <p><span class="label">Posts:</span> {self.results['profile_info'].get('posts', 'N/A')}</p>
            <p><span class="label">Private Account:</span> {self.results['profile_info'].get('is_private', 'N/A')}</p>
            <p><span class="label">Verified:</span> {self.results['profile_info'].get('is_verified', 'N/A')}</p>
            <p><span class="label">External URL:</span> <span class="url">{self.results['profile_info'].get('external_url', 'N/A')}</span></p>
        </div>

        <h2>🌐 Cross-Platform Results</h2>
        <div class="section">
            {''.join(f'<p class="found">✅ <a href="{url}" target="_blank">{url}</a></p>' for url in self.results.get('cross_platform', ['<p class="not-found">No results found</p>']))}
        </div>

        <h2>📸 Reverse Image Search</h2>
        <div class="section">
            <p>Upload profile photo to these services:</p>
            <ul>
                <li><a href="https://images.google.com" target="_blank">🔍 Google Images</a></li>
                <li><a href="https://tineye.com" target="_blank">🔍 TinEye</a></li>
                <li><a href="https://yandex.com/images/" target="_blank">🔍 Yandex Images</a></li>
                <li><a href="https://pimeyes.com" target="_blank">🔍 PimEyes (Face Search)</a></li>
                <li><a href="https://facecheck.id" target="_blank">🔍 FaceCheck.ID</a></li>
            </ul>
            <p>Photo saved at: <code>{self.output_dir}/photos/profile_pic.jpg</code></p>
        </div>

        <h2>📱 Google Dork Queries</h2>
        <div class="section">
            {''.join(f'<div class="dork">🔍 {dork}</div>' for dork in self.results.get('dorks', []))}
        </div>

        <h2>🔧 Metadata Analysis</h2>
        <div class="section">
            {f'<div class="gps-alert">🔥 GPS DATA FOUND!</div>' if self.results.get('metadata', {}).get('gps_found') else '<p>No GPS data found</p>'}
            {''.join(f'<p><span class="label">{k}:</span> {v}</p>' for k, v in self.results.get('metadata', {}).items() if k != 'gps_found')}
        </div>

        <h2>⚠️ Recommended Actions</h2>
        <div class="section">
            <ol>
                <li><strong>Report to Instagram:</strong> Profile → 3 dots → Report → Impersonation</li>
                <li><strong>Cyber Crime Complaint:</strong> <a href="https://cybercrime.gov.in" target="_blank">cybercrime.gov.in</a> or call <strong>1930</strong></li>
                <li><strong>IP Tracking (if DM possible):</strong> Use <a href="https://grabify.link" target="_blank">Grabify.link</a> to track IP</li>
                <li><strong>More Investigation:</strong> Check Telegram, Reddit, Discord for same username</li>
            </ol>
        </div>

        <div class="footer">
            <p>Instagram OSINT Scanner v2.0 | Scan completed: {self.results['scan_time']}</p>
            <p>⚠️ For authorized security testing only</p>
        </div>
    </div>
</body>
</html>"""

        html_path = f"{self.output_dir}/reports/report.html"
        with open(html_path, 'w') as f:
            f.write(html_report)
        
        print_color(GREEN, f"    ✓ HTML Report: {html_path}")
        
        # Also save JSON results
        json_path = f"{self.output_dir}/reports/results.json"
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=4)
        print_color(GREEN, f"    ✓ JSON Results: {json_path}")
        
        # Open report in browser
        try:
            webbrowser.open(f"file://{os.path.abspath(html_path)}")
            print_color(GREEN, "    ✓ Report opened in browser!")
        except:
            print_color(YELLOW, f"    Open manually: {html_path}")
        
        return html_path

    def run(self):
        """Execute all scanning modules"""
        print_color(CYAN, BANNER_TEXT)
        print_color(YELLOW, f"[+] Target: @{self.username}")
        print_color(YELLOW, f"[+] Time: {self.results['scan_time']}")
        print("="*60)
        
        self.setup_directories()
        self.run_instaloader()
        self.run_sherlock()
        self.reverse_image_search()
        self.check_metadata()
        self.generate_google_dorks()
        report_path = self.generate_final_report()
        
        print("\n" + "="*60)
        print_color(GREEN, """
╔══════════════════════════════════════════════╗
║              ✅ SCAN COMPLETE!                ║
╠══════════════════════════════════════════════╣
║  All data saved in: """ + self.output_dir + """   ║
║  Open report: """ + report_path + """  ║
╚══════════════════════════════════════════════╝
        """)
        
        return self.results


# ================= MAIN EXECUTION =================
if __name__ == "__main__":
    # Clear screen
    os.system("clear || cls")
    
    print_color(CYAN, BANNER_TEXT)
    
    # Get username
    username = input(f"{BOLD}Enter Instagram username to scan: {END}").strip()
    
    if not username:
        print_color(RED, "[-] No username provided. Exiting.")
        sys.exit(1)
    
    # Clean username (remove @ and URL parts)
    username = username.replace("@", "").replace("https://", "").replace("instagram.com/", "").replace("/", "").strip()
    
    # Confirm
    print_color(YELLOW, f"\n[?] Target username: @{username}")
    confirm = input("Continue? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print_color(RED, "[-] Aborted by user.")
        sys.exit(0)
    
    # Run scanner
    scanner = InstagramOSINT(username)
    results = scanner.run()