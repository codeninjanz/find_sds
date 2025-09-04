#!/usr/bin/python3.10

"""
WSGI file for PythonAnywhere deployment
This file should be uploaded as your WSGI configuration file
"""

import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/find_sds'  # Update this path to match your PythonAnywhere directory
if path not in sys.path:
    sys.path.insert(0, path)

# Import your Flask application
from app import app as application

if __name__ == "__main__":
    application.run()
