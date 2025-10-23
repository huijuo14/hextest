#!/usr/bin/env python3
"""
DEBUG AdShare Monitor - Full logging to find crash reason
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
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import psutil

# ========== CONFIGURATION ==========
EMAIL = "loginallapps@gmail.com"
PASSWORD = "@Sd2007123"
PROFILE_PATH = "/app/firefox_profile"
PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_profile.tar.1.gz"

app = Flask(__name__)

class DebugAdShareMonitor:
    def __init__(self):
        self.browser = None
        self.monitoring = False
        self.credits = "Unknown"
        self.status = "Initializing"
        self.start_time = time.time()
        
        # Setup DEBUG logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/app/debug.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def debug_system_info(self):
        """Debug system information"""
        self.logger.debug("=== SYSTEM DEBUG INFO ===")
        
        # Check Firefox
        try:
            firefox_version = subprocess.check_output(['firefox', '--version'], stderr=subprocess.STDOUT)
            self.logger.debug(f"Firefox: {firefox_version.decode().strip()}")
        except Exception as e:
            self.logger.debug(f"Firefox check failed: {e}")
        
        # Check geckodriver
        try:
            gecko_version = subprocess.check_output(['geckodriver', '--version'], stderr=subprocess.STDOUT)
            self.logger.debug(f"Geckodriver: {gecko_version.decode().strip()}")
        except Exception as e:
            self.logger.debug(f"Geckodriver check failed: {e}")
        
        # Check memory
        memory = psutil.virtual_memory()
        self.logger.debug(f"Memory: {memory.available/1024/1024:.1f}MB available of {memory.total/1024/1024:.1f}MB total")
        
        # Check disk
        disk = psutil.disk_usage('/')
        self.logger.debug(f"Disk: {disk.free/1024/1024/1024:.1f}GB free")

    def download_profile(self):
        """Download and extract profile"""
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
            
            self.logger.debug(f"Downloaded: {os.path.getsize(temp_path)} bytes")
            
            # Extract
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall(PROFILE_PATH)
            
            # List extracted files
            extracted_files = []
            for root, dirs, files in os.walk(PROFILE_PATH):
                for file in files:
                    extracted_files.append(os.path.relpath(os.path.join(root, file), PROFILE_PATH))
            
            self.logger.debug(f"Extracted {len(extracted_files)} files")
            self.logger.debug(f"Sample files: {extracted_files[:10]}")
            
            os.remove(temp_path)
            self.logger.info("✅ Profile downloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Profile download failed: {e}")
            return False

    def setup_browser_with_debug(self):
        """Setup browser with maximum debug info"""
        self.logger.info("🦊 Setting up Firefox with DEBUG...")
        
        # Download profile first
        if not self.download_profile():
            self.logger.warning("⚠️ Continuing without profile")
            return False
        
        options = Options()
        options.headless = True
        
        # DEBUG preferences - enable all logging
        debug_prefs = {
            # Enable all logging
            "browser.dom.window.dump.enabled": True,
            "devtools.console.stdout.content": True,
            "devtools.debugger.remote-enabled": True,
            "devtools.chrome.enabled": True,
            
            # Memory limits
            "browser.cache.disk.enable": False,
            "browser.cache.memory.enable": False,
            "dom.ipc.processCount": 1,
            "browser.tabs.remote.autostart": False,
            "javascript.options.mem.max": 80000000,
            
            # Keep extensions
            "extensions.autoDisableScopes": 0,
        }
        
        for pref, value in debug_prefs.items():
            options.set_preference(pref, value)
        
        # Add debug arguments
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--verbose")
        options.add_argument("--log-level=0")  # Maximum logging
        
        # Use profile
        options.add_argument(f"-profile")
        options.add_argument(PROFILE_PATH)
        
        # Service with debug logging
        service = Service(
            log_path="/app/geckodriver.log",
            service_args=['--log', 'debug']
        )
        
        try:
            self.logger.debug("🚀 Starting Firefox process...")
            
            # Start browser with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Browser startup timeout")
            
            # Set timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
            
            self.browser = webdriver.Firefox(
                options=options,
                service=service
            )
            
            # Cancel timeout
            signal.alarm(0)
            
            self.logger.info("✅ Firefox started successfully!")
            
            # Test browser functionality
            self.browser.get("about:blank")
            self.logger.debug("✅ Browser basic functionality test passed")
            
            return True
            
        except TimeoutError:
            self.logger.error("❌ Browser startup timeout")
            return False
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            self.logger.debug(f"Exception type: {type(e)}")
            self.logger.debug(f"Exception args: {e.args}")
            
            # Try to get more info from geckodriver log
            if os.path.exists("/app/geckodriver.log"):
                with open("/app/geckodriver.log", "r") as f:
                    gecko_log = f.read()
                    self.logger.debug(f"Geckodriver log: {gecko_log[-1000:]}")  # Last 1000 chars
            
            return False

    def test_browser_manually(self):
        """Test browser startup manually to see exact error"""
        self.logger.info("🔧 Testing browser manually...")
        
        try:
            # Test Firefox directly
            result = subprocess.run(
                ['firefox', '--headless', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.logger.debug(f"Firefox test stdout: {result.stdout}")
            self.logger.debug(f"Firefox test stderr: {result.stderr}")
            
            # Test with profile
            result = subprocess.run([
                'firefox', 
                '--headless',
                '-profile', PROFILE_PATH,
                '--screenshot', '/app/test.png',
                'about:blank'
            ], capture_output=True, text=True, timeout=30)
            
            self.logger.debug(f"Firefox with profile stdout: {result.stdout}")
            self.logger.debug(f"Firefox with profile stderr: {result.stderr}")
            
            if result.returncode == 0:
                self.logger.info("✅ Manual Firefox test PASSED")
                return True
            else:
                self.logger.error(f"❌ Manual Firefox test FAILED: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Manual test failed: {e}")
            return False

    def start_monitoring(self):
        """Start monitoring with full debug"""
        self.logger.info("🚀 Starting DEBUG AdShare monitor...")
        
        # Debug system first
        self.debug_system_info()
        
        # Test browser manually
        if not self.test_browser_manually():
            self.logger.error("❌ Manual browser test failed")
            return False
        
        # Try Selenium setup
        if not self.setup_browser_with_debug():
            self.logger.error("❌ Selenium browser setup failed")
            return False
        
        self.logger.info("✅ DEBUG setup completed successfully!")
        return True

# Global monitor instance
monitor = DebugAdShareMonitor()

# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    return jsonify({
        "status": "DEBUG AdShare Monitor",
        "monitor_status": monitor.status,
        "message": "Check /app/debug.log for detailed logs"
    })

@app.route('/start')
def start_monitor():
    if not monitor.monitoring:
        success = monitor.start_monitoring()
        return jsonify({
            "status": "started" if success else "failed",
            "logs": "Check /app/debug.log and /app/geckodriver.log"
        })
    return jsonify({"status": "already_running"})

@app.route('/debug/logs')
def get_logs():
    """Get recent logs"""
    try:
        with open('/app/debug.log', 'r') as f:
            logs = f.read().split('\n')[-50:]  # Last 50 lines
        return jsonify({"recent_logs": logs})
    except:
        return jsonify({"error": "No logs yet"})

@app.route('/health')
def health_check():
    return jsonify({"status": "debug_mode"})

# Auto-start
def initialize():
    time.sleep(5)
    monitor.start_monitoring()

init_thread = threading.Thread(target=initialize)
init_thread.daemon = True
init_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)