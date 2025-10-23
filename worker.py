#!/usr/bin/env python3
"""
FIXED AdShare Worker - All Issues Resolved
"""

import os
import time
import logging
import tarfile
import requests
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psutil

# ========== CONFIGURATION ==========
EMAIL = "loginallapps@gmail.com"
PASSWORD = "@Sd2007123"
PROFILE_PATH = "/app/firefox_profile"
PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_profile.tar.1.gz"

class FixedAdShareWorker:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        
        # Setup robust logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/app/worker.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_profile_fixed(self):
        """Fixed profile setup with proper path handling"""
        self.logger.info("📥 Setting up Firefox profile...")
        
        try:
            # Clear existing profile
            if os.path.exists(PROFILE_PATH):
                shutil.rmtree(PROFILE_PATH)
            os.makedirs(PROFILE_PATH, exist_ok=True)
            
            # Download profile
            self.logger.info("Downloading profile...")
            response = requests.get(PROFILE_URL, timeout=60, stream=True)
            response.raise_for_status()
            
            temp_path = "/app/temp_profile.tar.gz"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract and fix directory structure
            self.logger.info("Extracting profile...")
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall(PROFILE_PATH)
            
            # FIX: Find and move the actual profile files to root
            profile_found = False
            for root, dirs, files in os.walk(PROFILE_PATH):
                if "prefs.js" in files:
                    self.logger.info(f"Found profile at: {root}")
                    # Move all files from this directory to PROFILE_PATH root
                    for item in os.listdir(root):
                        src = os.path.join(root, item)
                        dst = os.path.join(PROFILE_PATH, item)
                        
                        # Remove if exists
                        if os.path.exists(dst):
                            if os.path.isdir(dst):
                                shutil.rmtree(dst)
                            else:
                                os.remove(dst)
                        
                        # Move file/directory
                        if os.path.isdir(src):
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)
                    
                    # Remove the now-empty source directory
                    if root != PROFILE_PATH:
                        shutil.rmtree(root)
                    
                    profile_found = True
                    break
            
            os.remove(temp_path)
            
            if profile_found and os.path.exists(os.path.join(PROFILE_PATH, "prefs.js")):
                self.logger.info("✅ Profile setup completed successfully")
                return True
            else:
                self.logger.warning("❌ No valid profile found in archive")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Profile setup failed: {e}")
            return False

    def setup_browser_fixed(self):
        """Fixed browser setup with compatibility settings"""
        self.logger.info("🦊 Setting up Firefox browser...")
        
        # Try to setup profile, but continue if it fails
        profile_ready = self.setup_profile_fixed()
        
        options = Options()
        options.headless = True
        
        # COMPATIBILITY FIX: Use stable preferences
        prefs = {
            # Memory optimization
            "browser.cache.disk.enable": False,
            "browser.cache.memory.enable": False,
            "dom.ipc.processCount": 1,
            "browser.tabs.remote.autostart": False,
            
            # JavaScript settings
            "javascript.options.mem.max": 80000000,  # 80MB
            
            # Extensions - keep enabled but limit
            "extensions.autoDisableScopes": 0,
            
            # Performance
            "browser.sessionstore.interval": 300000,
            "media.memory_cache_max_size": 0,
            
            # Security (compatibility)
            "security.sandbox.content.level": 0,
            
            # Disable updates
            "app.update.auto": False,
            "datareporting.healthreport.uploadEnabled": False,
            "toolkit.telemetry.enabled": False,
        }
        
        for pref, value in prefs.items():
            options.set_preference(pref, value)
        
        # FIX: Add compatibility arguments
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        
        # FIX: Use profile only if it's valid
        if profile_ready and os.path.exists(os.path.join(PROFILE_PATH, "prefs.js")):
            options.add_argument(f"-profile")
            options.add_argument(PROFILE_PATH)
            self.logger.info("✅ Using Firefox profile with extensions")
        else:
            self.logger.info("ℹ️ Using fresh Firefox instance")
        
        # FIX: Use Service with proper configuration
        service = Service(
            log_path="/app/geckodriver.log",
            service_args=[
                '--log', 'info',
                '--marionette-port', '2828'
            ]
        )
        
        try:
            self.logger.info("Starting Firefox...")
            self.browser = webdriver.Firefox(
                options=options,
                service=service
            )
            
            # Set reasonable window size
            self.browser.set_window_size(1280, 720)
            
            self.logger.info("✅ Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            
            # Try fallback without service
            try:
                self.logger.info("🔄 Trying fallback setup...")
                self.browser = webdriver.Firefox(options=options)
                self.logger.info("✅ Fallback browser started!")
                return True
            except Exception as e2:
                self.logger.error(f"❌ Fallback also failed: {e2}")
                return False

    def navigate_to_adshare(self):
        """Robust navigation with error handling"""
        self.logger.info("🌐 Navigating to AdShare...")
        
        try:
            self.browser.get("https://adsha.re/surf")
            
            # Wait for page to load
            WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            current_url = self.browser.current_url
            self.logger.info(f"📍 Current URL: {current_url}")
            
            # Check if login is needed
            if "login" in current_url.lower():
                self.logger.info("🔐 Login required, attempting...")
                return self.perform_login_robust()
            else:
                self.logger.info("✅ Already on surf page!")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {e}")
            return False

    def perform_login_robust(self):
        """Robust login with multiple attempts"""
        try:
            # Wait for page to stabilize
            time.sleep(5)
            
            # Try multiple email field selectors
            email_selectors = [
                "input[name='mail']",
                "input[type='email']",
                "input[placeholder*='email' i]",
                "input[id*='mail']"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"✅ Found email field with: {selector}")
                    break
                except:
                    continue
            
            if email_field:
                email_field.clear()
                email_field.send_keys(EMAIL)
                self.logger.info("✅ Email entered")
                time.sleep(1)
            
            # Try multiple password field selectors
            password_selectors = [
                "input[type='password']",
                "input[name='password']", 
                "input[placeholder*='password' i]",
                "input[id*='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"✅ Found password field with: {selector}")
                    break
                except:
                    continue
            
            if password_field:
                password_field.clear()
                password_field.send_keys(PASSWORD)
                self.logger.info("✅ Password entered")
                time.sleep(1)
            
            # Try multiple login button selectors
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
                        # Text-based search
                        buttons = self.browser.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if "login" in btn.text.lower():
                                login_btn = btn
                                break
                    else:
                        login_btn = self.browser.find_element(By.CSS_SELECTOR, selector)
                    
                    if login_btn:
                        self.logger.info(f"✅ Found login button with: {selector}")
                        break
                except:
                    continue
            
            if login_btn:
                login_btn.click()
                self.logger.info("✅ Login button clicked")
                
                # Wait for login to complete
                time.sleep(10)
                
                # Check if login was successful
                if "surf" in self.browser.current_url and "login" not in self.browser.current_url:
                    self.logger.info("✅ Login successful!")
                    return True
                else:
                    self.logger.warning("⚠️ Login may need manual verification")
                    return True  # Continue anyway
            else:
                self.logger.warning("⚠️ Login button not found, continuing...")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Login attempt failed: {e}")
            return False

    def check_credits(self):
        """Check credit balance"""
        try:
            page_source = self.browser.page_source.lower()
            import re
            
            # Multiple credit patterns
            patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*credits',
                r'credits.*?(\d{1,3}(?:,\d{3})*)',
                r'balance.*?(\d[\d,]*)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    self.credits = f"{matches[0]} Credits"
                    return True
            
            self.credits = "Not found"
            return False
            
        except Exception as e:
            self.credits = f"Error: {str(e)[:20]}"
            return False

    def log_system_status(self):
        """Log system resource usage"""
        try:
            memory = psutil.virtual_memory()
            self.logger.info(f"💾 System: Memory {memory.percent}% used")
        except:
            pass

    def run_monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("🔄 Starting monitoring loop...")
        self.monitoring = True
        
        cycle_count = 0
        consecutive_errors = 0
        
        while self.monitoring and consecutive_errors < 3:
            try:
                # Refresh page periodically
                if cycle_count % 6 == 0:  # Every 10 minutes
                    self.browser.refresh()
                    time.sleep(5)
                
                # Check credits every 30 minutes
                if cycle_count % 18 == 0:
                    if self.check_credits():
                        self.logger.info(f"💰 Credits: {self.credits}")
                    else:
                        self.logger.info("🔍 Checking page...")
                
                # Log system status every hour
                if cycle_count % 36 == 0:
                    self.log_system_status()
                
                cycle_count += 1
                consecutive_errors = 0
                
                # Wait 100 seconds
                time.sleep(100)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                consecutive_errors += 1
                time.sleep(60)
        
        if consecutive_errors >= 3:
            self.logger.error("🚨 Too many errors, stopping...")

    def run(self):
        """Main worker function"""
        self.logger.info("🚀 Starting AdShare Worker...")
        
        # Setup browser
        if not self.setup_browser_fixed():
            self.logger.error("❌ Failed to setup browser")
            return
        
        # Navigate to AdShare
        if not self.navigate_to_adshare():
            self.logger.warning("⚠️ Navigation issues, but continuing...")
        
        # Start monitoring
        self.run_monitoring_loop()
        
        self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("🧹 Cleaning up...")
        self.monitoring = False
        
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
        
        self.logger.info("✅ Worker stopped")

def main():
    """Main entry point"""
    worker = FixedAdShareWorker()
    
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.logger.info("🛑 Interrupted by user")
        worker.cleanup()
    except Exception as e:
        worker.logger.error(f"💥 Worker crashed: {e}")
        worker.cleanup()
        raise

if __name__ == '__main__':
    main()