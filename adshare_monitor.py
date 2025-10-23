#!/usr/bin/env python3
"""
Lightweight AdShare Monitor for Koyeb 24/7 with Profile Download
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
from selenium.webdriver.common.by import By
import psutil

# ========== CONFIGURATION ==========
EMAIL = "loginallapps@gmail.com"
PASSWORD = "@Sd2007123"
PROFILE_PATH = "/app/firefox_profile"
PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_profile.tar.gz"

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

    def download_and_extract_profile(self):
        """Download and extract Firefox profile from GitHub"""
        self.logger.info("📥 Downloading Firefox profile from GitHub...")
        
        try:
            # Download profile
            response = requests.get(PROFILE_URL, timeout=60)
            response.raise_for_status()
            
            # Save compressed profile
            temp_path = "/app/profile_temp.tar.gz"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Extract to profile directory
            if os.path.exists(PROFILE_PATH):
                import shutil
                shutil.rmtree(PROFILE_PATH)
            
            os.makedirs(PROFILE_PATH, exist_ok=True)
            
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall(PROFILE_PATH)
            
            # Cleanup
            os.remove(temp_path)
            
            self.logger.info("✅ Profile downloaded and extracted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Profile download failed: {e}")
            return False

    def check_profile_exists(self):
        """Check if profile exists and has necessary files"""
        if not os.path.exists(PROFILE_PATH):
            return False
        
        # Check for essential profile files
        essential_files = [
            "prefs.js",
            "extensions",
            "cookies.sqlite"
        ]
        
        for file in essential_files:
            if not os.path.exists(os.path.join(PROFILE_PATH, file)):
                return False
        
        return True

    def log_memory_usage(self):
        """Log current memory usage"""
        memory = psutil.virtual_memory()
        self.logger.info(f"Memory: {memory.used/1024/1024:.1f}MB / {memory.total/1024/1024:.1f}MB ({memory.percent}%)")

    def setup_browser(self):
        """Setup Firefox with optimized settings for low memory"""
        self.logger.info("🦊 Setting up Firefox browser...")
        
        # Download profile if doesn't exist
        if not self.check_profile_exists():
            self.logger.info("📥 No profile found, downloading...")
            if not self.download_and_extract_profile():
                self.logger.warning("⚠️ Using fresh profile without extensions")
        
        options = Options()
        options.headless = True
        
        # Memory optimization settings (keep extensions enabled)
        memory_prefs = {
            "browser.cache.disk.enable": False,
            "browser.cache.memory.enable": False,
            "dom.ipc.processCount": 1,  # Single content process
            "browser.tabs.remote.autostart": False,
            "javascript.options.mem.max": 150000000,  # 150MB JS memory limit
            "content.processLimit": 1,
            # Keep extensions enabled
            "extensions.autoDisableScopes": 0,
            "extensions.enabledScopes": 15,
        }
        
        for pref, value in memory_prefs.items():
            options.set_preference(pref, value)
        
        # Use profile
        if self.check_profile_exists():
            options.add_argument(f"-profile")
            options.add_argument(PROFILE_PATH)
            self.logger.info("✅ Using downloaded Firefox profile with extensions")
        else:
            self.logger.info("ℹ️ Using fresh Firefox instance")
        
        try:
            self.browser = webdriver.Firefox(options=options)
            self.logger.info("✅ Firefox started successfully")
            self.log_memory_usage()
            return True
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            return False

    def login_to_adshare(self):
        """Login to AdShare service"""
        self.logger.info("🔐 Logging into AdShare...")
        
        try:
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            # Check current page
            current_url = self.browser.current_url
            page_source = self.browser.page_source.lower()
            
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # Check if login is needed
            if "login" in current_url or "sign in" in page_source:
                self.logger.info("📧 Entering credentials...")
                
                # Find and fill email
                email_field = self.browser.find_element(By.CSS_SELECTOR, "input[name='mail']")
                email_field.clear()
                email_field.send_keys(EMAIL)
                time.sleep(2)
                
                # Find password field - try multiple selectors
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
                    time.sleep(2)
                else:
                    self.logger.error("❌ Password field not found")
                    return False
                
                # Click login button - try multiple selectors
                login_selectors = [
                    "a.button[onclick*='submit']",
                    "button[type='submit']",
                    "input[type='submit']",
                    ".login-btn",
                    "button:contains('Login')"
                ]
                
                login_btn = None
                for selector in login_selectors:
                    try:
                        if "contains" in selector:
                            # Simple contains text search
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
                    self.logger.info("🔄 Login button clicked")
                else:
                    self.logger.error("❌ Login button not found")
                    return False
                
                time.sleep(10)
            
            # Verify login success
            current_url = self.browser.current_url
            if "surf" in current_url and "login" not in current_url:
                self.logger.info("✅ Login successful")
                return True
            else:
                self.logger.warning(f"⚠️ May need manual login. Current URL: {current_url}")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"❌ Login failed: {e}")
            return False

    def extract_credits(self):
        """Extract current credit balance"""
        try:
            self.browser.refresh()
            time.sleep(5)
            
            page_source = self.browser.page_source
            import re
            
            # Look for credit patterns
            patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*Credits',
                r'Credits.*?(\d{1,3}(?:,\d{3})*)',
                r'balance.*?(\d[\d,]*)',
                r'>\s*(\d[\d,]*)\s*Credits<',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    self.credits = f"{matches[0]} Credits"
                    return True
            
            self.credits = "Not found"
            return False
            
        except Exception as e:
            self.credits = f"Error: {e}"
            return False

    def keep_alive(self):
        """Keep the session alive and monitor credits"""
        self.logger.info("🔄 Starting keep-alive monitoring...")
        self.monitoring = True
        
        credit_check_count = 0
        consecutive_errors = 0
        
        while self.monitoring and consecutive_errors < 5:
            try:
                # Refresh every 10 minutes to keep session alive
                self.browser.refresh()
                time.sleep(5)
                
                # Check credits every 30 minutes
                if credit_check_count % 3 == 0:  # 3 * 10min = 30min
                    if self.extract_credits():
                        self.logger.info(f"💰 Credits: {self.credits}")
                        consecutive_errors = 0  # Reset error counter
                    else:
                        self.logger.warning("⚠️ Could not extract credits")
                        consecutive_errors += 1
                
                credit_check_count += 1
                self.status = f"Running - Credits: {self.credits}"
                self.log_memory_usage()
                
                # Wait 10 minutes
                for _ in range(60):  # 60 * 10s = 10min
                    if not self.monitoring:
                        break
                    time.sleep(10)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                self.status = f"Error: {e}"
                consecutive_errors += 1
                time.sleep(60)  # Wait 1min before retry
        
        if consecutive_errors >= 5:
            self.logger.error("🚨 Too many consecutive errors, stopping monitor")
            self.stop_monitoring()

    def start_monitoring(self):
        """Start the monitoring service"""
        self.logger.info("🚀 Starting AdShare monitor...")
        
        if not self.setup_browser():
            return False
        
        if not self.login_to_adshare():
            self.logger.warning("⚠️ Login failed, but continuing anyway...")
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=self.keep_alive)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.status = "Monitoring active"
        return True

    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.logger.info("🛑 Stopping monitor...")
        self.monitoring = False
        
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
            self.browser = None
        
        self.status = "Stopped"

# Global monitor instance
monitor = KoyebAdShareMonitor()

# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    """Main status page"""
    uptime = time.time() - monitor.start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    
    return jsonify({
        "status": "AdShare Monitor Running",
        "monitor_status": monitor.status,
        "credits": monitor.credits,
        "uptime": f"{hours}h {minutes}m",
        "memory_usage": f"{psutil.virtual_memory().percent}%",
        "endpoints": {
            "/start": "Start monitoring",
            "/stop": "Stop monitoring", 
            "/status": "Current status",
            "/credits": "Current credits",
            "/health": "Health check",
            "/restart": "Restart monitor"
        }
    })

@app.route('/start')
def start_monitor():
    """Start the monitoring service"""
    if monitor.monitoring:
        return jsonify({"status": "Already running"})
    
    success = monitor.start_monitoring()
    return jsonify({"status": "Started" if success else "Failed"})

@app.route('/stop')
def stop_monitor():
    """Stop the monitoring service"""
    monitor.stop_monitoring()
    return jsonify({"status": "Stopped"})

@app.route('/restart')
def restart_monitor():
    """Restart the monitoring service"""
    monitor.stop_monitoring()
    time.sleep(5)
    success = monitor.start_monitoring()
    return jsonify({"status": "Restarted" if success else "Restart failed"})

@app.route('/status')
def get_status():
    """Get current status"""
    return jsonify({
        "monitoring": monitor.monitoring,
        "status": monitor.status,
        "credits": monitor.credits,
        "uptime_seconds": time.time() - monitor.start_time
    })

@app.route('/credits')
def get_credits():
    """Get current credits"""
    if monitor.browser and monitor.monitoring:
        monitor.extract_credits()
    return jsonify({"credits": monitor.credits})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    memory = psutil.virtual_memory()
    return jsonify({
        "status": "healthy",
        "memory_used_mb": round(memory.used / 1024 / 1024, 1),
        "memory_total_mb": round(memory.total / 1024 / 1024, 1),
        "memory_percent": memory.percent,
        "monitoring": monitor.monitoring,
        "browser_alive": monitor.browser is not None
    })

# ========== STARTUP ==========

def initialize_app():
    """Initialize the application"""
    # Wait a bit for system to stabilize
    time.sleep(10)
    
    # Start monitoring
    monitor.start_monitoring()

# Start initialization in background
init_thread = threading.Thread(target=initialize_app)
init_thread.daemon = True
init_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)