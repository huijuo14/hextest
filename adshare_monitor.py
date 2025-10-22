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
        """Download profile"""
        logging.info("📥 Downloading Firefox profile...")
        
        if os.path.exists(PROFILE_BACKUP):
            os.remove(PROFILE_BACKUP)
        if os.path.exists(PROFILE_PATH):
            shutil.rmtree(PROFILE_PATH)
        os.makedirs(PROFILE_PATH, exist_ok=True)
        
        try:
            response = requests.get(PROFILE_URL, stream=True, timeout=60)
            with open(PROFILE_BACKUP, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if os.path.getsize(PROFILE_BACKUP) > 10000:
                logging.info("✅ Download successful")
                return True
        except Exception as e:
            logging.error(f"❌ Download failed: {e}")
        
        return False

    def extract_profile(self):
        """Extract profile - FIXED VERSION"""
        logging.info("📦 Extracting profile...")
        
        # Use system tar command (more reliable)
        result = os.system(f'tar -xzf "{PROFILE_BACKUP}" -C "{PROFILE_PATH}"')
        
        if result != 0:
            logging.error("❌ Extraction failed")
            return None
        
        # Check what was extracted
        extracted_items = os.listdir(PROFILE_PATH)
        logging.info(f"📁 Found {len(extracted_items)} items in profile")
        
        for item in extracted_items:
            logging.info(f"   📄 {item}")
        
        # Profile is directly in PROFILE_PATH (no subfolder)
        # This is CORRECT - the files are extracted directly to /tmp/firefox_profile/
        logging.info("✅ Profile extracted successfully")
        return PROFILE_PATH  # Use the directory directly

    def setup_browser_with_profile(self, profile_dir):
        """Setup Firefox with profile"""
        try:
            logging.info("🦊 Setting up Firefox with profile...")
            
            # Setup display
            os.system('Xvfb :99 -screen 0 1024x768x16 &')
            os.environ['DISPLAY'] = ':99'
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1024,768")
            
            # Memory optimizations
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("browser.tabs.remote.autostart", False)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            
            # Use profile directory directly
            options.add_argument(f"-profile")
            options.add_argument(profile_dir)
            
            self.browser = webdriver.Firefox(options=options)
            self.browser.set_page_load_timeout(30)
            self.browser.implicitly_wait(10)
            
            logging.info("✅ Firefox started successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Browser setup failed: {e}")
            return False

    def check_login_status(self):
        """Check if logged in"""
        try:
            logging.info("🌐 Navigating to AdShare...")
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            current_url = self.browser.current_url
            logging.info(f"📍 Current URL: {current_url}")
            
            if "surf" in current_url:
                logging.info("✅ Already logged in! On surf page.")
                return True
            elif "login" in current_url:
                logging.info("🔐 Need to login...")
                return self.perform_login()
            else:
                logging.warning("⚠️ On unknown page, trying surf again...")
                self.browser.get("https://adsha.re/surf")
                time.sleep(10)
                return "surf" in self.browser.current_url
                
        except Exception as e:
            logging.error(f"❌ Navigation failed: {e}")
            return False

    def perform_login(self):
        """Perform login"""
        try:
            logging.info("🔐 Attempting login...")
            
            # Find and fill email
            email_field = self.browser.find_element(By.CSS_SELECTOR, "input[name='mail']")
            email_field.clear()
            email_field.send_keys(EMAIL)
            logging.info("📧 Email entered")
            time.sleep(2)
            
            # Find and fill password
            password_field = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logging.info("🔑 Password entered")
            time.sleep(2)
            
            # Find and click login button
            login_btn = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_btn.click()
            logging.info("🔄 Login button clicked")
            time.sleep(10)
            
            # Check if login successful
            if "surf" in self.browser.current_url:
                logging.info("✅ Login successful!")
                return True
            else:
                logging.error("❌ Login failed - not redirected to surf")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False

    def monitor_loop(self):
        """Main monitoring loop"""
        logging.info("🎯 Starting continuous monitoring...")
        self.is_running = True
        iteration = 0
        
        while self.is_running:
            iteration += 1
            
            try:
                # Refresh every 15 minutes
                if iteration % 18 == 0:  # 18 * 50s = 15 minutes
                    logging.info("🔄 Refreshing page...")
                    self.browser.refresh()
                    time.sleep(10)
                
                # Simple keep-alive
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
    # Start health server
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    logging.info("✅ Health server started on port 8080")
    
    try:
        # Step 1: Download
        if not monitor.download_firefox_profile():
            logging.error("❌ Failed to download profile")
            exit(1)
        
        # Step 2: Extract
        profile_dir = monitor.extract_profile()
        if not profile_dir:
            logging.error("❌ Failed to extract profile")
            exit(1)
        
        # Step 3: Setup browser
        if not monitor.setup_browser_with_profile(profile_dir):
            logging.error("❌ Failed to setup browser")
            exit(1)
        
        # Step 4: Check login
        if not monitor.check_login_status():
            logging.error("❌ Failed to reach surf page")
            monitor.cleanup()
            exit(1)
        
        # Step 5: Start monitoring
        logging.info("🎉 ALL SYSTEMS GO! Starting 24/7 monitoring...")
        monitor.monitor_loop()
        
    except Exception as e:
        logging.error(f"💥 System failed: {e}")
    finally:
        monitor.cleanup()
        logging.info("🛑 Monitor stopped")