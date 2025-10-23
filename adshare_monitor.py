#!/usr/bin/env python3
"""
Ultra-light Koyeb Memory Test - No OOM crashes
"""

import os
import sys
import time
import psutil

def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def test_system_limits():
    """Safe memory testing without allocations"""
    log("🔍 Starting Ultra-Light System Test")
    
    results = {}
    
    # 1. Basic system info (safe)
    try:
        memory = psutil.virtual_memory()
        results['total_mb'] = memory.total / 1024 / 1024
        results['available_mb'] = memory.available / 1024 / 1024
        results['used_mb'] = memory.used / 1024 / 1024
        
        log(f"Total RAM: {results['total_mb']:.1f} MB")
        log(f"Available: {results['available_mb']:.1f} MB") 
        log(f"Used: {results['used_mb']:.1f} MB")
    except Exception as e:
        log(f"❌ Memory check failed: {e}")
    
    # 2. Disk info (safe)
    try:
        disk = psutil.disk_usage('/')
        results['disk_total_gb'] = disk.total / 1024 / 1024 / 1024
        results['disk_free_gb'] = disk.free / 1024 / 1024 / 1024
        
        log(f"Disk Total: {results['disk_total_gb']:.1f} GB")
        log(f"Disk Free: {results['disk_free_gb']:.1f} GB")
    except Exception as e:
        log(f"❌ Disk check failed: {e}")
    
    # 3. CPU info (safe)
    try:
        results['cpu_cores'] = psutil.cpu_count()
        log(f"CPU Cores: {results['cpu_cores']}")
    except Exception as e:
        log(f"❌ CPU check failed: {e}")
    
    return results

def test_firefox_memory_safe():
    """Test Firefox memory usage safely"""
    log("🦊 Testing Firefox Memory (Safe Mode)")
    
    try:
        # Check if Firefox is even possible
        firefox_paths = [
            "/usr/bin/firefox",
            "/usr/bin/firefox-esr", 
            "/usr/local/bin/firefox"
        ]
        
        firefox_found = any(os.path.exists(path) for path in firefox_paths)
        
        if not firefox_found:
            log("❌ Firefox not installed")
            return None
        
        log("✅ Firefox is available")
        
        # Estimate memory usage based on system constraints
        available_memory = psutil.virtual_memory().available / 1024 / 1024
        
        # Conservative estimates
        firefox_base = 150  # MB (optimized)
        profile_overhead = 50  # MB (compressed)
        tab_memory = 50  # MB (your target)
        
        total_estimated = firefox_base + profile_overhead + tab_memory
        headroom = available_memory - total_estimated
        
        log(f"📊 Memory Estimation:")
        log(f"  Available: {available_memory:.1f} MB")
        log(f"  Firefox base: ~{firefox_base} MB")
        log(f"  Profile: ~{profile_overhead} MB") 
        log(f"  Tab: ~{tab_memory} MB")
        log(f"  Total needed: ~{total_estimated} MB")
        log(f"  Headroom: {headroom:.1f} MB")
        
        if headroom > 50:
            log("✅ SUCCESS: Should work with optimization")
            return True
        elif headroom > 0:
            log("⚠️  MARGINAL: Very tight, may crash")
            return True  
        else:
            log("❌ IMPOSSIBLE: Not enough memory")
            return False
            
    except Exception as e:
        log(f"❌ Firefox test failed: {e}")
        return False

def generate_report(results):
    """Generate safe report"""
    log("\n" + "="*50)
    log("📊 ULTRA-LIGHT TEST REPORT")
    log("="*50)
    
    if 'total_mb' in results:
        log(f"Total RAM: {results['total_mb']:.1f} MB")
        log(f"Available: {results['available_mb']:.1f} MB")
        
        # Calculate realistic capacity
        os_overhead = 100  # MB for OS
        python_overhead = 50  # MB for Python
        available_for_app = results['available_mb'] - os_overhead - python_overhead
        
        log(f"Realistic for app: ~{available_for_app:.1f} MB")
        
        if available_for_app < 200:
            log("❌ CRITICAL: Insufficient memory for Firefox + profile")
        elif available_for_app < 250:
            log("⚠️  MARGINAL: Will require heavy optimization")
        else:
            log("✅ ADEQUATE: Should work with optimization")
    
    log(f"\n💡 RECOMMENDATIONS:")
    log("1. Use ultra-light Firefox configuration")
    log("2. Pre-compress and optimize profile")
    log("3. Implement aggressive memory management")
    log("4. Consider lighter alternatives (requests + lxml)")

def main():
    log("🚀 Starting Ultra-Light Koyeb Test")
    
    try:
        # Test system limits safely
        results = test_system_limits()
        
        # Test Firefox feasibility
        firefox_possible = test_firefox_memory_safe()
        
        # Generate report
        generate_report(results)
        
        log(f"\n🎯 FINAL VERDICT: {'POSSIBLE with optimization' if firefox_possible else 'LIKELY IMPOSSIBLE'}")
        
    except Exception as e:
        log(f"💥 Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())