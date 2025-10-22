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
        """Download with multiple fallbacks"""
        logging.info("📥 Downloading Firefox profile...")
        
        if os.path.exists(PROFILE_BACKUP):
            os.remove(PROFILE_BACKUP)
        if os.path.exists(PROFILE_PATH):
            shutil.rmtree(PROFILE_PATH)
        os.makedirs(PROFILE_PATH, exist_ok=True)
        
        # Try multiple download methods
        methods = [
            self._download_requests,
            self._download_wget,
            self._download_curl
        ]
        
        for method in methods:
            if method():
                return True
        
        logging.error("❌ All download methods failed")
        return False

    def _download_requests(self):
        """Download using requests"""
        try:
            logging.info("🔄 Trying requests...")
            response = requests.get(PROFILE_URL, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(PROFILE_BACKUP, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.getsize(PROFILE_BACKUP) > 10000:
                logging.info("✅ Requests download successful")
                return True
        except Exception as e:
            logging.error(f"❌ Requests failed: {e}")
            return False

    def _download_wget(self):
        """Download using wget"""
        try:
            logging.info("🔄 Trying wget...")
            result = os.system(f'wget -O "{PROFILE_BACKUP}" "{PROFILE_URL}" --timeout=30 -q')
            if result == 0 and os.path.getsize(PROFILE_BACKUP) > 10000:
                logging.info("✅ Wget download successful")
                return True
        except:
            return False

    def _download_curl(self):
        """Download using curl"""
        try:
            logging.info("🔄 Trying curl...")
            result = os.system(f'curl -L -o "{PROFILE_BACKUP}" "{PROFILE_URL}" --connect-timeout 30 -s')
            if result == 0 and os.path.getsize(PROFILE_BACKUP) > 10000:
                logging.info("✅ Curl download successful")
                return True
        except:
            return False

    def extract_profile(self):
        """Extract using system commands"""
        logging.info("📦 Extracting profile...")
        
        # Method 1: System tar with verbose output
        logging.info("🔄 Trying system tar...")
        result = os.system(f'tar -xzvf "{PROFILE_BACKUP}" -C "{PROFILE_PATH}"')
        
        if result == 0:
            logging.info("✅ System extraction successful")
        else:
            # Method 2: Force extraction
            logging.info("🔄 Trying forced extraction...")
            result = os.system(f'tar -xzf "{PROFILE_BACKUP}" -C "{PROFILE_PATH}" --force-local')
            if result != 0:
                logging.error("❌ All extraction methods failed")
                return None
        
        # Check results
        extracted_items = os.listdir(PROFILE_PATH)
        logging.info(f"📁 Extracted {len(extracted_items)} items")
        
        if not extracted_items:
            logging.error("❌ No files extracted")
            return None
            
        # Find profile directory
        for item in extracted_items:
            item_path = os.path.join(PROFILE_PATH, item)
            if os.path.isdir(item_path):
                logging.info(f"✅ Using profile: {item}")
                return item_path
        
        logging.info("✅ Using root extraction directory")
        return PROFILE_PATH

    def setup_browser_with_profile(self, profile_dir):
        """Setup Firefox browser"""
        try:
            logging.info("🦊 Setting up Firefox...")
            
            os.system('Xvfb :99 -screen 0 800x600x16 &')
            os.environ['DISPLAY'] = ':99'
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=800,600")
            
            # Memory optimizations
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("browser.tabs.remote.autostart", False)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            
            # Use profile
            options.add_argument(f"-profile")
            options.add_argument(profile_dir)
            
            self.browser = webdriver.Firefox(options=options)
            self.browser.set_page_load_timeout(30)
            
            logging.info("✅ Firefox started successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Browser setup failed: {e}")
            return False

    def check_login_status(self):
        """Check login status"""
        try:
            logging.info("🌐 Navigating to AdShare...")
            self.browser.get("https://adsha.re/surf")
            time.sleep(8)
            
            current_url = self.browser.current_url
            logging.info(f"📍 Current URL: {current_url}")
            
            if "surf" in current_url:
                logging.info("✅ Already on surf page!")
                return True
            elif "login" in current_url:
                logging.info("🔐 Attempting login...")
                return self.perform_login()
            else:
                return False
                
        except Exception as e:
            logging.error(f"❌ Navigation failed: {e}")
            return False

    def perform_login(self):
        """Perform login"""
        try:
            # Simple login attempt
            email_field = self.browser.find_element(By.CSS_SELECTOR, "input[name='mail']")
            email_field.send_keys(EMAIL)
            
            password_field = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.send_keys(PASSWORD)
            
            login_btn = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            
            time.sleep(10)
            return "surf" in self.browser.current_url
            
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False

    def monitor_loop(self):
        """Main monitoring loop"""
        logging.info("🎯 Starting monitoring loop...")
        self.is_running = True
        
        while self.is_running:
            try:
                # Keep alive - simple refresh every 15 minutes
                self.browser.refresh()
                time.sleep(900)  # 15 minutes
            except Exception as e:
                logging.error(f"❌ Monitoring error: {e}")
                break
        
        self.is_running = False

    def cleanup(self):
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass

monitor = AdShareMonitor()

@app.route('/')
def health_check():
    return jsonify({"status": "running", "browser_alive": monitor.browser is not None})

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
        # Download
        if not monitor.download_firefox_profile():
            exit(1)
        
        # Extract
        profile_dir = monitor.extract_profile()
        if not profile_dir:
            exit(1)
        
        # Setup browser
        if not monitor.setup_browser_with_profile(profile_dir):
            exit(1)
        
        # Check login
        if not monitor.check_login_status():
            exit(1)
        
        # Start monitoring
        logging.info("✅ ALL SYSTEMS GO! Starting monitor...")
        monitor.monitor_loop()
        
    except Exception as e:
        logging.error(f"💥 System failed: {e}")
    finally:
        monitor.cleanup()