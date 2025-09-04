"""
Flask API wrapper for find_sds functionality
Provides REST API endpoints for searching Safety Data Sheets by CAS number or product name
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union
import shutil
import traceback

from flask import Flask, request, jsonify, send_file
from werkzeug.exceptions import BadRequest

from find_sds.find_sds import find_sds as find_sds_by_cas, download_sds
from find_sds.find_sds import (
    extract_download_url_from_chemblink,
    extract_download_url_from_vwr,
    extract_download_url_from_fisher,
    extract_download_url_from_tci,
    extract_download_url_from_chemicalsafety,
    extract_download_url_from_fluorochem
)

app = Flask(__name__)

# Global configuration
TEMP_DIR = Path(tempfile.gettempdir()) / "sds_downloads"
TEMP_DIR.mkdir(exist_ok=True)

@app.route('/', methods=['GET'])
def home():
    """API documentation endpoint"""
    return jsonify({
        "message": "SDS Finder API",
        "version": "2.0.0",
        "description": "Search for Safety Data Sheets by CAS number or product name",
        "endpoints": {
            "/search/cas": {
                "method": "POST",
                "description": "Search for SDS by CAS number(s)",
                "parameters": {
                    "cas_numbers": "List of CAS numbers (required)",
                    "download": "Boolean to download files (optional, default: false)"
                }
            },
            "/search/product": {
                "method": "POST", 
                "description": "Search for SDS by product name(s)",
                "parameters": {
                    "product_names": "List of product names (required)",
                    "download": "Boolean to download files (optional, default: false)"
                }
            },
            "/search/mixed": {
                "method": "POST",
                "description": "Search for SDS by both CAS numbers and product names",
                "parameters": {
                    "cas_numbers": "List of CAS numbers (optional)",
                    "product_names": "List of product names (optional)", 
                    "download": "Boolean to download files (optional, default: false)"
                }
            }
        }
    })

@app.route('/search/cas', methods=['POST'])
def search_by_cas():
    """Search for SDS by CAS number(s)"""
    try:
        data = request.get_json()
        if not data or 'cas_numbers' not in data:
            return jsonify({"error": "cas_numbers parameter is required"}), 400
        
        cas_numbers = data['cas_numbers']
        download = data.get('download', False)
        
        if not isinstance(cas_numbers, list):
            cas_numbers = [cas_numbers]
        
        # Create unique download directory for this request
        request_id = str(uuid.uuid4())
        download_path = TEMP_DIR / request_id
        
        results = []
        
        if download:
            # Use existing find_sds function for bulk download
            find_sds_by_cas(cas_list=cas_numbers, download_path=str(download_path), pool_size=5)
            
            # Check which files were downloaded
            for cas_nr in cas_numbers:
                file_name = f"{cas_nr}-SDS.pdf"
                file_path = download_path / file_name
                
                results.append({
                    "cas_number": cas_nr,
                    "found": file_path.exists(),
                    "file_path": str(file_path) if file_path.exists() else None,
                    "download_url": f"/download/{request_id}/{file_name}" if file_path.exists() else None
                })
        else:
            # Just search for URLs without downloading
            for cas_nr in cas_numbers:
                found_info = search_sds_sources(cas_nr, search_type="cas")
                results.append({
                    "cas_number": cas_nr,
                    "found": found_info is not None,
                    "source": found_info[0] if found_info else None,
                    "url": found_info[1] if found_info else None
                })
        
        return jsonify({
            "request_id": request_id,
            "results": results,
            "total_searched": len(cas_numbers),
            "found_count": sum(1 for r in results if r['found'])
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/search/product', methods=['POST'])
def search_by_product():
    """Search for SDS by product name(s)"""
    try:
        data = request.get_json()
        if not data or 'product_names' not in data:
            return jsonify({"error": "product_names parameter is required"}), 400
        
        product_names = data['product_names']
        download = data.get('download', False)
        
        if not isinstance(product_names, list):
            product_names = [product_names]
        
        # Create unique download directory for this request
        request_id = str(uuid.uuid4())
        download_path = TEMP_DIR / request_id
        
        results = []
        
        for product_name in product_names:
            found_info = search_sds_sources(product_name, search_type="product")
            
            if found_info and download:
                # Download the file
                download_path.mkdir(exist_ok=True)
                file_name = f"{product_name.replace(' ', '_').replace('/', '_')}-SDS.pdf"
                file_path = download_path / file_name
                
                try:
                    import requests
                    headers = {
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36'
                    }
                    r = requests.get(found_info[1], headers=headers, timeout=20)
                    if r.status_code == 200:
                        with open(file_path, 'wb') as f:
                            f.write(r.content)
                        downloaded = True
                    else:
                        downloaded = False
                except:
                    downloaded = False
            else:
                downloaded = False
                file_path = None
            
            results.append({
                "product_name": product_name,
                "found": found_info is not None,
                "source": found_info[0] if found_info else None,
                "url": found_info[1] if found_info else None,
                "downloaded": downloaded if download else None,
                "download_url": f"/download/{request_id}/{file_path.name}" if downloaded else None
            })
        
        return jsonify({
            "request_id": request_id,
            "results": results,
            "total_searched": len(product_names),
            "found_count": sum(1 for r in results if r['found'])
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/search/mixed', methods=['POST'])
def search_mixed():
    """Search for SDS by both CAS numbers and product names"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        cas_numbers = data.get('cas_numbers', [])
        product_names = data.get('product_names', [])
        download = data.get('download', False)
        
        if not cas_numbers and not product_names:
            return jsonify({"error": "Either cas_numbers or product_names must be provided"}), 400
        
        # Create unique download directory for this request
        request_id = str(uuid.uuid4())
        download_path = TEMP_DIR / request_id
        
        results = []
        
        # Search by CAS numbers
        if cas_numbers:
            if not isinstance(cas_numbers, list):
                cas_numbers = [cas_numbers]
            
            for cas_nr in cas_numbers:
                found_info = search_sds_sources(cas_nr, search_type="cas")
                
                if found_info and download:
                    # Use existing download_sds function
                    download_path.mkdir(exist_ok=True)
                    cas_result = download_sds(cas_nr, str(download_path))
                    downloaded = cas_result[1]
                    file_name = f"{cas_nr}-SDS.pdf"
                    file_path = download_path / file_name
                else:
                    downloaded = False
                    file_path = None
                
                results.append({
                    "type": "cas",
                    "identifier": cas_nr,
                    "found": found_info is not None,
                    "source": found_info[0] if found_info else None,
                    "url": found_info[1] if found_info else None,
                    "downloaded": downloaded if download else None,
                    "download_url": f"/download/{request_id}/{file_name}" if downloaded else None
                })
        
        # Search by product names
        if product_names:
            if not isinstance(product_names, list):
                product_names = [product_names]
            
            for product_name in product_names:
                found_info = search_sds_sources(product_name, search_type="product")
                
                if found_info and download:
                    # Download the file
                    download_path.mkdir(exist_ok=True)
                    file_name = f"{product_name.replace(' ', '_').replace('/', '_')}-SDS.pdf"
                    file_path = download_path / file_name
                    
                    try:
                        import requests
                        headers = {
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36'
                        }
                        r = requests.get(found_info[1], headers=headers, timeout=20)
                        if r.status_code == 200:
                            with open(file_path, 'wb') as f:
                                f.write(r.content)
                            downloaded = True
                        else:
                            downloaded = False
                    except:
                        downloaded = False
                else:
                    downloaded = False
                    file_path = None
                
                results.append({
                    "type": "product",
                    "identifier": product_name,
                    "found": found_info is not None,
                    "source": found_info[0] if found_info else None,
                    "url": found_info[1] if found_info else None,
                    "downloaded": downloaded if download else None,
                    "download_url": f"/download/{request_id}/{file_path.name}" if downloaded else None
                })
        
        return jsonify({
            "request_id": request_id,
            "results": results,
            "total_searched": len(cas_numbers) + len(product_names),
            "found_count": sum(1 for r in results if r['found'])
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/download/<request_id>/<filename>', methods=['GET'])
def download_file(request_id, filename):
    """Download a previously found SDS file"""
    try:
        file_path = TEMP_DIR / request_id / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        return send_file(str(file_path), as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def search_sds_sources(query: str, search_type: str = "cas") -> Optional[tuple]:
    """
    Search all SDS sources for a given query (CAS number or product name)
    
    Args:
        query: CAS number or product name to search for
        search_type: "cas" or "product" to indicate search type
    
    Returns:
        Tuple of (source_name, url) if found, None otherwise
    """
    
    # Enable debug mode for better error handling
    import find_sds.find_sds as sds_module
    sds_module.debug = True
    
    if search_type == "cas":
        # Use existing CAS-based search functions
        return (
            extract_download_url_from_chemblink(query) or 
            extract_download_url_from_vwr(query) or 
            extract_download_url_from_fisher(query) or 
            extract_download_url_from_tci(query) or 
            extract_download_url_from_chemicalsafety(query) or 
            extract_download_url_from_fluorochem(query)
        )
    
    elif search_type == "product":
        # Use product name search functions (will be implemented)
        return (
            extract_download_url_from_chemicalsafety_by_name(query) or
            extract_download_url_from_vwr_by_name(query) or
            extract_download_url_from_fisher_by_name(query) or
            extract_download_url_from_tci_by_name(query) or
            extract_download_url_from_chemblink_by_name(query) or
            extract_download_url_from_fluorochem_by_name(query)
        )
    
    return None

# Import product name search functions
from find_sds.enhanced_search import (
    extract_download_url_from_chemicalsafety_by_name,
    extract_download_url_from_vwr_by_name,
    extract_download_url_from_fisher_by_name,
    extract_download_url_from_tci_by_name,
    extract_download_url_from_chemblink_by_name,
    extract_download_url_from_fluorochem_by_name
)

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
