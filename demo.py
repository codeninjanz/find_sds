#!/usr/bin/env python3
"""
Demonstration script for the enhanced SDS Finder API
Shows both the original library usage and new API capabilities
"""

import requests
import json
import time
import sys
from pathlib import Path

def demo_library_usage():
    """Demonstrate the original library functionality"""
    print("=" * 60)
    print("DEMO: Original Library Functionality")
    print("=" * 60)
    
    try:
        from find_sds.find_sds import find_sds
        
        print("Searching for SDS using CAS numbers...")
        cas_list = ['67-63-0', '75-09-2']  # Isopropanol, Dichloromethane
        
        # Create a demo directory
        demo_dir = Path('./demo_downloads')
        demo_dir.mkdir(exist_ok=True)
        
        find_sds(cas_list=cas_list, download_path=str(demo_dir), pool_size=2)
        
        print(f"\nCheck the '{demo_dir}' directory for downloaded SDS files.")
        
    except ImportError:
        print("Library not available for demo")
    except Exception as e:
        print(f"Demo error: {e}")

def demo_api_usage(base_url="http://localhost:5000"):
    """Demonstrate the new API functionality"""
    print("\n" + "=" * 60)
    print("DEMO: New API Functionality")
    print("=" * 60)
    
    # Test if API is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code != 200:
            print(f"API not responding at {base_url}")
            print("Start the API with: python run_server.py")
            return
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to API at {base_url}")
        print("Start the API with: python run_server.py")
        return
    
    print(f"API running at: {base_url}")
    
    # Demo 1: CAS number search
    print("\n1. Searching by CAS numbers...")
    cas_data = {
        "cas_numbers": ["67-63-0", "75-09-2"],
        "download": False
    }
    
    response = requests.post(f"{base_url}/search/cas", 
                           headers={"Content-Type": "application/json"},
                           data=json.dumps(cas_data))
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['found_count']} out of {data['total_searched']} SDS")
        for result in data['results']:
            status = "✓ Found" if result['found'] else "✗ Not found"
            source = f" ({result.get('source', 'Unknown')})" if result['found'] else ""
            print(f"   {result['cas_number']}: {status}{source}")
    else:
        print(f"   Error: {response.status_code}")
    
    # Demo 2: Product name search
    print("\n2. Searching by product names...")
    product_data = {
        "product_names": ["Isopropanol", "Acetone"],
        "download": False
    }
    
    response = requests.post(f"{base_url}/search/product",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps(product_data))
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['found_count']} out of {data['total_searched']} SDS")
        for result in data['results']:
            status = "✓ Found" if result['found'] else "✗ Not found"
            source = f" ({result.get('source', 'Unknown')})" if result['found'] else ""
            print(f"   {result['product_name']}: {status}{source}")
    else:
        print(f"   Error: {response.status_code}")
    
    # Demo 3: Mixed search
    print("\n3. Mixed search (CAS + Product names)...")
    mixed_data = {
        "cas_numbers": ["67-63-0"],
        "product_names": ["Benzene"],
        "download": False
    }
    
    response = requests.post(f"{base_url}/search/mixed",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps(mixed_data))
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['found_count']} out of {data['total_searched']} SDS")
        for result in data['results']:
            status = "✓ Found" if result['found'] else "✗ Not found"
            source = f" ({result.get('source', 'Unknown')})" if result['found'] else ""
            search_type = result.get('type', 'unknown')
            identifier = result.get('identifier', 'unknown')
            print(f"   {identifier} ({search_type}): {status}{source}")
    else:
        print(f"   Error: {response.status_code}")
    
    # Demo 4: Download demonstration
    print("\n4. Download demonstration...")
    download_data = {
        "cas_numbers": ["67-63-0"],  # Just one for demo
        "download": True
    }
    
    print("   Downloading SDS file...")
    response = requests.post(f"{base_url}/search/cas",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps(download_data))
    
    if response.status_code == 200:
        data = response.json()
        for result in data['results']:
            if result['found'] and result.get('download_url'):
                print(f"   ✓ File available at: {base_url}{result['download_url']}")
            elif result['found']:
                print(f"   ✓ SDS found but download failed")
            else:
                print(f"   ✗ SDS not found for {result['cas_number']}")
    else:
        print(f"   Error: {response.status_code}")

def main():
    print("SDS Finder API - Enhanced Features Demo")
    print("This demo showcases both original and new functionality\n")
    
    # Demo library usage
    demo_library_usage()
    
    # Demo API usage
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    demo_api_usage(api_url)
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)
    print("\nNEW FEATURES:")
    print("• Search by product names (e.g., 'Acetone', 'Isopropanol')")
    print("• REST API with JSON responses")
    print("• Mixed searches combining CAS and product names")
    print("• URL-only mode for getting links without downloading")
    print("• Batch processing for multiple chemicals")
    print("• Ready for deployment on PythonAnywhere")
    
    print(f"\nTo test the API with different chemicals:")
    print(f"  python test_api.py {api_url}")
    
    print(f"\nTo deploy to PythonAnywhere:")
    print(f"  See deployment_instructions.md for detailed steps")

if __name__ == "__main__":
    main()
