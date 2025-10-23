#!/usr/bin/env python3
"""
DEBUG Worker - Find exact Firefox crash reason
"""

import os
import time
import logging
import tarfile
import requests
import subprocess
import sys

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/debug.log')
    ]
)
logger = logging.getLogger(__name__)

def debug_system():
    """Debug system information"""
    logger.info("🔧 DEBUG SYSTEM INFORMATION")
    
    # Check Firefox
    try:
        result = subprocess.run(['firefox', '--version'], capture_output=True, text=True)
        logger.info(f"Firefox version: {result.stdout.strip()}")
    except Exception as e:
        logger.error(f"Firefox check failed: {e}")
    
    # Check geckodriver
    try:
        result = subprocess.run(['geckodriver', '--version'], capture_output=True, text=True)
        logger.info(f"Geckodriver: {result.stdout.splitlines()[0]}")
    except Exception as e:
        logger.error(f"Geckodriver check failed: {e}")
    
    # Check memory
    try:
        import psutil
        memory = psutil.virtual_memory()
        logger.info(f"Memory: {memory.total/1024/1024:.0f}MB total, {memory.available/1024/1024:.0f}MB available")
    except:
        logger.warning("Could not check memory")

def test_firefox_directly():
    """Test Firefox directly without Selenium"""
    logger.info("🧪 TESTING FIREFOX DIRECTLY")
    
    tests = [
        # Test 1: Basic Firefox
        {
            'name': 'Basic Firefox',
            'cmd': ['firefox', '--headless', '--version'],
            'timeout': 10
        },
        # Test 2: Firefox with simple page
        {
            'name': 'Firefox with about:blank', 
            'cmd': ['firefox', '--headless', '--screenshot', '/app/test1.png', 'about:blank'],
            'timeout': 30
        },
        # Test 3: Firefox with memory limits
        {
            'name': 'Firefox with memory limits',
            'cmd': ['firefox', '--headless', '--screenshot', '/app/test2.png', '--window-size=800,600', 'about:blank'],
            'timeout': 30
        }
    ]
    
    for test in tests:
        logger.info(f"🧪 Running: {test['name']}")
        try:
            result = subprocess.run(
                test['cmd'],
                capture_output=True,
                text=True,
                timeout=test['timeout']
            )
            logger.info(f"  Return code: {result.returncode}")
            if result.stdout:
                logger.info(f"  stdout: {result.stdout.strip()}")
            if result.stderr:
                logger.info(f"  stderr: {result.stderr.strip()}")
                
            if result.returncode == 0:
                logger.info(f"  ✅ {test['name']} PASSED")
            else:
                logger.info(f"  ❌ {test['name']} FAILED")
                
        except subprocess.TimeoutExpired:
            logger.error(f"  ⏰ {test['name']} TIMEOUT")
        except Exception as e:
            logger.error(f"  💥 {test['name']} ERROR: {e}")

def test_with_profile():
    """Test Firefox with the profile"""
    logger.info("📁 TESTING WITH PROFILE")
    
    PROFILE_PATH = "/app/firefox_profile"
    PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_profile.tar.1.gz"
    
    try:
        # Download profile
        if os.path.exists(PROFILE_PATH):
            import shutil
            shutil.rmtree(PROFILE_PATH)
        os.makedirs(PROFILE_PATH, exist_ok=True)
        
        logger.info("📥 Downloading profile...")
        response = requests.get(PROFILE_URL, timeout=60, stream=True)
        with open('/app/temp.tar.gz', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract
        logger.info("📦 Extracting profile...")
        with tarfile.open('/app/temp.tar.gz', 'r:gz') as tar:
            tar.extractall(PROFILE_PATH)
        
        # List what we extracted
        extracted = []
        for root, dirs, files in os.walk(PROFILE_PATH):
            for file in files[:10]:  # First 10 files
                extracted.append(os.path.relpath(os.path.join(root, file), PROFILE_PATH))
        logger.info(f"📄 Sample files: {extracted}")
        
        # Test Firefox with profile
        logger.info("🧪 Testing Firefox with profile...")
        result = subprocess.run([
            'firefox', '--headless',
            '-profile', PROFILE_PATH,
            '--screenshot', '/app/test_profile.png',
            'about:blank'
        ], capture_output=True, text=True, timeout=60)
        
        logger.info(f"Profile test return code: {result.returncode}")
        if result.stdout:
            logger.info(f"Profile stdout: {result.stdout}")
        if result.stderr:
            logger.info(f"Profile stderr: {result.stderr}")
            
        os.remove('/app/temp.tar.gz')
        
    except Exception as e:
        logger.error(f"❌ Profile test failed: {e}")

def test_selenium_simple():
    """Test Selenium with simplest possible setup"""
    logger.info("🕸️ TESTING SELENIUM")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        
        # Absolute minimum setup
        options = Options()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # NO preferences, NO profile
        logger.info("🚀 Starting Selenium Firefox...")
        driver = webdriver.Firefox(options=options)
        
        logger.info("✅ Selenium started successfully!")
        
        # Test basic navigation
        driver.get("about:blank")
        logger.info("✅ Basic navigation works!")
        
        driver.quit()
        logger.info("✅ Selenium test COMPLETE!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Selenium test failed: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all debug tests"""
    logger.info("🐛 STARTING DEBUG SESSION")
    
    # Test 1: System info
    debug_system()
    time.sleep(2)
    
    # Test 2: Firefox directly
    test_firefox_directly()
    time.sleep(2)
    
    # Test 3: With profile
    test_with_profile()
    time.sleep(2)
    
    # Test 4: Selenium
    test_selenium_simple()
    
    logger.info("🎯 DEBUG COMPLETE - Check logs above for the exact issue!")

if __name__ == '__main__':
    main()