"""Runtime hook to set SSL certificate path for curl_cffi"""
import os
import sys

# Find certifi bundle in the frozen app
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = sys._MEIPASS
    
    # Look for certifi cacert.pem in common locations
    possible_paths = [
        os.path.join(bundle_dir, 'certifi', 'cacert.pem'),
        os.path.join(bundle_dir, 'certifi', 'cacert.pem'),
        os.path.join(bundle_dir, '_internal', 'certifi', 'cacert.pem'),
    ]
    
    for cert_path in possible_paths:
        if os.path.exists(cert_path):
            os.environ['CURL_CA_BUNDLE'] = cert_path
            os.environ['SSL_CERT_FILE'] = cert_path
            os.environ['REQUESTS_CA_BUNDLE'] = cert_path
            print(f"[OK] SSL certificates loaded from: {cert_path}")
            break
    else:
        # If not found, disable SSL verification (not recommended but prevents crashes)
        os.environ['CURL_CA_BUNDLE'] = ''
        print("[WARNING] SSL certificates not found, verification may fail")
