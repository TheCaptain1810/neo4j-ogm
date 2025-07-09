#!/usr/bin/env python3
"""
Simple test script to verify the API endpoints are working
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:6969'

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f'{BASE_URL}/health')
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_create_user():
    """Test creating a user"""
    user_data = {
        "id": "354a020c-cf84-4e30-afd3-07ba0b07c4fc",
        "email": "tom@hoppa.ai",
        "displayName": "Tom Goldsmith"
    }
    
    try:
        response = requests.post(f'{BASE_URL}/users/', json=user_data)
        print(f"Create User: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Create user failed: {e}")
        return False

def test_create_document():
    """Test creating a document"""
    document_data = {
        "id": "01FCBACZIFWRL22JSIMJAYZJ5UAYIDY36K",
        "name": "BGS borehole 426100 (SU72SW51).pdf",
        "label": "BGS borehole 426100 (SU72SW51).pdf",
        "size": 3040,
        "file_name": "BGS borehole 426100 (SU72SW51).pdf",
        "source": "sharepoint",
        "type": "application/pdf",
        "createdDateTime": "2024-12-17T10:31:25Z",
        "lastModifiedDateTime": "2024-12-17T10:31:25Z",
        "webUrl": "https://hoppa.sharepoint.com/sites/EngineeringDesign/test.pdf",
        "downloadUrl": "https://hoppa.sharepoint.com/sites/EngineeringDesign/download.pdf",
        "driveId": "01FCBACZFWRL22JSIMJAYZJ5UAYIDY36K",
        "siteId": "hoppa.sharepoint.com,5d2c3e4f-8a9b-4c5d-9e8f-1a2b3c4d5e6f",
        "status": "N/A",
        "description": "BGS borehole record for location 426100"
    }
    
    try:
        response = requests.post(f'{BASE_URL}/documents/', json=document_data)
        print(f"Create Document: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Create document failed: {e}")
        return False

def test_get_documents():
    """Test getting documents list"""
    try:
        response = requests.get(f'{BASE_URL}/documents/')
        print(f"Get Documents: {response.status_code}")
        if response.status_code == 200:
            docs = response.json()
            print(f"Found {len(docs)} documents")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Get documents failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("Starting API tests...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Create User", test_create_user),
        ("Create Document", test_create_document),
        ("Get Documents", test_get_documents),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"{test_name}: ERROR - {e}")
            results.append((test_name, False))
        print("-" * 30)
    
    print("\nTest Results Summary:")
    print("=" * 50)
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    run_tests()
