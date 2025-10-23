#!/usr/bin/env python3
"""
Lightweight AdShare Background Worker for Railway
"""

import os
import time
import logging
import tarfile
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import psutil

# ========== CONFIGURATION ==========
EMAIL = "loginallapps@gmail.com"
PASSWORD = "@Sd2007123"
PROFILE_PATH = "/app/firefox_profile"
PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_profile.tar.1.gz"

class AdShareWorker:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/app/worker.log')
            ]
        )
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
        
        # Optimized preferences
        prefs = {
            # Memory optimization
            "browser.cache.disk.enable": False,
            "browser.cache.memory.enable": False,
            "dom.ipc.processCount": 1,
            "browser.tabs.remote.autostart": False,
            "javascript.options.mem.max": 100000000,
            
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
        if profile_ready:
            options.add_argument(f"-profile")
            options.add_argument(PROFILE_PATH)
            self.logger.info("✅ Using Firefox profile with extensions")
        
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
        """Perform login"""
        try:
            # Email field
            try:
                email_field = self.browser.find_element(By.CSS_SELECTOR, "input[name='mail']")
                email_field.clear()
                email_field.send_keys(EMAIL)
                self.logger.info("✅ Email entered")
            except:
                self.logger.warning("⚠️ Email field not found")
            
            # Password field
            try:
                password_field = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.clear()
                password_field.send_keys(PASSWORD)
                self.logger.info("✅ Password entered")
            except:
                self.logger.warning("⚠️ Password field not found")
            
            # Login button
            try:
                login_btn = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_btn.click()
                self.logger.info("✅ Login button clicked")
            except:
                self.logger.warning("⚠️ Login button not found")
            
            time.sleep(10)
            
            # Verify login success
            if "surf" in self.browser.current_url:
                self.logger.info("✅ Login successful!")
                return True
            else:
                self.logger.warning("⚠️ Login may need manual verification")
                return True
                
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

    def log_status(self):
        """Log current status and system info"""
        memory = psutil.virtual_memory()
        self.logger.info(f"📊 Status: {self.credits} | Memory: {memory.percent}%")

    def run(self):
        """Main worker loop"""
        self.logger.info("🚀 Starting AdShare Background Worker...")
        self.monitoring = True
        
        # Setup browser
        if not self.setup_browser():
            self.logger.error("❌ Failed to setup browser, exiting...")
            return
        
        # Navigate to AdShare
        if not self.navigate_to_adshare():
            self.logger.warning("⚠️ Navigation issues, but continuing...")
        
        self.logger.info("🔄 Starting main monitoring loop...")
        
        cycle_count = 0
        consecutive_errors = 0
        
        while self.monitoring and consecutive_errors < 5:
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
                
                # Log status every hour
                if cycle_count % 36 == 0:
                    self.log_status()
                
                cycle_count += 1
                consecutive_errors = 0  # Reset error counter
                
                # Wait 100 seconds between cycles
                time.sleep(100)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                consecutive_errors += 1
                time.sleep(60)  # Wait before retry
        
        if consecutive_errors >= 5:
            self.logger.error("🚨 Too many consecutive errors, stopping worker...")
        
        self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("🧹 Cleaning up resources...")
        self.monitoring = False
        
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
        
        self.logger.info("✅ Worker stopped")

def main():
    """Main function"""
    worker = AdShareWorker()
    
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.logger.info("🛑 Worker interrupted by user")
        worker.cleanup()
    except Exception as e:
        worker.logger.error(f"💥 Worker crashed: {e}")
        worker.cleanup()
        # Restart after crash (Railway will handle this)
        raise e

if __name__ == '__main__':
    main()