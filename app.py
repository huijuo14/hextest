#!/usr/bin/env python3
"""
ULTIMATE FIX - Test Firefox directly first
"""

import os
import time
import logging
import threading
import tarfile
import requests
import subprocess
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

class UltimateAdShareMonitor:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        self.status = "Initializing"
        self.start_time = time.time()
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def test_firefox_directly(self):
        """Test Firefox directly to see the real error"""
        self.logger.info("🔧 Testing Firefox directly...")
        
        # First test Firefox without profile
        try:
            result = subprocess.run(
                ['firefox', '--headless', '--screenshot', '/app/test1.png', 'about:blank'],
                capture_output=True, text=True, timeout=30
            )
            self.logger.info(f"Firefox no-profile test: returncode={result.returncode}")
            if result.stderr:
                self.logger.info(f"Firefox stderr: {result.stderr[:500]}")
        except Exception as e:
            self.logger.error(f"Firefox no-profile test failed: {e}")
        
        # Now test with profile
        try:
            # Download profile first
            if os.path.exists(PROFILE_PATH):
                import shutil
                shutil.rmtree(PROFILE_PATH)
            os.makedirs(PROFILE_PATH, exist_ok=True)
            
            response = requests.get(PROFILE_URL, timeout=60, stream=True)
            with open('/app/temp.tar.gz', 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract all files
            with tarfile.open('/app/temp.tar.gz', 'r:gz') as tar:
                tar.extractall(PROFILE_PATH)
            
            os.remove('/app/temp.tar.gz')
            
            # Test Firefox with profile
            result = subprocess.run([
                'firefox', '--headless',
                '-profile', PROFILE_PATH,
                '--screenshot', '/app/test2.png',
                'about:blank'
            ], capture_output=True, text=True, timeout=30)
            
            self.logger.info(f"Firefox with-profile test: returncode={result.returncode}")
            if result.stdout:
                self.logger.info(f"Firefox stdout: {result.stdout}")
            if result.stderr:
                self.logger.info(f"Firefox stderr: {result.stderr}")
                
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Firefox with-profile test failed: {e}")
            return False

    def setup_browser_ultralight(self):
        """ULTRA LIGHT browser setup"""
        self.logger.info("🦊 Setting up ULTRA LIGHT Firefox...")
        
        # Test Firefox first
        firefox_works = self.test_firefox_directly()
        if not firefox_works:
            self.logger.error("❌ Firefox itself is broken")
            return False
        
        options = Options()
        options.headless = True
        
        # ULTRA MINIMAL preferences
        options.set_preference("dom.ipc.processCount", 1)
        options.set_preference("browser.tabs.remote.autostart", False)
        options.set_preference("javascript.options.mem.max", 30000000)  # 30MB only!
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Try WITHOUT profile first
        self.logger.info("🚀 Trying Firefox WITHOUT profile...")
        try:
            self.browser = webdriver.Firefox(options=options)
            self.logger.info("✅ Firefox started WITHOUT profile!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Browser without profile failed: {e}")
        
        # If that fails, try with profile but with even more restrictions
        self.logger.info("🚀 Trying Firefox WITH profile...")
        try:
            options.add_argument(f"-profile")
            options.add_argument(PROFILE_PATH)
            
            # Add more restrictions for profile
            options.set_preference("extensions.autoDisableScopes", 10)  # Disable most extensions
            
            self.browser = webdriver.Firefox(options=options)
            self.logger.info("✅ Firefox started WITH profile!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Browser with profile failed: {e}")
        
        return False

    def simple_navigation(self):
        """Simple navigation to surf page"""
        try:
            self.logger.info("🌐 Navigating to AdShare...")
            self.browser.get("https://adsha.re/surf")
            time.sleep(15)  # Longer wait
            
            current_url = self.browser.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # If login page, try basic login
            if "login" in current_url:
                self.logger.info("🔐 Attempting simple login...")
                
                # Just try the most common selectors
                try:
                    email = self.browser.find_element(By.CSS_SELECTOR, "input[name='mail']")
                    email.send_keys(EMAIL)
                except: pass
                
                try:
                    password = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
                    password.send_keys(PASSWORD)
                except: pass
                
                try:
                    login = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    login.click()
                except: pass
                
                time.sleep(10)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {e}")
            return False

    def monitor_simple(self):
        """Simple monitoring"""
        self.logger.info("🔄 Starting simple monitoring...")
        self.monitoring = True
        
        while self.monitoring:
            try:
                # Just keep the page open, refresh every 20 minutes
                self.browser.refresh()
                time.sleep(5)
                
                # Simple credit check
                page_source = self.browser.page_source
                if "Credits" in page_source:
                    import re
                    match = re.search(r'(\d[\d,]*) Credits', page_source)
                    if match:
                        self.credits = f"{match.group(1)} Credits"
                        self.logger.info(f"💰 Credits: {self.credits}")
                
                self.status = f"Monitoring - {self.credits}"
                
                # Wait 20 minutes
                for _ in range(120):  # 120 * 10s = 20 minutes
                    if not self.monitoring:
                        break
                    time.sleep(10)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)

    def start_monitoring(self):
        """Start monitoring"""
        self.logger.info("🚀 Starting Ultimate AdShare monitor...")
        
        if not self.setup_browser_ultralight():
            return False
        
        self.simple_navigation()
        
        monitor_thread = threading.Thread(target=self.monitor_simple)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.status = "Monitoring started"
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
monitor = UltimateAdShareMonitor()

@app.route('/')
def index():
    return jsonify({
        "status": "AdShare Monitor - ULTIMATE FIX",
        "monitor_status": monitor.status,
        "credits": monitor.credits
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

# Don't auto-start - let user start manually
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)