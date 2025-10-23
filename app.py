#!/usr/bin/env python3
"""
Fixed AdShare Monitor for Koyeb - Memory Optimized
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

    def setup_browser(self):
        """Setup Firefox with ULTRA memory optimization"""
        self.logger.info("🦊 Setting up Firefox with memory optimization...")
        
        options = Options()
        options.headless = True
        
        # CRITICAL MEMORY OPTIMIZATION
        memory_prefs = {
            # Disable all possible memory usage
            "browser.cache.disk.enable": False,
            "browser.cache.memory.enable": False,
            "browser.cache.offline.enable": False,
            "browser.sessionstore.interval": 300000,  # 5 minutes
            
            # Single process mode
            "dom.ipc.processCount": 1,
            "browser.tabs.remote.autostart": False,
            "browser.tabs.remote.autostart.2": False,
            
            # JavaScript memory limits
            "javascript.options.mem.max": 50000000,  # 50MB only!
            "javascript.options.gc_mem_threshold": 1,
            
            # Disable features
            "media.memory_cache_max_size": 0,
            "media.cache_size": 0,
            "image.cache.size": 0,
            
            # Keep extensions but limit them
            "extensions.autoDisableScopes": 0,
            "extensions.enabledScopes": 1,
            
            # Security (optional for memory)
            "security.sandbox.content.level": 0,
            
            # Disable updates and telemetry
            "app.update.auto": False,
            "app.update.enabled": False,
            "datareporting.healthreport.uploadEnabled": False,
            "toolkit.telemetry.enabled": False,
        }
        
        for pref, value in memory_prefs.items():
            options.set_preference(pref, value)
        
        # Add arguments for memory saving
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        # Service configuration for stability
        service = Service(
            log_path=os.devnull,  # Disable geckodriver logs
            service_args=['--log', 'fatal']  # Only fatal errors
        )
        
        try:
            self.logger.info("🚀 Starting Firefox...")
            self.browser = webdriver.Firefox(
                options=options,
                service=service
            )
            
            # Set small window size
            self.browser.set_window_size(800, 600)
            
            self.logger.info("✅ Firefox started successfully")
            self.log_memory_usage()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            return False

    def login_to_adshare(self):
        """Simple login without complex element finding"""
        self.logger.info("🔐 Attempting AdShare login...")
        
        try:
            # Go directly to surf page
            self.browser.get("https://adsha.re/surf")
            time.sleep(15)  # Longer wait for page load
            
            current_url = self.browser.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # If redirected to login, try basic login
            if "login" in current_url:
                self.logger.info("📧 Attempting login...")
                
                # Try simple approach - just fill forms by name
                try:
                    # Find email field
                    email_fields = self.browser.find_elements(By.NAME, "mail")
                    if email_fields:
                        email_fields[0].send_keys(EMAIL)
                        self.logger.info("✅ Email entered")
                    
                    # Find password field
                    password_fields = self.browser.find_elements(By.CSS_SELECTOR, "input[type='password']")
                    if password_fields:
                        password_fields[0].send_keys(PASSWORD)
                        self.logger.info("✅ Password entered")
                    
                    # Find any submit button
                    submit_buttons = self.browser.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                    if submit_buttons:
                        submit_buttons[0].click()
                        self.logger.info("✅ Login button clicked")
                    
                    time.sleep(10)
                    
                except Exception as login_error:
                    self.logger.warning(f"⚠️ Login attempt failed: {login_error}")
            
            # Check if we're on surf page
            current_url = self.browser.current_url
            if "surf" in current_url:
                self.logger.info("✅ On surf page - ready to monitor")
                return True
            else:
                self.logger.warning(f"⚠️ Not on surf page: {current_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {e}")
            return False

    def extract_credits_simple(self):
        """Simple credit extraction without refresh"""
        try:
            page_source = self.browser.page_source
            
            # Simple text search for credits
            if "Credits" in page_source:
                # Find numbers near "Credits"
                import re
                credit_match = re.search(r'(\d[\d,]*) Credits', page_source)
                if credit_match:
                    self.credits = f"{credit_match.group(1)} Credits"
                    return True
            
            self.credits = "Not detected"
            return False
            
        except Exception as e:
            self.credits = f"Error: {str(e)[:50]}"
            return False

    def keep_alive_lightweight(self):
        """Ultra-light monitoring to save memory"""
        self.logger.info("🔄 Starting lightweight monitoring...")
        self.monitoring = True
        
        check_count = 0
        
        while self.monitoring:
            try:
                # Minimal activity - just check page every 15 minutes
                if check_count % 9 == 0:  # 9 * 100s ≈ 15 minutes
                    if self.extract_credits_simple():
                        self.logger.info(f"💰 Credits: {self.credits}")
                    else:
                        self.logger.info("🔍 Checking page...")
                
                check_count += 1
                self.status = f"Active - Credits: {self.credits}"
                
                # Minimal memory logging
                if check_count % 30 == 0:  # Every 30 cycles
                    self.log_memory_usage()
                
                # Wait 100 seconds between checks
                for _ in range(10):
                    if not self.monitoring:
                        break
                    time.sleep(10)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)

    def start_monitoring(self):
        """Start monitoring with error handling"""
        self.logger.info("🚀 Starting monitor...")
        
        if not self.setup_browser():
            self.logger.error("❌ Cannot start - browser setup failed")
            return False
        
        # Try login but continue even if it fails
        login_success = self.login_to_adshare()
        if not login_success:
            self.logger.warning("⚠️ Login may have failed, continuing anyway...")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.keep_alive_lightweight)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.status = "Monitoring started"
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
        "uptime": f"{(time.time() - monitor.start_time)/3600:.1f}h"
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

# Auto-start monitoring
def initialize():
    time.sleep(15)  # Wait for system to stabilize
    monitor.start_monitoring()

init_thread = threading.Thread(target=initialize)
init_thread.daemon = True
init_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)