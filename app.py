#!/usr/bin/env python3
"""
FIXED AdShare Monitor - Correct Profile Path
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

class FixedAdShareMonitor:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        self.status = "Initializing"
        self.start_time = time.time()
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def download_and_fix_profile(self):
        """Download profile and fix directory structure"""
        self.logger.info("📥 Downloading and fixing Firefox profile...")
        
        try:
            # Clear existing
            if os.path.exists(PROFILE_PATH):
                import shutil
                shutil.rmtree(PROFILE_PATH)
            os.makedirs(PROFILE_PATH, exist_ok=True)
            
            # Download
            response = requests.get(PROFILE_URL, timeout=60, stream=True)
            response.raise_for_status()
            
            temp_path = "/app/profile_temp.tar.gz"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract to temp location first
            temp_extract = "/app/temp_extract"
            if os.path.exists(temp_extract):
                shutil.rmtree(temp_extract)
            os.makedirs(temp_extract)
            
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall(temp_extract)
            
            # FIX: Find the actual profile directory
            actual_profile = None
            for root, dirs, files in os.walk(temp_extract):
                if "prefs.js" in files:
                    actual_profile = root
                    break
            
            if actual_profile:
                # Copy all files from actual profile to PROFILE_PATH
                for item in os.listdir(actual_profile):
                    src = os.path.join(actual_profile, item)
                    dst = os.path.join(PROFILE_PATH, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                
                self.logger.info(f"✅ Profile fixed and moved to {PROFILE_PATH}")
            else:
                self.logger.error("❌ No valid profile found in archive")
                return False
            
            # Cleanup
            shutil.rmtree(temp_extract)
            os.remove(temp_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Profile download failed: {e}")
            return False

    def setup_browser(self):
        """Setup browser with fixed profile"""
        self.logger.info("🦊 Setting up Firefox with fixed profile...")
        
        # Download and fix profile
        if not self.download_and_fix_profile():
            self.logger.warning("⚠️ Using fresh profile")
        
        options = Options()
        options.headless = True
        
        # Memory optimization
        memory_prefs = {
            "browser.cache.disk.enable": False,
            "browser.cache.memory.enable": False,
            "dom.ipc.processCount": 1,
            "browser.tabs.remote.autostart": False,
            "javascript.options.mem.max": 80000000,
            "extensions.autoDisableScopes": 0,
        }
        
        for pref, value in memory_prefs.items():
            options.set_preference(pref, value)
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Use the fixed profile
        if os.path.exists(os.path.join(PROFILE_PATH, "prefs.js")):
            options.add_argument(f"-profile")
            options.add_argument(PROFILE_PATH)
            self.logger.info("✅ Using fixed Firefox profile with extensions")
        else:
            self.logger.warning("⚠️ No valid profile, using fresh instance")
        
        try:
            self.browser = webdriver.Firefox(options=options)
            self.logger.info("✅ Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            return False

    def login_to_adshare(self):
        """Login to AdShare"""
        self.logger.info("🔐 Logging into AdShare...")
        
        try:
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            current_url = self.browser.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            if "login" in current_url:
                self.logger.info("📧 Entering credentials...")
                
                # Email
                try:
                    email_field = self.browser.find_element(By.CSS_SELECTOR, "input[name='mail']")
                    email_field.send_keys(EMAIL)
                    self.logger.info("✅ Email entered")
                except:
                    self.logger.warning("⚠️ Email field not found")
                
                # Password
                try:
                    password_field = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
                    password_field.send_keys(PASSWORD)
                    self.logger.info("✅ Password entered")
                except:
                    self.logger.warning("⚠️ Password field not found")
                
                # Login button
                try:
                    login_btn = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                    login_btn.click()
                    self.logger.info("✅ Login button clicked")
                except:
                    self.logger.warning("⚠️ Login button not found")
                
                time.sleep(10)
            
            # Check if on surf page
            if "surf" in self.browser.current_url:
                self.logger.info("✅ On surf page!")
                return True
            else:
                self.logger.warning(f"⚠️ Not on surf page: {self.browser.current_url}")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"❌ Login failed: {e}")
            return False

    def extract_credits(self):
        """Extract credits"""
        try:
            import re
            page_source = self.browser.page_source
            
            patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*Credits',
                r'Credits.*?(\d{1,3}(?:,\d{3})*)',
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
        """Monitoring loop"""
        self.logger.info("🔄 Starting monitoring...")
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
                self.status = f"Running - Credits: {self.credits}"
                
                # Wait 100 seconds
                for _ in range(10):
                    if not self.monitoring:
                        break
                    time.sleep(10)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)

    def start_monitoring(self):
        """Start monitoring"""
        self.logger.info("🚀 Starting AdShare monitor...")
        
        if not self.setup_browser():
            return False
        
        self.login_to_adshare()  # Try login, continue anyway
        
        monitor_thread = threading.Thread(target=self.keep_alive)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.status = "Monitoring active"
        return True

    def stop_monitoring(self):
        """Stop monitoring"""
        self.logger.info("🛑 Stopping monitor...")
        self.monitoring = False
        
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
        
        self.status = "Stopped"

# Global monitor
monitor = FixedAdShareMonitor()

@app.route('/')
def index():
    return jsonify({
        "status": "AdShare Monitor",
        "monitor_status": monitor.status,
        "credits": monitor.credits,
        "uptime": f"{(time.time() - monitor.start_time)/3600:.1f}h"
    })

@app.route('/start')
def start_monitor():
    if not monitor.monitoring:
        success = monitor.start_monitoring()
        return jsonify({"status": "started" if success else "failed"})
    return jsonify({"status": "already_running"})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "monitoring": monitor.monitoring})

# Auto-start
def initialize():
    time.sleep(5)
    monitor.start_monitoring()

init_thread = threading.Thread(target=initialize)
init_thread.daemon = True
init_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)