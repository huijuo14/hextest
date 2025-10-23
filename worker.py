#!/usr/bin/env python3
"""
MINIMAL AdShare Worker - Just Works
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== CONFIGURATION ==========
EMAIL = "loginallapps@gmail.com"
PASSWORD = "@Sd2007123"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinimalAdShareWorker:
    def __init__(self):
        self.browser = None
        self.monitoring = False

    def setup_browser_minimal(self):
        """Minimal browser setup that just works"""
        logger.info("🦊 Starting Firefox...")
        
        options = Options()
        options.headless = True
        
        # ABSOLUTE MINIMUM settings
        options.set_preference("dom.ipc.processCount", 1)
        options.set_preference("browser.tabs.remote.autostart", False)
        
        # Essential arguments
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.browser = webdriver.Firefox(options=options)
            logger.info("✅ Firefox started successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Browser failed: {e}")
            return False

    def navigate_and_login(self):
        """Simple navigation and login"""
        logger.info("🌐 Going to AdShare...")
        
        try:
            # Go directly to surf page
            self.browser.get("https://adsha.re/surf")
            
            # Wait for page to load
            WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(5)
            current_url = self.browser.current_url
            logger.info(f"📍 Current URL: {current_url}")
            
            # If login page, try simple login
            if "login" in current_url:
                logger.info("🔐 Trying login...")
                return self.simple_login()
            else:
                logger.info("✅ On surf page!")
                return True
                
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False

    def simple_login(self):
        """Simple login attempt"""
        try:
            # Try to find and fill email
            try:
                email = self.browser.find_element(By.CSS_SELECTOR, "input[name='mail']")
                email.send_keys(EMAIL)
                logger.info("✅ Email entered")
            except:
                logger.warning("⚠️ Email field not found")
            
            # Try to find and fill password  
            try:
                password = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
                password.send_keys(PASSWORD)
                logger.info("✅ Password entered")
            except:
                logger.warning("⚠️ Password field not found")
            
            # Try to click login button
            try:
                login_btn = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_btn.click()
                logger.info("✅ Login button clicked")
            except:
                logger.warning("⚠️ Login button not found")
            
            # Wait for login
            time.sleep(10)
            
            # Check result
            if "surf" in self.browser.current_url:
                logger.info("✅ Login successful!")
                return True
            else:
                logger.warning("⚠️ May need manual login")
                return True  # Continue anyway
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return True  # Continue anyway

    def keep_alive(self):
        """Keep the page alive"""
        logger.info("🔄 Keeping page alive...")
        self.monitoring = True
        
        cycle = 0
        
        while self.monitoring:
            try:
                # Refresh every 15 minutes
                if cycle % 9 == 0:
                    self.browser.refresh()
                    time.sleep(5)
                    logger.info("🔁 Page refreshed")
                
                cycle += 1
                
                # Wait 100 seconds
                time.sleep(100)
                    
            except Exception as e:
                logger.error(f"❌ Keep-alive error: {e}")
                time.sleep(60)

    def run(self):
        """Main function"""
        logger.info("🚀 Starting Minimal AdShare Worker")
        
        # Setup browser
        if not self.setup_browser_minimal():
            logger.error("💥 Cannot start - browser failed")
            return
        
        # Navigate and login
        if not self.navigate_and_login():
            logger.warning("⚠️ Navigation issues, but continuing...")
        
        # Keep alive
        self.keep_alive()
        
        # Cleanup
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
        
        logger.info("🛑 Worker stopped")

def main():
    worker = MinimalAdShareWorker()
    
    try:
        worker.run()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"💥 Worker crashed: {e}")

if __name__ == '__main__':
    main()