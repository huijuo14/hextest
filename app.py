#!/usr/bin/env python3
"""
AUTO-START AdShare Monitor
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

class AutoAdShareMonitor:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        self.status = "Initializing"
        self.start_time = time.time()
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def setup_browser_barebones(self):
        """Barebones browser setup - NO PROFILE"""
        self.logger.info("🦊 Setting up barebones Firefox...")
        
        options = Options()
        options.headless = True
        
        # ABSOLUTE MINIMUM settings
        options.set_preference("dom.ipc.processCount", 1)
        options.set_preference("browser.tabs.remote.autostart", False)
        options.set_preference("javascript.options.mem.max", 20000000)  # 20MB
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        try:
            self.browser = webdriver.Firefox(options=options)
            self.logger.info("✅ Firefox started successfully!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            return False

    def navigate_and_login(self):
        """Navigate to AdShare and login"""
        try:
            self.logger.info("🌐 Navigating to AdShare...")
            self.browser.get("https://adsha.re/surf")
            time.sleep(10)
            
            current_url = self.browser.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # If login page, try to login
            if "login" in current_url:
                self.logger.info("🔐 Attempting login...")
                
                # Try email
                try:
                    email = self.browser.find_element(By.CSS_SELECTOR, "input[name='mail']")
                    email.send_keys(EMAIL)
                    self.logger.info("✅ Email entered")
                except:
                    self.logger.warning("⚠️ Email field not found")
                
                # Try password
                try:
                    password = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
                    password.send_keys(PASSWORD)
                    self.logger.info("✅ Password entered")
                except:
                    self.logger.warning("⚠️ Password field not found")
                
                # Try login button
                try:
                    login_btn = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    login_btn.click()
                    self.logger.info("✅ Login button clicked")
                except:
                    self.logger.warning("⚠️ Login button not found")
                
                time.sleep(10)
            
            self.logger.info("✅ Navigation completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {e}")
            return False

    def check_credits(self):
        """Check credits on page"""
        try:
            page_source = self.browser.page_source
            import re
            match = re.search(r'(\d[\d,]*) Credits', page_source)
            if match:
                self.credits = f"{match.group(1)} Credits"
                return True
            else:
                self.credits = "Not found"
                return False
        except:
            self.credits = "Error checking"
            return False

    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("🔄 Starting monitoring loop...")
        self.monitoring = True
        
        cycle = 0
        
        while self.monitoring:
            try:
                # Refresh every 15 minutes
                if cycle % 9 == 0:
                    self.browser.refresh()
                    time.sleep(5)
                    
                    if self.check_credits():
                        self.logger.info(f"💰 Credits: {self.credits}")
                
                cycle += 1
                self.status = f"Running - {self.credits}"
                
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
        
        if not self.setup_browser_barebones():
            return False
        
        self.navigate_and_login()
        
        monitor_thread = threading.Thread(target=self.monitor_loop)
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
monitor = AutoAdShareMonitor()

@app.route('/')
def index():
    return jsonify({
        "status": "AdShare Monitor - READY",
        "monitor_status": monitor.status,
        "credits": monitor.credits,
        "endpoints": {
            "/start": "Start monitoring",
            "/stop": "Stop monitoring",
            "/health": "Health check"
        }
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

# AUTO-START
def auto_start():
    time.sleep(10)  # Wait for app to fully start
    monitor.start_monitoring()

# Start automatically
auto_start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)