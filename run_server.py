#!/usr/bin/env python3
"""
Simple server runner script for development and testing
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set Flask environment variables
os.environ['FLASK_APP'] = 'app.py'
os.environ['FLASK_ENV'] = 'development'

if __name__ == '__main__':
    try:
        from app import app
        print("Starting SDS Finder API server...")
        print("API will be available at: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
