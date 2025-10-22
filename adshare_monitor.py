import os
import time
import requests
import tarfile
import gdown
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

# Google Drive URLs for Firefox profile
PROFILE_URLS = [
    "https://drive.google.com/uc?id=14FV2eLutUpJ9TdUrhLEvLFflRvAdCIG",
    "https://drive.google.com/file/d/1XRb3wnpH8qq4BX06IhqRtvAaU5NI7H-2/view?usp=drivesdk",
    "https://drive.google.com/file/d/1uxjgJ3wVMh5JTnHBd8r6MnXgixLufraM/view?usp=drivesdk"
]

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
        """Download Firefox profile from Google Drive"""
        logging.info("📥 Downloading Firefox profile from Google Drive...")
        
        # Clean up existing files
        if os.path.exists(PROFILE_BACKUP):
            os.remove(PROFILE_BACKUP)
        if os.path.exists(PROFILE_PATH):
            shutil.rmtree(PROFILE_PATH)
            
        os.makedirs(PROFILE_PATH, exist_ok=True)
        
        for url in PROFILE_URLS:
            try:
                logging.info(f"🔄 Trying URL: {url}")
                
                # Extract file ID from URL
                file_id = None
                if '/uc?id=' in url:
                    file_id = url.split('/uc?id=')[1]
                elif '/file/d/' in url:
                    file_id = url.split('/file/d/')[1].split('/')[0]
                elif '/id=' in url:
                    file_id = url.split('/id=')[1]
                
                if file_id:
                    download_url = f'https://drive.google.com/uc?id={file_id}'
                    logging.info(f"📦 Downloading profile with file ID: {file_id}")
                    
                    gdown.download(download_url, PROFILE_BACKUP, quiet=False)
                    
                    if os.path.exists(PROFILE_BACKUP) and os.path.getsize(PROFILE_BACKUP) > 1000000:
                        file_size = os.path.getsize(PROFILE_BACKUP)
                        logging.info(f"✅ Profile downloaded: {file_size} bytes")
                        return True
                        
            except Exception as e:
                logging.error(f"❌ Download failed: {e}")
                continue
                
        logging.error("❌ All download attempts failed")
        return False

    def extract_profile(self):
        """Extract the Firefox profile"""
        try:
            logging.info("📦 Extracting Firefox profile...")
            
            with tarfile.open(PROFILE_BACKUP, 'r:gz') as tar:
                tar.extractall(PROFILE_PATH)
            
            # Check what was extracted
            extracted_items = os.listdir(PROFILE_PATH)
            logging.info(f"📁 Extracted items: {extracted_items}")
            
            # Look for profile directories
            profile_dir = None
            for item in extracted_items:
                item_path = os.path.join(PROFILE_PATH, item)
                if os.path.isdir(item_path):
                    if 'default' in item or 'release' in item or 'profile' in item:
                        profile_dir = item_path
                        break
            
            if not profile_dir and extracted_items:
                # Use first directory found
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

    def setup_browser_with_profile(self, profile_dir):
        """Setup Firefox with custom profile"""
        try:
            logging.info("🦊 Setting up Firefox with custom profile...")
            
            # Set up virtual display
            os.system('Xvfb :99 -screen 0 1024x768x16 &')
            os.environ['DISPLAY'] = ':99'
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1024,768")
            
            # Use the custom profile
            options.add_argument(f"-profile")
            options.add_argument(profile_dir)
            
            # Memory optimizations
            options.set_preference("browser.tabs.remote.autostart", False)
            options.set_preference("browser.tabs.remote.autostart.2", False)
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("browser.sessionstore.resume_from_crash", False)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            
            self.browser = webdriver.Firefox(options=options)
            self.browser.set_page_load_timeout(30)
            self.browser.implicitly_wait(10)
            
            logging.info("✅ Firefox started with custom profile!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Browser setup failed: {e}")
            return False

    def check_login_status(self):
        """Check if we're logged in and navigate to surf page"""
        try:
            logging.info("🌐 Checking login status...")
            
            # First, try going directly to surf page
            self.browser.get("https://adsha.re/surf")
            time.sleep(8)
            
            current_url = self.browser.current_url
            logging.info(f"📍 Current URL: {current_url}")
            
            # If we're on surf page, we're good
            if "surf" in current_url:
                logging.info("✅ Already logged in and on surf page!")
                return True
                
            # If we're on login page, try to login
            elif "login" in current_url:
                logging.info("🔐 Profile needs login...")
                return self.perform_login()
                
            else:
                # Some other page, try to navigate to surf
                logging.info("🔄 Navigating to surf page...")
                self.browser.get("https://adsha.re/surf")
                time.sleep(8)
                return "surf" in self.browser.current_url
                
        except Exception as e:
            logging.error(f"❌ Navigation failed: {e}")
            return False

    def perform_login(self):
        """Perform login with multiple selector attempts"""
        try:
            logging.info("🔐 Performing login...")
            
            # Try multiple email field selectors
            email_selectors = [
                "input[name='mail']",
                "input[type='email']", 
                "input[name='email']",
                "input[id*='mail']",
                "input[id*='email']"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if email_field:
                email_field.clear()
                email_field.send_keys(EMAIL)
                logging.info("📧 Email entered")
                time.sleep(2)
            else:
                logging.error("❌ Could not find email field")
                return False
            
            # Try multiple password field selectors
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[name='pass']",
                "input[id*='password']",
                "input[id*='pass']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not password_field:
                logging.error("❌ Could not find password field")
                # Save page source for debugging
                try:
                    with open("/tmp/login_page.html", "w") as f:
                        f.write(self.browser.page_source)
                    logging.info("📄 Saved page source to /tmp/login_page.html")
                except:
                    pass
                return False
            
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logging.info("🔑 Password entered")
            time.sleep(2)
            
            # Try multiple login button selectors
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[onclick*='submit']",
                ".login-btn",
                ".submit-btn",
                "a.button[onclick*='submit']"
            ]
            
            login_btn = None
            for selector in login_selectors:
                try:
                    login_btn = self.browser.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            # If no button found by CSS, try by text
            if not login_btn:
                try:
                    buttons = self.browser.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        if "login" in btn.text.lower() or "sign in" in btn.text.lower():
                            login_btn = btn
                            break
                except:
                    pass
            
            if login_btn:
                login_btn.click()
                logging.info("🔄 Login button clicked")
                time.sleep(10)
                
                # Check if login successful
                if "surf" in self.browser.current_url:
                    logging.info("✅ Login successful!")
                    return True
                else:
                    logging.error("❌ Login failed - not on surf page")
                    return False
            else:
                logging.error("❌ Could not find login button")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False

    def monitor_loop(self):
        """Main monitoring loop"""
        logging.info("🎯 Starting monitoring loop...")
        self.is_running = True
        iteration = 0
        
        while self.is_running:
            iteration += 1
            
            try:
                # Refresh page every 15 minutes to keep session alive
                if iteration % 18 == 0:  # 18 * 50s = 15 minutes
                    logging.info("🔄 Refreshing page...")
                    try:
                        self.browser.refresh()
                        time.sleep(8)
                        
                        # Check if we got logged out
                        if "login" in self.browser.current_url:
                            logging.info("🔐 Session expired, re-logging in...")
                            if not self.perform_login():
                                logging.error("❌ Re-login failed, restarting...")
                                break
                    except Exception as e:
                        logging.warning(f"⚠️ Refresh failed: {e}")
                
                # Extract credits every 30 minutes
                if iteration % 36 == 0:
                    credits = self.extract_credits()
                    logging.info(f"💰 Current credits: {credits}")
                
                time.sleep(50)  # 50 second intervals
                
            except Exception as e:
                logging.error(f"❌ Monitoring error: {e}")
                break
        
        self.is_running = False

    def extract_credits(self):
        """Extract credit information from page"""
        try:
            page_source = self.browser.page_source
            
            patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*Credits',
                r'Credits.*?(\d{1,3}(?:,\d{3})*)',
                r'balance.*?(\d[\d,]*)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    return f"{matches[0]} Credits"
            
            return "Credits not found"
            
        except Exception as e:
            return f"Error: {str(e)}"

    def cleanup(self):
        """Cleanup resources"""
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
        "monitor_running": monitor.is_running,
        "service": "AdShare Monitor with Custom Profile"
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
        # Step 1: Download Firefox profile
        if not monitor.download_firefox_profile():
            logging.error("❌ Failed to download profile")
            exit(1)
        
        # Step 2: Extract profile
        profile_dir = monitor.extract_profile()
        if not profile_dir:
            logging.error("❌ Failed to extract profile")
            exit(1)
        
        # Step 3: Setup browser with profile
        if not monitor.setup_browser_with_profile(profile_dir):
            logging.error("❌ Failed to setup browser with profile")
            exit(1)
        
        # Step 4: Check login and navigate to surf
        if not monitor.check_login_status():
            logging.error("❌ Failed to login/navigate to surf")
            monitor.cleanup()
            exit(1)
        
        # Step 5: Start monitoring
        logging.info("✅ All systems go! Starting monitoring...")
        monitor.monitor_loop()
        
    except Exception as e:
        logging.error(f"💥 Main execution failed: {e}")
    finally:
        monitor.cleanup()
        logging.info("🛑 Monitor stopped")
