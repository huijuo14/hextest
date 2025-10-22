import os
import time
import requests
import json
import tarfile
import gdown
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import logging
import re
import shutil
import glob
import sys
import threading
from flask import Flask, jsonify
import signal

# ========== CONFIGURATION ==========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8332116388:AAGbWaVQic0g7m5DU1USSXgXjP-bHKkPbsQ")
EMAIL = os.getenv("ADSHARE_EMAIL", "loginallapps@gmail.com")
PASSWORD = os.getenv("ADSHARE_PASSWORD", "@Sd2007123")

# File paths
PROFILE_BACKUP = "/tmp/firefox_profile_backup.tar.gz"
PROFILE_PATH = "/tmp/restored_firefox_profile"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/adshare_monitor.log')
    ]
)

# Flask app for health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        "status": "running",
        "service": "AdShare Monitor",
        "timestamp": time.time(),
        "browser_alive": monitor.browser_is_alive() if monitor else False
    })

@app.route('/status')
def status():
    return jsonify({
        "status": "healthy",
        "monitor_running": monitor.is_running if monitor else False,
        "uptime": time.time() - monitor.start_time if monitor else 0
    })

def start_flask_app():
    """Start Flask app in a separate thread"""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

class AdShareMonitor:
    def __init__(self):
        self.browser = None
        self.telegram_chat_id = None
        self.screenshot_counter = 0
        self.is_running = False
        self.start_time = time.time()
        
    def browser_is_alive(self):
        """Check if browser is responsive"""
        if not self.browser:
            return False
        try:
            self.browser.current_url
            return True
        except:
            return False

    def setup_telegram(self):
        """Setup Telegram bot communication"""
        try:
            logging.info("🤖 Setting up Telegram...")
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                bot_info = response.json()
                if bot_info['ok']:
                    logging.info(f"✅ Bot is working: @{bot_info['result']['username']}")
                    
                    # Get chat ID from last message
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        updates = response.json()
                        if updates['result']:
                            self.telegram_chat_id = updates['result'][-1]['message']['chat']['id']
                            logging.info(f"✅ Telegram Chat ID: {self.telegram_chat_id}")
                            
                            # Send startup message
                            message = "🚀 <b>AdShare Monitor Started on Koyeb</b>\n✅ Firefox is running headless\n🌐 Keeping adsha.re/surf active 24/7"
                            self.send_telegram(message)
                            return True
            return False
        except Exception as e:
            logging.error(f"❌ Telegram setup failed: {e}")
            return False

    def send_telegram(self, text):
        """Send message to Telegram"""
        if not self.telegram_chat_id:
            return False

        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {'chat_id': self.telegram_chat_id, 'text': text, 'parse_mode': 'HTML'}
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"❌ Telegram send failed: {e}")
            return False

    def install_firefox_dependencies(self):
        """Install Firefox and geckodriver on Koyeb"""
        logging.info("🔧 INSTALLING FIREFOX ON KOYEB...")
        
        try:
            # Update and install Firefox
            os.system('apt-get update -qq')
            os.system('apt-get install -y -qq firefox-esr xvfb')
            
            # Install geckodriver
            GECKODRIVER_VERSION = "0.34.0"
            GECKODRIVER_URL = f"https://github.com/mozilla/geckodriver/releases/download/v{GECKODRIVER_VERSION}/geckodriver-v{GECKODRIVER_VERSION}-linux64.tar.gz"
            
            os.system(f'wget -q {GECKODRIVER_URL} -O /tmp/geckodriver.tar.gz')
            os.system('tar -xzf /tmp/geckodriver.tar.gz -C /tmp/')
            os.system('chmod +x /tmp/geckodriver')
            os.system('mv /tmp/geckodriver /usr/local/bin/')
            
            logging.info("✅ Firefox and geckodriver installed successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Firefox installation failed: {e}")
            return False

    def setup_firefox_browser(self):
        """Setup Firefox browser in headless mode"""
        logging.info("🦊 SETTING UP FIREFOX BROWSER...")
        
        try:
            # Set up virtual display (optional but good practice)
            os.system('Xvfb :99 -screen 0 1920x1080x24 &')
            os.environ['DISPLAY'] = ':99'
            
            # Firefox options
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Performance optimizations for headless
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("browser.cache.offline.enable", False)
            options.set_preference("network.http.use-cache", False)
            
            # Start browser
            self.browser = webdriver.Firefox(options=options)
            
            # Set page load timeout
            self.browser.set_page_load_timeout(30)
            self.browser.implicitly_wait(10)
            
            logging.info("✅ Firefox browser started successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Browser setup failed: {e}")
            return False

    def navigate_to_adshare(self):
        """Navigate to adsha.re and login"""
        logging.info("🌐 NAVIGATING TO ADSHARE...")
        
        try:
            # Go to adsha.re surf page
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            logging.info(f"📍 Current URL: {self.browser.current_url}")
            
            # Check if login is needed
            if "login" in self.browser.current_url.lower():
                return self.perform_login()
            else:
                logging.info("✅ Already on surf page!")
                return True
                
        except Exception as e:
            logging.error(f"❌ Navigation failed: {e}")
            return False

    def perform_login(self):
        """Perform login to AdShare"""
        logging.info("🔐 PERFORMING LOGIN...")
        
        try:
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
            
            # Click login button
            login_btn = self.browser.find_element(By.CSS_SELECTOR, "a.button, button[type='submit']")
            login_btn.click()
            logging.info("🔄 Login button clicked")
            time.sleep(10)
            
            # Verify login success
            if "surf" in self.browser.current_url:
                logging.info("✅ Login successful!")
                self.send_telegram("✅ <b>Login Successful!</b>\n🌐 Now monitoring adsha.re/surf")
                return True
            else:
                logging.error("❌ Login failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False

    def keep_page_active(self):
        """Keep the surf page active and monitor credits"""
        logging.info("🎯 STARTING CONTINUOUS MONITORING...")
        
        self.is_running = True
        credit_check_count = 0
        
        try:
            while self.is_running:
                credit_check_count += 1
                
                # Refresh page every 10 minutes to keep session alive
                if credit_check_count % 12 == 0:  # 12 * 50 seconds = 10 minutes
                    logging.info("🔄 Refreshing page...")
                    try:
                        self.browser.refresh()
                        time.sleep(10)
                    except:
                        logging.warning("⚠️ Page refresh failed, reinitializing...")
                        self.reinitialize_browser()
                
                # Check credits every 30 minutes
                if credit_check_count % 36 == 0:  # 36 * 50 seconds = 30 minutes
                    credits = self.extract_credits()
                    logging.info(f"💰 Credits: {credits}")
                    
                    # Send Telegram update every 2 hours (4 * 30 minutes)
                    if credit_check_count % 144 == 0:
                        message = f"📊 <b>AdShare Update</b>\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}\n💰 {credits}\n🔄 System running smoothly on Koyeb"
                        self.send_telegram(message)
                
                # Take periodic screenshots (optional)
                if credit_check_count % 6 == 0:  # Every 5 minutes
                    self.take_screenshot()
                
                time.sleep(50)  # 50 second intervals
                
        except Exception as e:
            logging.error(f"❌ Monitoring error: {e}")
            self.is_running = False

    def extract_credits(self):
        """Extract credit information from page"""
        try:
            page_source = self.browser.page_source
            
            # Look for credit patterns
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

    def take_screenshot(self):
        """Take screenshot for debugging"""
        try:
            self.screenshot_counter += 1
            screenshot_path = f"/tmp/adshare_{self.screenshot_counter:04d}.png"
            self.browser.save_screenshot(screenshot_path)
            logging.info(f"📸 Screenshot saved: {screenshot_path}")
            
            # Cleanup old screenshots
            screenshots = sorted(glob.glob("/tmp/adshare_*.png"))
            if len(screenshots) > 10:
                for old_screenshot in screenshots[:-10]:
                    os.remove(old_screenshot)
                    
        except Exception as e:
            logging.error(f"❌ Screenshot failed: {e}")

    def reinitialize_browser(self):
        """Reinitialize browser if it crashes"""
        try:
            if self.browser:
                self.browser.quit()
        except:
            pass
        
        time.sleep(5)
        return self.setup_firefox_browser() and self.navigate_to_adshare()

    def run(self):
        """Main execution method"""
        logging.info("🚀 STARTING ADSHARE MONITOR ON KOYEB")
        
        # Start health check server
        flask_thread = threading.Thread(target=start_flask_app, daemon=True)
        flask_thread.start()
        logging.info("✅ Health check server started on port 8080")
        
        # Install dependencies
        if not self.install_firefox_dependencies():
            return False
        
        # Setup browser
        if not self.setup_firefox_browser():
            return False
        
        # Navigate and login
        if not self.navigate_to_adshare():
            return False
        
        # Setup Telegram
        self.setup_telegram()
        
        # Start monitoring
        logging.info("✅ ALL SYSTEMS GO! Starting continuous monitoring...")
        self.keep_page_active()
        
        return True

# Global instance
monitor = AdShareMonitor()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logging.info("🛑 Shutdown signal received...")
    monitor.is_running = False
    try:
        if monitor.browser:
            monitor.browser.quit()
    except:
        pass
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    success = monitor.run()
    if success:
        logging.info("🎉 AdShare monitor running successfully!")
    else:
        logging.error("💥 AdShare monitor failed to start")