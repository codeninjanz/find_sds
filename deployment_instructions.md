# PythonAnywhere Deployment Instructions

## Setup Steps

1. **Upload files to PythonAnywhere**
   - Upload all files to your home directory (e.g., `/home/yourusername/find_sds/`)
   - Make sure the directory structure is preserved

2. **Install dependencies**
   - Open a Bash console on PythonAnywhere
   - Navigate to your project directory: `cd ~/find_sds`
   - Install requirements: `pip3.10 install --user -r requirements.txt`

3. **Configure Web App**
   - Go to the "Web" tab in your PythonAnywhere dashboard
   - Click "Add a new web app"
   - Choose "Manual configuration" and Python 3.10
   - Set the source code directory to `/home/yourusername/find_sds`
   - Edit the WSGI configuration file and replace its contents with the contents of `flask_app.py`
   - Update the path in `flask_app.py` to match your actual PythonAnywhere directory

4. **Update WSGI Configuration**
   ```python
   #!/usr/bin/python3.10
   
   import sys
   import os
   
   # Add your project directory to the Python path
   path = '/home/yourusername/find_sds'  # Update 'yourusername' with your actual username
   if path not in sys.path:
       sys.path.insert(0, path)
   
   from app import app as application
   
   if __name__ == "__main__":
       application.run()
   ```

5. **Reload the web app** from the Web tab

## API Endpoints

Once deployed, your API will be available at:
- `https://yourusername.pythonanywhere.com/` - API documentation
- `https://yourusername.pythonanywhere.com/search/cas` - Search by CAS number
- `https://yourusername.pythonanywhere.com/search/product` - Search by product name  
- `https://yourusername.pythonanywhere.com/search/mixed` - Search by both CAS and product name

## Testing the API

### Search by CAS Number
```bash
curl -X POST https://yourusername.pythonanywhere.com/search/cas \
  -H "Content-Type: application/json" \
  -d '{"cas_numbers": ["67-63-0", "75-09-2"], "download": false}'
```

### Search by Product Name
```bash
curl -X POST https://yourusername.pythonanywhere.com/search/product \
  -H "Content-Type: application/json" \
  -d '{"product_names": ["Isopropanol", "Acetone"], "download": false}'
```

### Mixed Search
```bash
curl -X POST https://yourusername.pythonanywhere.com/search/mixed \
  -H "Content-Type: application/json" \
  -d '{"cas_numbers": ["67-63-0"], "product_names": ["Acetone"], "download": false}'
```

## File Structure
```
find_sds/
├── app.py                      # Main Flask application
├── flask_app.py               # WSGI configuration for PythonAnywhere
├── requirements.txt           # Python dependencies
├── deployment_instructions.md # This file
├── find_sds/
│   ├── __init__.py
│   ├── find_sds.py           # Original SDS search functionality
│   └── enhanced_search.py    # Product name search functionality
├── tests/
│   └── ...                   # Test files
└── ...
```

## Troubleshooting

1. **Import errors**: Make sure the path in `flask_app.py` is correct
2. **Module not found**: Ensure all dependencies are installed with `pip3.10 install --user`
3. **Permission errors**: Check that all files have appropriate read permissions
4. **Timeout errors**: The free tier has request timeouts; consider upgrading for longer-running searches

## Notes

- The free tier has daily CPU seconds limits
- Downloaded files are temporarily stored and cleaned up automatically
- For production use, consider implementing proper logging and error handling
- The API supports both single items and lists for batch processing
