#!/usr/bin/env python3
"""
Koyeb Free Tier Limits Test Script
Tests RAM, CPU, Disk, and Browser capabilities
"""

import os
import sys
import time
import psutil
import resource
import threading
import subprocess
from datetime import datetime

class KoyebTester:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_memory_limits(self):
        """Test RAM allocation and limits"""
        self.log("🧠 Testing Memory Limits...")
        
        # Current memory usage
        memory = psutil.virtual_memory()
        self.results['memory_total'] = memory.total / 1024 / 1024  # MB
        self.results['memory_available'] = memory.available / 1024 / 1024
        self.results['memory_used'] = memory.used / 1024 / 1024
        
        # Try to allocate memory progressively
        self.log("Testing memory allocation...")
        chunks = []
        chunk_size = 50  # MB
        max_allocated = 0
        
        try:
            for i in range(10):  # Try up to 500MB
                # Allocate chunk (in bytes)
                chunk = bytearray(chunk_size * 1024 * 1024)
                chunks.append(chunk)
                max_allocated = len(chunks) * chunk_size
                self.log(f"✓ Allocated {max_allocated} MB")
                time.sleep(0.5)
                
        except MemoryError:
            self.log(f"💥 Memory limit reached at {max_allocated} MB")
        
        self.results['max_allocated_memory'] = max_allocated
        
        # Clean up
        del chunks
        return max_allocated
    
    def test_cpu_performance(self):
        """Test CPU capabilities"""
        self.log("⚡ Testing CPU Performance...")
        
        # CPU info
        self.results['cpu_cores'] = psutil.cpu_count()
        self.results['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown"
        
        # CPU stress test
        self.log("Running CPU stress test (10 seconds)...")
        start_time = time.time()
        iterations = 0
        
        def cpu_worker():
            nonlocal iterations
            while time.time() - start_time < 10:
                # Some CPU-intensive work
                _ = [i**2 for i in range(10000)]
                iterations += 1
        
        threads = []
        for _ in range(self.results['cpu_cores']):
            t = threading.Thread(target=cpu_worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        self.results['cpu_iterations'] = iterations
        self.results['cpu_test_duration'] = time.time() - start_time
        
        return iterations
    
    def test_disk_limits(self):
        """Test disk space and I/O"""
        self.log("💾 Testing Disk Limits...")
        
        disk = psutil.disk_usage('/')
        self.results['disk_total'] = disk.total / 1024 / 1024 / 1024  # GB
        self.results['disk_used'] = disk.used / 1024 / 1024 / 1024
        self.results['disk_free'] = disk.free / 1024 / 1024 / 1024
        
        # Test file I/O
        self.log("Testing file I/O performance...")
        start_time = time.time()
        
        test_file = "disk_test.bin"
        file_size = 100  # MB
        
        try:
            # Write test
            with open(test_file, 'wb') as f:
                data = os.urandom(1024 * 1024)  # 1MB chunks
                for _ in range(file_size):
                    f.write(data)
            
            # Read test
            with open(test_file, 'rb') as f:
                while f.read(1024 * 1024):
                    pass
            
            write_read_time = time.time() - start_time
            self.results['disk_io_speed'] = (file_size * 2) / write_read_time  # MB/s
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
        
        return self.results['disk_io_speed']
    
    def test_firefox_memory(self):
        """Test Firefox memory usage with Selenium"""
        self.log("🦊 Testing Firefox Memory Usage...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.firefox.options import Options
            
            options = Options()
            options.headless = True
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Memory optimization
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("dom.ipc.processCount", 1)
            
            self.log("Starting Firefox...")
            
            # Measure memory before
            memory_before = psutil.virtual_memory().used / 1024 / 1024
            
            driver = webdriver.Firefox(options=options)
            
            # Measure memory after startup
            time.sleep(3)
            memory_after_start = psutil.virtual_memory().used / 1024 / 1024
            firefox_start_memory = memory_after_start - memory_before
            
            self.log(f"Firefox startup memory: {firefox_start_memory:.1f} MB")
            
            # Test loading a page
            self.log("Loading test page...")
            driver.get("https://httpbin.org/html")
            
            time.sleep(2)
            memory_after_page = psutil.virtual_memory().used / 1024 / 1024
            firefox_page_memory = memory_after_page - memory_before
            
            self.log(f"Firefox with page memory: {firefox_page_memory:.1f} MB")
            
            self.results['firefox_start_memory'] = firefox_start_memory
            self.results['firefox_page_memory'] = firefox_page_memory
            
            driver.quit()
            return firefox_page_memory
            
        except Exception as e:
            self.log(f"❌ Firefox test failed: {e}")
            self.results['firefox_error'] = str(e)
            return None
    
    def test_profile_loading(self, profile_path=None):
        """Test profile loading memory impact"""
        self.log("📁 Testing Profile Loading...")
        
        if profile_path and os.path.exists(profile_path):
            # Measure profile size
            profile_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(profile_path)
                for filename in filenames
            ) / 1024 / 1024  # MB
            
            self.results['profile_size'] = profile_size
            self.log(f"Profile size: {profile_size:.1f} MB")
        
        return profile_size if profile_path else 0
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.log("\n" + "="*50)
        self.log("📊 KOYEB FREE TIER TEST REPORT")
        self.log("="*50)
        
        # System Info
        self.log(f"System: {os.uname().sysname} {os.uname().release}")
        self.log(f"Python: {sys.version.split()[0]}")
        
        # Memory Results
        self.log(f"\n🧠 MEMORY RESULTS:")
        self.log(f"Total RAM: {self.results.get('memory_total', 0):.1f} MB")
        self.log(f"Available RAM: {self.results.get('memory_available', 0):.1f} MB")
        self.log(f"Used RAM: {self.results.get('memory_used', 0):.1f} MB")
        self.log(f"Max Allocated: {self.results.get('max_allocated_memory', 0)} MB")
        
        # CPU Results
        self.log(f"\n⚡ CPU RESULTS:")
        self.log(f"CPU Cores: {self.results.get('cpu_cores', 0)}")
        self.log(f"CPU Frequency: {self.results.get('cpu_freq', 'Unknown')} MHz")
        self.log(f"CPU Performance: {self.results.get('cpu_iterations', 0):,} iterations")
        
        # Disk Results
        self.log(f"\n💾 DISK RESULTS:")
        self.log(f"Total Disk: {self.results.get('disk_total', 0):.1f} GB")
        self.log(f"Free Disk: {self.results.get('disk_free', 0):.1f} GB")
        self.log(f"Disk I/O Speed: {self.results.get('disk_io_speed', 0):.1f} MB/s")
        
        # Firefox Results
        if 'firefox_start_memory' in self.results:
            self.log(f"\n🦊 FIREFOX RESULTS:")
            self.log(f"Startup Memory: {self.results['firefox_start_memory']:.1f} MB")
            self.log(f"With Page Memory: {self.results['firefox_page_memory']:.1f} MB")
        
        # Profile Results
        if 'profile_size' in self.results:
            self.log(f"Profile Size: {self.results['profile_size']:.1f} MB")
        
        # Assessment
        self.log(f"\n🎯 ASSESSMENT:")
        total_memory = self.results.get('memory_total', 0)
        firefox_memory = self.results.get('firefox_page_memory', 300)  # Default estimate
        
        if total_memory > 0:
            available_for_tab = total_memory - firefox_memory - 100  # 100MB for OS/Python
            self.log(f"Available for your 50MB tab: {available_for_tab:.1f} MB")
            
            if available_for_tab >= 50:
                self.log("✅ SUCCESS: Should handle your 50MB tab!")
            else:
                self.log("❌ MARGINAL: Memory is very tight")
                self.log(f"Need: {50 - available_for_tab:.1f} MB more")
        
        self.log(f"\n⏱️ Total test duration: {(datetime.now() - self.start_time).total_seconds():.1f}s")

def main():
    tester = KoyebTester()
    
    try:
        # Run tests
        tester.test_memory_limits()
        tester.test_cpu_performance()
        tester.test_disk_limits()
        tester.test_firefox_memory()
        
        # Test with profile if provided as argument
        if len(sys.argv) > 1:
            tester.test_profile_loading(sys.argv[1])
        
        # Generate report
        tester.generate_report()
        
    except Exception as e:
        tester.log(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()