import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import sys
import threading
from flask import Flask, jsonify

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8332116388:AAGbWaVQic0g7m5DU1USSXgXjP-bHKkPbsQ")
EMAIL = os.getenv("ADSHARE_EMAIL", "loginallapps@gmail.com")
PASSWORD = os.getenv("ADSHARE_PASSWORD", "@Sd2007123")

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
        
    def setup_browser(self):
        """Setup Firefox with memory optimizations"""
        try:
            logging.info("🦊 Setting up Firefox browser...")
            
            # Set up virtual display
            os.system('Xvfb :99 -screen 0 800x600x16 &')
            os.environ['DISPLAY'] = ':99'
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=800,600")
            
            # CRITICAL: Memory optimizations for 512MB RAM
            options.set_preference("browser.tabs.remote.autostart", False)
            options.set_preference("browser.tabs.remote.autostart.2", False)
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("browser.sessionstore.resume_from_crash", False)
            options.set_preference("browser.sessionstore.max_resumed_crashes", 0)
            options.set_preference("browser.startup.page", 0)  # Blank page
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("browser.cache.offline.enable", False)
            options.set_preference("network.http.use-cache", False)
            
            self.browser = webdriver.Firefox(options=options)
            self.browser.set_page_load_timeout(30)
            self.browser.implicitly_wait(10)
            
            logging.info("✅ Firefox browser started successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Browser setup failed: {e}")
            return False

    def smart_login(self):
        """Smart login that handles different password field scenarios"""
        try:
            logging.info("🌐 Navigating to AdShare...")
            self.browser.get("https://adsha.re/surf")
            time.sleep(8)
            
            current_url = self.browser.current_url
            logging.info(f"📍 Current URL: {current_url}")
            
            # If we're not on surf page, try login
            if "surf" not in current_url:
                logging.info("🔐 Attempting login...")
                
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
                    # Take screenshot for debugging
                    try:
                        self.browser.save_screenshot("/tmp/login_page.png")
                        logging.info("📸 Saved screenshot to /tmp/login_page.png")
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
                    "a.button[onclick*='submit']",
                    "button:contains('Login')",
                    "input[value*='Login']"
                ]
                
                login_btn = None
                for selector in login_selectors:
                    try:
                        if "contains" in selector:
                            # Simple text-based search
                            buttons = self.browser.find_elements(By.TAG_NAME, "button")
                            for btn in buttons:
                                if "login" in btn.text.lower():
                                    login_btn = btn
                                    break
                        else:
                            login_btn = self.browser.find_element(By.CSS_SELECTOR, selector)
                        if login_btn:
                            break
                    except:
                        continue
                
                if login_btn:
                    login_btn.click()
                    logging.info("🔄 Login button clicked")
                    time.sleep(10)
                    
                    # Check if login successful
                    if "surf" in self.browser.current_url:
                        logging.info("✅ Login successful!")
                        return True
                    else:
                        logging.error("❌ Login failed - not redirected to surf page")
                        return False
                else:
                    logging.error("❌ Could not find login button")
                    return False
            else:
                logging.info("✅ Already on surf page!")
                return True
                
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False

    def simple_monitor(self):
        """Simple monitoring loop with memory conservation"""
        logging.info("🎯 Starting simple monitoring...")
        self.is_running = True
        iteration = 0
        
        while self.is_running:
            iteration += 1
            
            try:
                # Refresh every 20 minutes (less frequent to save memory)
                if iteration % 24 == 0:  # 24 * 50s = 20 minutes
                    logging.info("🔄 Refreshing page...")
                    try:
                        self.browser.refresh()
                        time.sleep(8)
                        
                        # Check if we got logged out
                        if "login" in self.browser.current_url:
                            logging.info("🔐 Session expired, re-logging in...")
                            if not self.smart_login():
                                logging.error("❌ Re-login failed")
                                break
                    except Exception as e:
                        logging.warning(f"⚠️ Refresh failed: {e}")
                
                # Simple keep-alive - just sleep
                time.sleep(50)
                
            except Exception as e:
                logging.error(f"❌ Monitoring error: {e}")
                break
        
        self.is_running = False

    def cleanup(self):
        """Cleanup browser"""
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
        "service": "AdShare Monitor"
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
    
    # Setup and start monitor
    if monitor.setup_browser():
        if monitor.smart_login():
            logging.info("✅ Monitor started successfully!")
            monitor.simple_monitor()
        else:
            logging.error("❌ Login failed")
            monitor.cleanup()
    else:
        logging.error("❌ Browser setup failed")
    
    logging.info("🛑 Monitor stopped")
