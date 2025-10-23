#!/usr/bin/env python3
"""
FIXED AdShare Monitor - Simple Profile Extraction
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

app = Flask(__name__)

class SimpleAdShareMonitor:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        self.status = "Initializing"
        self.start_time = time.time()
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def download_profile_simple(self):
        """Simple profile download that just extracts everything"""
        self.logger.info("📥 Downloading Firefox profile...")
        
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
            
            # Extract directly to profile path, ignoring errors
            with tarfile.open(temp_path, 'r:gz') as tar:
                # Get all members
                members = tar.getmembers()
                for member in members:
                    try:
                        # Fix path - remove the nested directory structure
                        if '5yvzi8ts.default-default' in member.name:
                            # Extract files from the actual profile directory
                            member.name = os.path.basename(member.name)
                            tar.extract(member, PROFILE_PATH)
                    except Exception as e:
                        self.logger.debug(f"⚠️ Skipped {member.name}: {e}")
                        continue
            
            os.remove(temp_path)
            
            # Check if we have essential files
            essential_files = ['prefs.js', 'extensions']
            has_essentials = any(os.path.exists(os.path.join(PROFILE_PATH, f)) for f in essential_files)
            
            if has_essentials:
                self.logger.info("✅ Profile extracted successfully")
                return True
            else:
                self.logger.warning("⚠️ Profile missing essential files")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Profile download failed: {e}")
            return False

    def setup_browser_simple(self):
        """Simple browser setup that just works"""
        self.logger.info("🦊 Setting up Firefox...")
        
        # Try to download profile, but continue if it fails
        profile_loaded = self.download_profile_simple()
        
        options = Options()
        options.headless = True
        
        # Minimal memory settings
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("dom.ipc.processCount", 1)
        options.set_preference("javascript.options.mem.max", 50000000)
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Use profile if we have one
        if profile_loaded and os.path.exists(os.path.join(PROFILE_PATH, "prefs.js")):
            options.add_argument(f"-profile")
            options.add_argument(PROFILE_PATH)
            self.logger.info("✅ Using Firefox profile with extensions")
        else:
            self.logger.info("ℹ️ Using fresh Firefox instance")
        
        try:
            self.browser = webdriver.Firefox(options=options)
            self.logger.info("✅ Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            return False

    def navigate_to_surf(self):
        """Simply navigate to surf page"""
        self.logger.info("🌐 Navigating to AdShare...")
        
        try:
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            current_url = self.browser.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # Check if we need to login
            if "login" in current_url:
                self.logger.info("🔐 Attempting login...")
                return self.attempt_login()
            else:
                self.logger.info("✅ Already on surf page!")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {e}")
            return False

    def attempt_login(self):
        """Simple login attempt"""
        try:
            # Try to find and fill email
            email_selectors = ["input[name='mail']", "input[type='email']"]
            for selector in email_selectors:
                try:
                    email_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys(EMAIL)
                    self.logger.info("✅ Email entered")
                    break
                except:
                    continue
            
            # Try to find and fill password
            password_selectors = ["input[type='password']", "input[name='password']"]
            for selector in password_selectors:
                try:
                    password_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    password_field.clear()
                    password_field.send_keys(PASSWORD)
                    self.logger.info("✅ Password entered")
                    break
                except:
                    continue
            
            # Try to find and click login button
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
            
            # Check result
            if "surf" in self.browser.current_url:
                self.logger.info("✅ Login successful!")
                return True
            else:
                self.logger.warning("⚠️ Login may have failed, but continuing...")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Login attempt failed: {e}")
            return True  # Continue anyway

    def check_credits(self):
        """Check current credits"""
        try:
            import re
            page_source = self.browser.page_source
            
            # Simple credit pattern matching
            credit_match = re.search(r'(\d[\d,]*) Credits', page_source)
            if credit_match:
                self.credits = f"{credit_match.group(1)} Credits"
                return True
            else:
                self.credits = "Not found"
                return False
                
        except Exception as e:
            self.credits = f"Error: {str(e)[:20]}"
            return False

    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("🔄 Starting monitoring loop...")
        self.monitoring = True
        
        cycle_count = 0
        
        while self.monitoring:
            try:
                # Refresh page every 10 minutes
                if cycle_count % 6 == 0:  # 6 * 100s = 10 minutes
                    self.browser.refresh()
                    time.sleep(5)
                
                # Check credits every 30 minutes
                if cycle_count % 18 == 0:  # 18 * 100s = 30 minutes
                    if self.check_credits():
                        self.logger.info(f"💰 Credits: {self.credits}")
                    else:
                        self.logger.info("🔍 Checking page status...")
                
                cycle_count += 1
                self.status = f"Active - Credits: {self.credits}"
                
                # Wait 100 seconds
                for i in range(10):
                    if not self.monitoring:
                        break
                    time.sleep(10)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute before retry

    def start_monitoring(self):
        """Start the monitor"""
        self.logger.info("🚀 Starting AdShare monitor...")
        
        if not self.setup_browser_simple():
            self.logger.error("❌ Failed to start browser")
            return False
        
        # Navigate to surf page
        if not self.navigate_to_surf():
            self.logger.warning("⚠️ Navigation issues, but continuing...")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.status = "Monitoring started"
        return True

    def stop_monitoring(self):
        """Stop the monitor"""
        self.logger.info("🛑 Stopping monitor...")
        self.monitoring = False
        
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
        
        self.status = "Stopped"

# Global monitor instance
monitor = SimpleAdShareMonitor()

@app.route('/')
def index():
    return jsonify({
        "status": "AdShare Monitor",
        "monitor_status": monitor.status,
        "credits": monitor.credits,
        "uptime_hours": f"{(time.time() - monitor.start_time)/3600:.1f}"
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

# Auto-start
def initialize():
    time.sleep(5)
    monitor.start_monitoring()

init_thread = threading.Thread(target=initialize)
init_thread.daemon = True
init_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)