import os
import time
import requests
import tarfile
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import logging
import sys
import threading
from flask import Flask, jsonify
import shutil
import re

# ========== CONFIGURATION ==========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8332116388:AAGbWaVQic0g7m5DU1USSXgXjP-bHKkPbsQ")
EMAIL = os.getenv("ADSHARE_EMAIL", "loginallapps@gmail.com")
PASSWORD = os.getenv("ADSHARE_PASSWORD", "@Sd2007123")

# File paths - USING YOUR GITHUB TAR.GZ
PROFILE_BACKUP = "/tmp/firefox_profile.tar.gz"
PROFILE_PATH = "/tmp/firefox_profile"
PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_minimal.tar.gz"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)

class AdShareMonitor:
    def __init__(self):
        self.browser = None
        self.is_running = False
        
    def download_firefox_profile(self):
        """Download Firefox profile with proper verification"""
        logging.info("📥 Downloading minimal Firefox profile...")
        
        # Clean up existing files
        if os.path.exists(PROFILE_BACKUP):
            os.remove(PROFILE_BACKUP)
        if os.path.exists(PROFILE_PATH):
            shutil.rmtree(PROFILE_PATH)
            
        os.makedirs(PROFILE_PATH, exist_ok=True)
        
        try:
            logging.info("🔄 Downloading from GitHub...")
            
            # Method 1: Use requests with stream to verify download
            response = requests.get(PROFILE_URL, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            logging.info(f"📦 File size: {total_size} bytes")
            
            with open(PROFILE_BACKUP, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify file size
            if os.path.exists(PROFILE_BACKUP):
                downloaded_size = os.path.getsize(PROFILE_BACKUP)
                logging.info(f"✅ Download complete: {downloaded_size} bytes")
                
                if downloaded_size > 10000:
                    logging.info("✅ File downloaded successfully")
                    return True
                else:
                    logging.error(f"❌ File too small: {downloaded_size} bytes")
                    return False
                    
        except Exception as e:
            logging.error(f"❌ Download failed: {e}")
            # Try wget as fallback
            try:
                logging.info("🔄 Trying wget fallback...")
                result = os.system(f'wget -O "{PROFILE_BACKUP}" "{PROFILE_URL}" --timeout=60 --tries=2')
                if result == 0 and os.path.exists(PROFILE_BACKUP) and os.path.getsize(PROFILE_BACKUP) > 10000:
                    file_size = os.path.getsize(PROFILE_BACKUP)
                    logging.info(f"✅ Wget download: {file_size} bytes")
                    return True
            except Exception as e2:
                logging.error(f"❌ Wget also failed: {e2}")
        
        logging.error("❌ All download attempts failed")
        return False

    def extract_profile(self):
        """Extract from double-compressed tar.gz"""
        try:
            logging.info("📦 Extracting double-compressed profile...")
            
            # First extract: .tar.gz to .tar
            temp_tar = "/tmp/firefox_profile.tar"
            
            with tarfile.open(PROFILE_BACKUP, 'r:gz') as tar_gz:
                # List contents first to see what's inside
                members = tar_gz.getmembers()
                logging.info(f"📁 First layer contains {len(members)} items")
                for member in members:
                    logging.info(f"   - {member.name}")
                
                # Extract the .tar file
                tar_gz.extractall("/tmp")
                logging.info("✅ First extraction: .tar.gz to .tar")
            
            # Find the extracted .tar file
            tar_files = [f for f in os.listdir("/tmp") if f.endswith('.tar')]
            if tar_files:
                temp_tar = f"/tmp/{tar_files[0]}"
                logging.info(f"📦 Found tar file: {tar_files[0]}")
            else:
                logging.error("❌ No .tar file found after first extraction")
                return None
            
            # Second extract: .tar to actual files
            with tarfile.open(temp_tar, 'r') as tar:
                members = tar.getmembers()
                logging.info(f"📁 Second layer contains {len(members)} files")
                tar.extractall(PROFILE_PATH)
                logging.info("✅ Second extraction: .tar to files")
            
            # Clean up temp file
            if os.path.exists(temp_tar):
                os.remove(temp_tar)
            
            extracted_items = os.listdir(PROFILE_PATH)
            logging.info(f"📁 Final extracted items: {extracted_items}")
            
            if not extracted_items:
                logging.error("❌ No files extracted")
                return None
                
            # Find profile directory
            profile_dir = None
            for item in extracted_items:
                item_path = os.path.join(PROFILE_PATH, item)
                if os.path.isdir(item_path):
                    profile_dir = item_path
                    break
            
            if not profile_dir:
                profile_dir = PROFILE_PATH
            
            logging.info(f"✅ Profile ready at: {profile_dir}")
            return profile_dir
            
        except Exception as e:
            logging.error(f"❌ Double extraction failed: {e}")
            return None

    def setup_browser_with_profile(self, profile_dir):
        """Setup Firefox with minimal profile"""
        try:
            logging.info("🦊 Setting up Firefox with minimal profile...")
            
            # Set up virtual display
            os.system('Xvfb :99 -screen 0 800x600x16 &')
            os.environ['DISPLAY'] = ':99'
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=800,600")
            
            # Memory optimizations
            options.set_preference("browser.startup.homepage", "about:blank")
            options.set_preference("browser.startup.page", 0)
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("browser.tabs.remote.autostart", False)
            
            # Keep extensions enabled
            options.set_preference("extensions.autoDisableScopes", 0)
            
            # Disable cache
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            
            # Use the profile
            options.add_argument(f"-profile")
            options.add_argument(profile_dir)
            
            # Start browser
            self.browser = webdriver.Firefox(options=options)
            self.browser.set_page_load_timeout(45)
            self.browser.implicitly_wait(15)
            
            logging.info("✅ Firefox started with minimal profile!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Browser setup failed: {e}")
            return False

    def check_login_status(self):
        """Check if we're logged in using the profile"""
        try:
            logging.info("🌐 Checking login status...")
            
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            current_url = self.browser.current_url
            logging.info(f"📍 Current URL: {current_url}")
            
            if "surf" in current_url:
                logging.info("✅ Profile has active session! On surf page.")
                return True
            elif "login" in current_url:
                logging.info("🔐 Profile needs login...")
                return self.perform_login()
            else:
                self.browser.get("https://adsha.re/surf")
                time.sleep(10)
                return "surf" in self.browser.current_url
                
        except Exception as e:
            logging.error(f"❌ Navigation failed: {e}")
            return False

    def perform_login(self):
        """Perform login"""
        try:
            logging.info("🔐 Performing login...")
            
            # Email field
            email_selectors = ["input[name='mail']", "input[type='email']"]
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if email_field:
                email_field.send_keys(EMAIL)
                logging.info("📧 Email entered")
                time.sleep(2)
            
            # Password field
            password_field = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.send_keys(PASSWORD)
            logging.info("🔑 Password entered")
            time.sleep(2)
            
            # Login button
            login_btn = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_btn.click()
            logging.info("🔄 Login button clicked")
            time.sleep(10)
            
            if "surf" in self.browser.current_url:
                logging.info("✅ Login successful!")
                return True
            else:
                logging.error("❌ Login failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False

    def monitor_loop(self):
        """Main monitoring loop"""
        logging.info("🎯 Starting monitoring...")
        self.is_running = True
        iteration = 0
        
        while self.is_running:
            iteration += 1
            
            try:
                # Refresh every 20 minutes
                if iteration % 24 == 0:
                    logging.info("🔄 Refreshing page...")
                    try:
                        self.browser.refresh()
                        time.sleep(10)
                    except Exception as e:
                        logging.warning(f"⚠️ Refresh failed: {e}")
                
                time.sleep(50)
                
            except Exception as e:
                logging.error(f"❌ Monitoring error: {e}")
                break
        
        self.is_running = False

    def cleanup(self):
        """Cleanup"""
        try:
            if self.browser:
                self.browser.quit()
        except:
            pass

monitor = AdShareMonitor()

@app.route('/')
def health_check():
    return jsonify({
        "status": "running", 
        "browser_alive": monitor.browser is not None,
        "monitor_running": monitor.is_running
    })

@app.route('/health')
def health():
    return "OK", 200

def start_flask():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    logging.info("✅ Health server started")
    
    try:
        if not monitor.download_firefox_profile():
            logging.error("❌ Failed to download profile")
            exit(1)
        
        profile_dir = monitor.extract_profile()
        if not profile_dir:
            logging.error("❌ Failed to extract profile")
            exit(1)
        
        if not monitor.setup_browser_with_profile(profile_dir):
            logging.error("❌ Failed to setup browser")
            exit(1)
        
        if not monitor.check_login_status():
            logging.error("❌ Failed to reach surf page")
            monitor.cleanup()
            exit(1)
        
        logging.info("✅ All systems go! Starting monitoring...")
        monitor.monitor_loop()
        
    except Exception as e:
        logging.error(f"💥 Main execution failed: {e}")
    finally:
        monitor.cleanup()
        logging.info("🛑 Monitor stopped")