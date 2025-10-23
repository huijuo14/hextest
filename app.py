#!/usr/bin/env python3
"""
Lightweight AdShare Monitor for Railway.app
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
PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_profile.tar.1.gz"
PORT = int(os.environ.get("PORT", 8000))

app = Flask(__name__)

class RailwayAdShareMonitor:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        self.status = "Initializing"
        self.start_time = time.time()
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def setup_profile(self):
        """Download and setup Firefox profile"""
        self.logger.info("📥 Setting up Firefox profile...")
        
        try:
            # Clear existing profile
            if os.path.exists(PROFILE_PATH):
                import shutil
                shutil.rmtree(PROFILE_PATH)
            os.makedirs(PROFILE_PATH, exist_ok=True)
            
            # Download profile
            response = requests.get(PROFILE_URL, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save and extract
            temp_path = "/app/temp_profile.tar.gz"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract all files
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall(PROFILE_PATH)
            
            os.remove(temp_path)
            
            # Fix: Find actual profile directory
            actual_profile = None
            for root, dirs, files in os.walk(PROFILE_PATH):
                if "prefs.js" in files:
                    actual_profile = root
                    break
            
            if actual_profile and actual_profile != PROFILE_PATH:
                # Move files to root profile directory
                for item in os.listdir(actual_profile):
                    src = os.path.join(actual_profile, item)
                    dst = os.path.join(PROFILE_PATH, item)
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.remove(dst)
                    
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                
                # Remove the nested directory
                shutil.rmtree(os.path.dirname(actual_profile))
            
            self.logger.info("✅ Profile setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Profile setup failed: {e}")
            return False

    def setup_browser(self):
        """Setup Firefox browser with profile"""
        self.logger.info("🦊 Setting up Firefox with profile...")
        
        # Setup profile first
        profile_ready = self.setup_profile()
        
        options = Options()
        options.headless = True
        
        # Optimized preferences for Railway
        prefs = {
            # Memory optimization
            "browser.cache.disk.enable": False,
            "browser.cache.memory.enable": False,
            "dom.ipc.processCount": 1,
            "browser.tabs.remote.autostart": False,
            "javascript.options.mem.max": 100000000,  # 100MB
            
            # Keep extensions enabled
            "extensions.autoDisableScopes": 0,
            "extensions.enabledScopes": 15,
            
            # Performance
            "browser.sessionstore.interval": 300000,
            "media.memory_cache_max_size": 0,
            
            # Disable updates & telemetry
            "app.update.auto": False,
            "datareporting.healthreport.uploadEnabled": False,
        }
        
        for pref, value in prefs.items():
            options.set_preference(pref, value)
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Use profile if available
        if profile_ready and os.path.exists(os.path.join(PROFILE_PATH, "prefs.js")):
            options.add_argument(f"-profile")
            options.add_argument(PROFILE_PATH)
            self.logger.info("✅ Using Firefox profile with extensions")
        else:
            self.logger.warning("⚠️ Using fresh Firefox instance")
        
        try:
            self.browser = webdriver.Firefox(options=options)
            self.logger.info("✅ Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            return False

    def navigate_to_adshare(self):
        """Navigate to AdShare and handle login"""
        self.logger.info("🌐 Navigating to AdShare...")
        
        try:
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            current_url = self.browser.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # Handle login if needed
            if "login" in current_url:
                self.logger.info("🔐 Performing login...")
                return self.perform_login()
            else:
                self.logger.info("✅ Already on surf page!")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {e}")
            return False

    def perform_login(self):
        """Perform login with multiple selector attempts"""
        try:
            # Email field
            email_selectors = [
                "input[name='mail']",
                "input[type='email']",
                "input[placeholder*='email' i]"
            ]
            
            for selector in email_selectors:
                try:
                    email_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys(EMAIL)
                    self.logger.info("✅ Email entered")
                    break
                except:
                    continue
            
            # Password field
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[placeholder*='password' i]"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    password_field.clear()
                    password_field.send_keys(PASSWORD)
                    self.logger.info("✅ Password entered")
                    break
                except:
                    continue
            
            # Login button
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "a.button[onclick*='submit']"
            ]
            
            for selector in login_selectors:
                try:
                    login_btn = self.browser.find_element(By.CSS_SELECTOR, selector)
                    login_btn.click()
                    self.logger.info("✅ Login button clicked")
                    break
                except:
                    continue
            
            time.sleep(10)
            
            # Verify login success
            if "surf" in self.browser.current_url:
                self.logger.info("✅ Login successful!")
                return True
            else:
                self.logger.warning("⚠️ Login may need manual verification")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"❌ Login failed: {e}")
            return False

    def check_credits(self):
        """Check and update credit balance"""
        try:
            import re
            page_source = self.browser.page_source
            
            credit_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*Credits',
                r'Credits.*?(\d{1,3}(?:,\d{3})*)',
                r'balance.*?(\d[\d,]*)',
            ]
            
            for pattern in credit_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    self.credits = f"{matches[0]} Credits"
                    return True
            
            self.credits = "Not found"
            return False
            
        except Exception as e:
            self.credits = f"Error: {str(e)[:30]}"
            return False

    def monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("🔄 Starting monitoring loop...")
        self.monitoring = True
        
        cycle_count = 0
        
        while self.monitoring:
            try:
                # Refresh page every 15 minutes
                if cycle_count % 9 == 0:
                    self.browser.refresh()
                    time.sleep(5)
                
                # Check credits every 30 minutes
                if cycle_count % 18 == 0:
                    if self.check_credits():
                        self.logger.info(f"💰 Credits: {self.credits}")
                    else:
                        self.logger.info("🔍 Checking page status...")
                
                cycle_count += 1
                self.status = f"Monitoring - Credits: {self.credits}"
                
                # Log memory usage every hour
                if cycle_count % 36 == 0:
                    memory = psutil.virtual_memory()
                    self.logger.info(f"💾 Memory: {memory.percent}% used")
                
                # Wait 100 seconds between cycles
                for _ in range(10):
                    if not self.monitoring:
                        break
                    time.sleep(10)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)  # Wait before retry

    def start_monitoring(self):
        """Start the monitoring service"""
        self.logger.info("🚀 Starting AdShare monitor...")
        
        if not self.setup_browser():
            return False
        
        if not self.navigate_to_adshare():
            self.logger.warning("⚠️ Navigation issues, but continuing...")
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=self.monitoring_loop)
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
monitor = RailwayAdShareMonitor()

# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    """Main status page"""
    uptime = time.time() - monitor.start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    
    return jsonify({
        "status": "AdShare Monitor - Railway",
        "monitor_status": monitor.status,
        "credits": monitor.credits,
        "uptime": f"{hours}h {minutes}m",
        "memory_usage": f"{psutil.virtual_memory().percent}%",
        "endpoints": {
            "/start": "Start monitoring",
            "/stop": "Stop monitoring",
            "/status": "Current status",
            "/health": "Health check"
        }
    })

@app.route('/start')
def start_monitor():
    """Start monitoring"""
    if not monitor.monitoring:
        success = monitor.start_monitoring()
        return jsonify({"status": "started" if success else "failed"})
    return jsonify({"status": "already_running"})

@app.route('/stop')
def stop_monitor():
    """Stop monitoring"""
    monitor.stop_monitoring()
    return jsonify({"status": "stopped"})

@app.route('/status')
def get_status():
    """Get current status"""
    return jsonify({
        "monitoring": monitor.monitoring,
        "status": monitor.status,
        "credits": monitor.credits
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "monitoring": monitor.monitoring,
        "memory_percent": psutil.virtual_memory().percent
    })

# ========== AUTO-START ==========

def initialize_monitor():
    """Initialize monitor after app starts"""
    time.sleep(15)  # Wait for Railway to fully initialize
    monitor.start_monitoring()

# Start monitor in background thread
init_thread = threading.Thread(target=initialize_monitor)
init_thread.daemon = True
init_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)