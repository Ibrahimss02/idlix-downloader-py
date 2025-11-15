"""Runtime hook to catch and log all crashes to file"""
import sys
import traceback
import os
from datetime import datetime

def exception_handler(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions to file before crashing"""
    log_file = os.path.join(os.path.dirname(sys.executable), 'idlix_crash.log')
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "="*80 + "\n")
            f.write(f"CRASH REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # Write exception details
            f.write(f"Exception Type: {exc_type.__name__}\n")
            f.write(f"Exception Value: {exc_value}\n\n")
            
            # Write full traceback
            f.write("Traceback:\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            
            # Write system info
            f.write("\n" + "-"*80 + "\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"Executable: {sys.executable}\n")
            f.write(f"Working Directory: {os.getcwd()}\n")
            f.write(f"Arguments: {sys.argv}\n")
            f.write("-"*80 + "\n")
        
        # Print to console too
        print("\n" + "="*80)
        print("APPLICATION CRASHED!")
        print("="*80)
        print(f"\nError: {exc_type.__name__}: {exc_value}")
        print(f"\nFull error details saved to: {log_file}")
        print("\nPlease share this file if you need help debugging.")
        print("="*80 + "\n")
        
    except Exception as log_error:
        # If logging fails, at least print to console
        print(f"\nFailed to write crash log: {log_error}")
        print(f"\nOriginal error: {exc_type.__name__}: {exc_value}")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # Don't wait for input in non-interactive environments
    if sys.stdin and sys.stdin.isatty():
        input("\nPress Enter to exit...")

# Install exception handler
sys.excepthook = exception_handler

print("[OK] Crash logging enabled - errors will be saved to idlix_crash.log")
