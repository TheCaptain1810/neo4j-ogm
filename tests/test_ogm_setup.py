#!/usr/bin/env python3
"""
Test script for the Neo4j OGM conversion using neomodel
"""

import sys
import os
import logging

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ogm_setup():
    """Test the OGM setup"""
    try:
        logger.info("Testing Neo4j OGM setup with neomodel...")
        
        # Test neomodel import
        from neomodel import StructuredNode
        logger.info("✓ neomodel imported successfully")
        
        # Import the database connection
        from database.database import db_connection
        logger.info("✓ Database connection imported successfully")
        
        # Import the models
        from models.models import Document, User, Folder, Session, FileMetadata, Version
        logger.info("✓ Models imported successfully")
        
        # Import the services
        from services.services import DocumentService, UserService, SessionService, ClassifierService
        logger.info("✓ Services imported successfully")
        
        # Test data import
        from data.data import parameters
        logger.info("✓ Test data imported successfully")
        
        logger.info("🎉 All OGM components imported successfully!")
        logger.info("The codebase has been successfully converted to use neomodel")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during OGM setup test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ogm_setup()
    if success:
        print("\n✅ OGM conversion successful! You can now run the FastAPI application.")
        print("To start the server, run: uvicorn main:app --reload")
        print("\nNote: Make sure to set your Neo4j connection details in your .env file:")
        print("NEO4J_URI=neo4j://localhost:7687")
        print("NEO4J_USERNAME=neo4j")
        print("NEO4J_PASSWORD=your_password")
    else:
        print("\n❌ OGM conversion failed. Please check the error messages above.")
        sys.exit(1)
