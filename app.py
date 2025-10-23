#!/usr/bin/env python3
"""
Fixed AdShare Monitor with Profile Restoration
"""

import os
import time
import logging
import threading
import tarfile
import requests
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import psutil

# ========== CONFIGURATION ==========
EMAIL = "loginallapps@gmail.com"
PASSWORD = "@Sd2007123"
PROFILE_PATH = "/app/firefox_profile"
PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_profile.tar.1.gz"

app = Flask(__name__)

class KoyebAdShareMonitor:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        self.status = "Initializing"
        self.start_time = time.time()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def download_profile(self):
        """Download and extract profile with error handling"""
        self.logger.info("📥 Downloading Firefox profile...")
        
        try:
            # Download profile
            response = requests.get(PROFILE_URL, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save compressed profile
            temp_path = "/app/profile_temp.tar.gz"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Clear existing profile
            if os.path.exists(PROFILE_PATH):
                import shutil
                shutil.rmtree(PROFILE_PATH)
            
            os.makedirs(PROFILE_PATH, exist_ok=True)
            
            # Extract profile
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall(PROFILE_PATH)
            
            # Cleanup
            os.remove(temp_path)
            
            self.logger.info("✅ Profile downloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Profile download failed: {e}")
            return False

    def setup_browser(self):
        """Setup Firefox with profile and memory optimization"""
        self.logger.info("🦊 Setting up Firefox browser...")
        
        # Download profile first
        if not self.download_profile():
            self.logger.warning("⚠️ Using fresh profile")
        
        options = Options()
        options.headless = True
        
        # ULTRA MEMORY OPTIMIZATION
        memory_prefs = {
            # Disable caches
            "browser.cache.disk.enable": False,
            "browser.cache.memory.enable": False,
            "browser.cache.offline.enable": False,
            
            # Single process
            "dom.ipc.processCount": 1,
            "browser.tabs.remote.autostart": False,
            
            # JS memory limits
            "javascript.options.mem.max": 80000000,  # 80MB
            "javascript.options.gc_mem_threshold": 1,
            
            # Disable features
            "media.memory_cache_max_size": 0,
            "media.cache_size": 0,
            "image.cache.size": 0,
            
            # Extensions
            "extensions.autoDisableScopes": 0,
            "extensions.enabledScopes": 15,
            
            # Updates & telemetry
            "app.update.auto": False,
            "datareporting.healthreport.uploadEnabled": False,
            "toolkit.telemetry.enabled": False,
            
            # Session
            "browser.sessionstore.interval": 300000,
        }
        
        for pref, value in memory_prefs.items():
            options.set_preference(pref, value)
        
        # Use profile
        options.add_argument(f"-profile")
        options.add_argument(PROFILE_PATH)
        
        # Browser arguments
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Service configuration
        service = Service(
            log_path=os.devnull,
            service_args=['--log', 'fatal']
        )
        
        try:
            self.logger.info("🚀 Starting Firefox with profile...")
            self.browser = webdriver.Firefox(
                options=options,
                service=service
            )
            
            # Small window
            self.browser.set_window_size(1024, 768)
            
            self.logger.info("✅ Firefox started with profile!")
            self.log_memory_usage()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            # Try without profile as fallback
            return self.setup_browser_fallback()

    def setup_browser_fallback(self):
        """Fallback browser setup without profile"""
        self.logger.info("🔄 Trying fallback browser setup...")
        
        options = Options()
        options.headless = True
        
        # Minimal preferences for fallback
        options.set_preference("dom.ipc.processCount", 1)
        options.set_preference("browser.tabs.remote.autostart", False)
        options.set_preference("javascript.options.mem.max", 50000000)
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.browser = webdriver.Firefox(options=options)
            self.logger.info("✅ Fallback browser started")
            return True
        except Exception as e:
            self.logger.error(f"❌ Fallback also failed: {e}")
            return False

    def login_to_adshare(self):
        """Simple login procedure"""
        self.logger.info("🔐 Logging into AdShare...")
        
        try:
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            current_url = self.browser.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # Check if login needed
            if "login" in current_url:
                self.logger.info("📧 Entering credentials...")
                
                # Try multiple field selectors
                selectors = [
                    "input[name='mail']",
                    "input[type='email']",
                    "input[placeholder*='email' i]",
                    "input[id*='mail']"
                ]
                
                email_field = None
                for selector in selectors:
                    try:
                        email_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if email_field:
                    email_field.clear()
                    email_field.send_keys(EMAIL)
                    self.logger.info("✅ Email entered")
                
                # Password field
                password_selectors = [
                    "input[type='password']",
                    "input[name='password']",
                    "input[placeholder*='password' i]"
                ]
                
                password_field = None
                for selector in password_selectors:
                    try:
                        password_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if password_field:
                    password_field.clear()
                    password_field.send_keys(PASSWORD)
                    self.logger.info("✅ Password entered")
                
                # Login button
                login_selectors = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "a.button[onclick*='submit']",
                    "button:contains('Login')",
                    "input[value*='Login' i]"
                ]
                
                login_btn = None
                for selector in login_selectors:
                    try:
                        if "contains" in selector:
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
                    self.logger.info("✅ Login button clicked")
                    time.sleep(10)
            
            # Final check
            current_url = self.browser.current_url
            if "surf" in current_url:
                self.logger.info("✅ Successfully on surf page!")
                return True
            else:
                self.logger.warning(f"⚠️ May need manual intervention: {current_url}")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"❌ Login process error: {e}")
            return False

    def extract_credits(self):
        """Extract credit information"""
        try:
            page_source = self.browser.page_source
            import re
            
            patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*Credits',
                r'Credits.*?(\d{1,3}(?:,\d{3})*)',
                r'balance.*?(\d[\d,]*)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    self.credits = f"{matches[0]} Credits"
                    return True
            
            self.credits = "Not found"
            return False
            
        except Exception as e:
            self.credits = f"Error: {str(e)[:30]}"
            return False

    def keep_alive(self):
        """Main monitoring loop"""
        self.logger.info("🔄 Starting monitoring loop...")
        self.monitoring = True
        
        check_count = 0
        
        while self.monitoring:
            try:
                # Refresh every 15 minutes
                if check_count % 9 == 0:
                    self.browser.refresh()
                    time.sleep(5)
                    
                    if self.extract_credits():
                        self.logger.info(f"💰 Credits: {self.credits}")
                
                check_count += 1
                self.status = f"Monitoring - Credits: {self.credits}"
                
                # Log memory every 30 minutes
                if check_count % 18 == 0:
                    self.log_memory_usage()
                
                # Wait 100 seconds
                for _ in range(10):
                    if not self.monitoring:
                        break
                    time.sleep(10)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)

    def start_monitoring(self):
        """Start the monitoring service"""
        self.logger.info("🚀 Starting AdShare monitor...")
        
        if not self.setup_browser():
            return False
        
        # Try login
        login_success = self.login_to_adshare()
        if not login_success:
            self.logger.warning("⚠️ Login may have issues, continuing...")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.keep_alive)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.status = "Monitoring active"
        return True

    def stop_monitoring(self):
        """Stop monitoring"""
        self.logger.info("🛑 Stopping monitor...")
        self.monitoring = False
        time.sleep(2)
        
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
            self.browser = None
        
        self.status = "Stopped"

    def log_memory_usage(self):
        """Log memory usage"""
        memory = psutil.virtual_memory()
        self.logger.info(f"💾 Memory: {memory.percent}% used")

# Global monitor instance
monitor = KoyebAdShareMonitor()

# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    return jsonify({
        "status": "AdShare Monitor",
        "monitor_status": monitor.status,
        "credits": monitor.credits,
        "uptime_hours": f"{(time.time() - monitor.start_time)/3600:.1f}",
        "memory_percent": psutil.virtual_memory().percent
    })

@app.route('/start')
def start_monitor():
    if not monitor.monitoring:
        success = monitor.start_monitoring()
        return jsonify({"status": "started" if success else "failed"})
    return jsonify({"status": "already_running"})

@app.route('/stop')
def stop_monitor():
    monitor.stop_monitoring()
    return jsonify({"status": "stopped"})

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "monitoring": monitor.monitoring,
        "memory_percent": psutil.virtual_memory().percent
    })

@app.route('/restart')
def restart_monitor():
    monitor.stop_monitoring()
    time.sleep(5)
    success = monitor.start_monitoring()
    return jsonify({"status": "restarted" if success else "restart_failed"})

# Auto-start
def initialize():
    time.sleep(10)
    monitor.start_monitoring()

init_thread = threading.Thread(target=initialize)
init_thread.daemon = True
init_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)