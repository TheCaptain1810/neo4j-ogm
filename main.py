from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
import os
import logging
from database import database, db_connection
from services import DocumentService, UserService, SessionService, ClassifierService
from data.data import parameters

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI()

# Pydantic models
class UserCreate(BaseModel):
    id: str
    email: str
    displayName: str

class FolderCreate(BaseModel):
    id: str
    name: str
    path: str
    driveType: str
    driveId: str
    siteId: str

class ParentReference(BaseModel):
    id: str
    name: str
    path: str
    driveType: str
    driveId: str
    siteId: str


class FileMetadataCreate(BaseModel):
    documentId: str
    mimeType: str
    quickXorHash: str
    sharedScope: str
    createdDateTime: str
    lastModifiedDateTime: str


class VersionCreate(BaseModel):
    documentId: str
    eTag: str
    cTag: str
    timestamp: str
    versionNumber: int


class DocumentCreate(BaseModel):
    id: str
    name: str
    label: str
    size: int
    file_name: Optional[str]
    source: str
    type: str
    createdDateTime: str
    lastModifiedDateTime: str
    webUrl: str
    downloadUrl: str
    driveId: str
    siteId: str
    status: str
    description: Optional[str]
    parentReference: Optional[ParentReference] = Field(None, description="Reference to the parent folder")
    createdBy: str
    lastModifiedBy: str
    file: Optional[FileMetadataCreate] = Field(None, description="File metadata associated with the document")
    version: str

class UserInfo(BaseModel):
    displayName: str
    id: str
    email: str
    
class File(BaseModel):
    mimeType: str
    hashes: Optional[dict] = Field(None, description="File hashes including quickXorHash")

class FileSystemInfo(BaseModel):
    createdDateTime: str
    lastModifiedDateTime: str

class Shared(BaseModel):
    scope: str
class Document(BaseModel):
    name: str
    source: str
    file_name: Optional[str]
    lastModifiedDate: str
    size: int
    id: str
    site_id: str
    drive_id: str
    label: str
    type: str
    microsoft_graph_downloadUrl: str = Field(alias="@microsoft.graph.downloadUrl")
    createdBy: Optional[UserInfo] = Field(None, description="Information about the user who created the item")
    createdDateTime: str
    eTag: Optional[str]
    lastModifiedBy: Optional[UserInfo] = Field(None, description="Information about the user who last modified the item")
    lastModifiedDateTime: str
    parentReference: Optional[ParentReference] = Field(None, description="Reference to the parent folder")
    webUrl: str
    cTag: Optional[str]
    file: Optional[File]
    fileSystemInfo: Optional[FileSystemInfo]
    shared: Optional[Shared]
    status: str


class SessionCreate(BaseModel): 
    sessionId: str
    sessionName: str
    createdAt: str
    createdBy: str
    fileCount: int
    completedAt: Optional[str]
    status: str
    warnings: int
    rowCount: int

class ClassifierCreate(BaseModel):
    id: str
    name: str
    isHierarchy: bool
    parentId: Optional[str]
    prompt: str
    description: str

class ClassifierDataCreate(BaseModel):
    classifierId: str
    code: str
    description: str
    prompt: Optional[str]

class EnricherCreate(BaseModel):
    name: str
    searchTerm: str
    body: str
    active: bool
    value: Optional[str]

class BGSClassificationCreate(BaseModel):
    documentId: str
    code: str 
    explanation: str
    tooltip: str
    appliedAt: str

class UserEditCreate(BaseModel):
    documentId: str
    field: str
    originalValue: str
    editedValue: str
    editedBy: str
    editedAt: str
    reason: Optional[str]

class AIEditExport(BaseModel):
    documentId: str
    field: str
    originalValue: str
    editedValue: str
    editedAt: str

class SessionStandardExport(BaseModel):
    classifiers: List[ClassifierCreate]
    enrichers: List[EnricherCreate]

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
