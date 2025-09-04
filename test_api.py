#!/usr/bin/env python3
"""
Test script for the SDS Finder API
Run this script to test the API endpoints locally or on deployment
"""

import requests
import json
import sys

def test_api(base_url="http://localhost:5000"):
    """Test the SDS Finder API endpoints"""
    
    print(f"Testing API at: {base_url}")
    print("=" * 50)
    
    # Test 1: API Documentation
    print("\n1. Testing API documentation endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✓ API documentation endpoint working")
            data = response.json()
            print(f"  API Version: {data.get('version', 'Unknown')}")
        else:
            print(f"✗ API documentation failed: {response.status_code}")
    except Exception as e:
        print(f"✗ API documentation error: {e}")
    
    # Test 2: Search by CAS Number
    print("\n2. Testing CAS number search...")
    cas_data = {
        "cas_numbers": ["67-63-0", "75-09-2"],  # Isopropanol and Dichloromethane
        "download": False
    }
    
    try:
        response = requests.post(f"{base_url}/search/cas", 
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(cas_data))
        if response.status_code == 200:
            print("✓ CAS search endpoint working")
            data = response.json()
            print(f"  Found {data.get('found_count', 0)} out of {data.get('total_searched', 0)} SDS")
            for result in data.get('results', []):
                status = "Found" if result['found'] else "Not found"
                source = f" (Source: {result.get('source', 'Unknown')})" if result['found'] else ""
                print(f"    {result['cas_number']}: {status}{source}")
        else:
            print(f"✗ CAS search failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ CAS search error: {e}")
    
    # Test 3: Search by Product Name
    print("\n3. Testing product name search...")
    product_data = {
        "product_names": ["Isopropanol", "Acetone"],
        "download": False
    }
    
    try:
        response = requests.post(f"{base_url}/search/product",
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(product_data))
        if response.status_code == 200:
            print("✓ Product name search endpoint working")
            data = response.json()
            print(f"  Found {data.get('found_count', 0)} out of {data.get('total_searched', 0)} SDS")
            for result in data.get('results', []):
                status = "Found" if result['found'] else "Not found"
                source = f" (Source: {result.get('source', 'Unknown')})" if result['found'] else ""
                print(f"    {result['product_name']}: {status}{source}")
        else:
            print(f"✗ Product name search failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Product name search error: {e}")
    
    # Test 4: Mixed Search
    print("\n4. Testing mixed search...")
    mixed_data = {
        "cas_numbers": ["67-63-0"],
        "product_names": ["Acetone"],
        "download": False
    }
    
    try:
        response = requests.post(f"{base_url}/search/mixed",
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(mixed_data))
        if response.status_code == 200:
            print("✓ Mixed search endpoint working")
            data = response.json()
            print(f"  Found {data.get('found_count', 0)} out of {data.get('total_searched', 0)} SDS")
            for result in data.get('results', []):
                status = "Found" if result['found'] else "Not found"
                source = f" (Source: {result.get('source', 'Unknown')})" if result['found'] else ""
                identifier = result.get('identifier', 'Unknown')
                search_type = result.get('type', 'Unknown')
                print(f"    {identifier} ({search_type}): {status}{source}")
        else:
            print(f"✗ Mixed search failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Mixed search error: {e}")
    
    # Test 5: Error handling
    print("\n5. Testing error handling...")
    try:
        response = requests.post(f"{base_url}/search/cas",
                               headers={"Content-Type": "application/json"},
                               data=json.dumps({}))  # Empty request
        if response.status_code == 400:
            print("✓ Error handling working (empty request properly rejected)")
        else:
            print(f"✗ Error handling not working: expected 400, got {response.status_code}")
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
    
    print("\n" + "=" * 50)
    print("API testing complete!")

if __name__ == "__main__":
    # Allow custom base URL as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    test_api(base_url)
