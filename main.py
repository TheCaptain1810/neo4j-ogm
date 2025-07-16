from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
import os
import logging
from database.database import database, db_connection
from services.services import DocumentService, UserService, SessionService, ClassifierService
from data.data import parameters

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    try:
        # Initialize the database connection
        database.install_all_labels()
        logger.info("Neo4j OGM models initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing OGM models: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post("/data")
async def insert_data():
    """Insert all data with complete schema using OGM"""
    try:
        logger.info("Starting complete data insertion")
        
        # Use the DocumentService to create the complete structure
        document = DocumentService.create_complete_document_structure(parameters)
        
        logger.info("Data insertion completed successfully")
        return {"success": True, "message": "Data inserted successfully", "document_id": document.uid}
            
    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error inserting data: {str(e)}")

@app.get("/export/document/{document_id}")
async def export_document(document_id: str):
    """Export document with complete data structure using OGM"""
    try:
        logger.info(f"Exporting document: {document_id}")
        
        response = DocumentService.get_document_with_relations(document_id)
        
        if not response:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        logger.info(f"Successfully exported document: {document_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error exporting document {document_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error exporting document: {str(e)}")

@app.delete("/data/")
async def delete_all_data():
    """Delete all data from the Neo4j database using OGM"""
    try:
        logger.info("Starting data deletion")
        
        DocumentService.delete_all_documents()
        
        logger.info("All data deleted successfully")
        return {"success": True, "message": "All data deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error deleting data: {str(e)}")

def convert_neo4j_datetime(obj):
    """Convert Neo4j datetime objects to ISO strings"""
    from neo4j.time import DateTime as Neo4jDateTime
    if isinstance(obj, dict):
        return {key: convert_neo4j_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_neo4j_datetime(item) for item in obj]
    elif isinstance(obj, Neo4jDateTime):
        return obj.to_native().isoformat() + 'Z' if obj.to_native() else None
    elif hasattr(obj, '__dict__'):
        # Handle Neo4j Node and Relationship objects
        return convert_neo4j_datetime(dict(obj))
    else:
        return obj
