import sys
print(f"Using Python interpreter: {sys.executable}")
print(f"Python path: {sys.path}")
try:
    from python_json_logger import jsonlogger
    print("\nSUCCESS: 'python_json_logger' imported successfully!")
except ImportError as e:
    print(f"\nERROR: Failed to import 'python_json_logger'.")
    print(f"Error details: {e}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
