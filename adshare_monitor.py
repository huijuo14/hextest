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

# File paths
PROFILE_BACKUP = "/tmp/firefox_profile.tar.gz"
PROFILE_PATH = "/tmp/firefox_profile"

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
        """Download Firefox profile from GitHub"""
        logging.info("📥 Downloading Firefox profile...")
        
        # Clean up existing files
        if os.path.exists(PROFILE_BACKUP):
            os.remove(PROFILE_BACKUP)
        if os.path.exists(PROFILE_PATH):
            shutil.rmtree(PROFILE_PATH)
            
        os.makedirs(PROFILE_PATH, exist_ok=True)
        
        # Use your GitHub direct download URL
        profile_url = "YOUR_GITHUB_DIRECT_DOWNLOAD_URL_HERE"
        
        try:
            logging.info("🔄 Downloading profile...")
            result = os.system(f'wget -O "{PROFILE_BACKUP}" "{profile_url}" --timeout=60 --tries=3')
            
            if result == 0 and os.path.exists(PROFILE_BACKUP) and os.path.getsize(PROFILE_BACKUP) > 1000000:
                file_size = os.path.getsize(PROFILE_BACKUP)
                logging.info(f"✅ Profile downloaded: {file_size} bytes")
                return True
                
        except Exception as e:
            logging.error(f"❌ Download failed: {e}")
        
        logging.error("❌ Download failed")
        return False

    def extract_profile(self):
        """Extract the Firefox profile"""
        try:
            logging.info("📦 Extracting Firefox profile...")
            
            with tarfile.open(PROFILE_BACKUP, 'r:gz') as tar:
                tar.extractall(PROFILE_PATH)
            
            extracted_items = os.listdir(PROFILE_PATH)
            logging.info(f"📁 Extracted items: {extracted_items}")
            
            # Find profile directory
            profile_dir = None
            for item in extracted_items:
                item_path = os.path.join(PROFILE_PATH, item)
                if os.path.isdir(item_path):
                    profile_dir = item_path
                    break
            
            if profile_dir:
                logging.info(f"✅ Profile extracted to: {profile_dir}")
                return profile_dir
            else:
                logging.error("❌ No profile directory found")
                return None
                
        except Exception as e:
            logging.error(f"❌ Extraction failed: {e}")
            return None

    def setup_browser_with_profile_optimized(self, profile_dir):
        """Setup Firefox with profile - MEMORY OPTIMIZED"""
        try:
            logging.info("🦊 Setting up Firefox with profile (optimized for 512MB RAM)...")
            
            # Set up virtual display
            os.system('Xvfb :99 -screen 0 800x600x16 &')
            os.environ['DISPLAY'] = ':99'
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=800,600")  # Smaller window
            
            # CRITICAL MEMORY OPTIMIZATIONS
            options.set_preference("browser.startup.homepage", "about:blank")
            options.set_preference("browser.startup.page", 0)
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("dom.ipc.processCount.webIsolated", 1)
            options.set_preference("browser.tabs.remote.autostart", False)
            options.set_preference("browser.tabs.remote.autostart.2", False)
           
            
            # Disable all unnecessary features
            options.set_preference("javascript.options.mem.max", 51200)  # 50MB max JS memory
            options.set_preference("browser.sessionstore.interval", 300000)  # 5 minutes
            options.set_preference("browser.sessionstore.max_resumed_crashes", 0)
            options.set_preference("browser.sessionstore.resume_from_crash", False)
            
            # Disable cache completely
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("browser.cache.offline.enable", False)
            options.set_preference("network.http.use-cache", False)
            
            # Use the profile
            options.add_argument(f"-profile")
            options.add_argument(profile_dir)
            
            # Start browser with minimal resources
            self.browser = webdriver.Firefox(options=options)
            
            # Minimal timeouts
            self.browser.set_page_load_timeout(45)
            self.browser.implicitly_wait(15)
            self.browser.set_script_timeout(30)
            
            logging.info("✅ Firefox started with optimized memory settings!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Browser setup failed: {e}")
            return False

    def check_login_status(self):
        """Check if we're logged in using the profile"""
        try:
            logging.info("🌐 Checking login status with profile...")
            
            # Try going to surf page
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)  # Give more time for profile to load
            
            current_url = self.browser.current_url
            logging.info(f"📍 Current URL: {current_url}")
            
            # If profile has active session, we should be on surf page
            if "surf" in current_url:
                logging.info("✅ Profile has active session! On surf page.")
                return True
                
            # If login needed, try login
            elif "login" in current_url:
                logging.info("🔐 Profile needs login...")
                return self.perform_login()
                
            else:
                logging.info("🔄 Navigating directly to surf...")
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
            
            # Check success
            if "surf" in self.browser.current_url:
                logging.info("✅ Login successful!")
                return True
            else:
                logging.error("❌ Login failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False

    def simple_monitor(self):
        """Simple monitoring to save memory"""
        logging.info("🎯 Starting memory-optimized monitoring...")
        self.is_running = True
        iteration = 0
        
        while self.is_running:
            iteration += 1
            
            try:
                # Refresh every 20 minutes (less frequent to save memory)
                if iteration % 24 == 0:
                    logging.info("🔄 Refreshing page...")
                    try:
                        self.browser.refresh()
                        time.sleep(10)
                    except Exception as e:
                        logging.warning(f"⚠️ Refresh failed: {e}")
                
                # Minimal operation - just sleep
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
    logging.info("✅ Health server started")
    
    try:
        # Download profile
        if not monitor.download_firefox_profile():
            logging.error("❌ Failed to download profile")
            exit(1)
        
        # Extract profile
        profile_dir = monitor.extract_profile()
        if not profile_dir:
            logging.error("❌ Failed to extract profile")
            exit(1)
        
        # Setup browser with memory optimizations
        if not monitor.setup_browser_with_profile_optimized(profile_dir):
            logging.error("❌ Failed to setup browser")
            exit(1)
        
        # Check login
        if not monitor.check_login_status():
            logging.error("❌ Failed to reach surf page")
            monitor.cleanup()
            exit(1)
        
        # Start monitoring
        logging.info("✅ All systems go! Starting monitoring...")
        monitor.simple_monitor()
        
    except Exception as e:
        logging.error(f"💥 Main execution failed: {e}")
    finally:
        monitor.cleanup()
        logging.info("🛑 Monitor stopped")