import os
import requests
import tarfile
import zipfile
import shutil
import hashlib

print("🔍 DEBUGGING FIREFOX PROFILE DOWNLOAD")
print("=" * 50)

PROFILE_URL = "https://github.com/huijuo14/hextest/releases/download/v1.0/firefox_minimal.tar.gz"
PROFILE_BACKUP = "/tmp/firefox_profile.tar.gz"
PROFILE_PATH = "/tmp/firefox_profile"

# Cleanup
if os.path.exists(PROFILE_BACKUP):
    os.remove(PROFILE_BACKUP)
if os.path.exists(PROFILE_PATH):
    shutil.rmtree(PROFILE_PATH)
os.makedirs(PROFILE_PATH, exist_ok=True)

print("📥 Step 1: Downloading file...")
try:
    response = requests.get(PROFILE_URL, stream=True, timeout=60)
    total_size = int(response.headers.get('content-length', 0))
    print(f"   Expected size: {total_size} bytes")
    
    with open(PROFILE_BACKUP, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    actual_size = os.path.getsize(PROFILE_BACKUP)
    print(f"   Actual size: {actual_size} bytes")
    print(f"   Download {'✅ SUCCESS' if actual_size == total_size else '❌ CORRUPTED'}")
    
except Exception as e:
    print(f"   ❌ Download failed: {e}")
    exit(1)

print("\n🔍 Step 2: Analyzing file...")
try:
    # Check file type
    result = os.system(f'file "{PROFILE_BACKUP}"')
    
    # Calculate hash
    with open(PROFILE_BACKUP, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    print(f"   MD5 Hash: {file_hash}")
    
except Exception as e:
    print(f"   ❌ Analysis failed: {e}")

print("\n📦 Step 3: Testing extraction...")
try:
    # Try Python tarfile
    print("   Trying Python tarfile...")
    with tarfile.open(PROFILE_BACKUP, 'r:gz') as tar:
        members = tar.getmembers()
        print(f"   Found {len(members)} items in archive")
        for i, member in enumerate(members[:5]):  # Show first 5
            print(f"     {i+1}. {member.name} ({member.size} bytes)")
        if len(members) > 5:
            print(f"     ... and {len(members) - 5} more")
        
        # Try to extract
        tar.extractall(PROFILE_PATH)
        print("   ✅ Python extraction successful")
        
except Exception as e:
    print(f"   ❌ Python extraction failed: {e}")
    
    # Try system command
    print("   Trying system tar command...")
    result = os.system(f'tar -xzf "{PROFILE_BACKUP}" -C "{PROFILE_PATH}" 2>&1')
    if result == 0:
        print("   ✅ System extraction successful")
    else:
        print("   ❌ System extraction failed")

print("\n📁 Step 4: Checking extracted files...")
if os.path.exists(PROFILE_PATH):
    extracted_items = os.listdir(PROFILE_PATH)
    print(f"   Found {len(extracted_items)} items in {PROFILE_PATH}:")
    for item in extracted_items:
        item_path = os.path.join(PROFILE_PATH, item)
        if os.path.isdir(item_path):
            print(f"   📁 {item}/")
            sub_items = os.listdir(item_path)[:3]  # Show first 3
            for sub_item in sub_items:
                print(f"      └── {sub_item}")
            if len(os.listdir(item_path)) > 3:
                print(f"      └── ...")
        else:
            print(f"   📄 {item}")
else:
    print("   ❌ No extraction directory found")

print("\n" + "=" * 50)
print("🔧 SUMMARY:")
print(f"   Download: {'✅' if actual_size == total_size else '❌'}")
print(f"   Extraction: {'✅' if extracted_items else '❌'}")
print(f"   Profile ready: {'✅' if any('default' in item for item in extracted_items) else '❌'}")

if extracted_items:
    print("\n🎯 NEXT: Run the main monitor script")
else:
    print("\n💥 ISSUE: File is corrupted or extraction failed")