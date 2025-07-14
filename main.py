from fastapi import FastAPI, Depends, HTTPException
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
import os
import logging
from data.data import insert_query, parameters

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI()

class Neo4jConnection:
    def __init__(self):
        try:
            self.driver = AsyncGraphDatabase.driver(
                os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
                auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
            )
            logger.info("Neo4j connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {str(e)}")
            raise

    async def close(self):
        await self.driver.close()
        logger.info("Neo4j connection closed")

    async def query(self, query, parameters=None):
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters or {})
                data = [dict(record) for record in await result.data()]
                logger.debug(f"Query executed: {query[:50]}... with params: {parameters}")
                return data
        except Exception as e:
            logger.error(f"Query failed: {query[:50]}... Error: {str(e)}")
            raise

async def get_db():
    db = Neo4jConnection()
    try:
        yield db
    finally:
        await db.close()

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
    db = Neo4jConnection()
    try:
        await db.query("""
        CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE
        """)
        await db.query("""
        CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE
        """)
        await db.query("""
        CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.sessionId IS UNIQUE
        """)
        await db.query("""
        CREATE CONSTRAINT classifier_id_unique IF NOT EXISTS FOR (c:Classifier) REQUIRE c.id IS UNIQUE
        """)
        await db.query("""
        CREATE CONSTRAINT folder_id_unique IF NOT EXISTS FOR (f:Folder) REQUIRE f.id IS UNIQUE
        """)
        await db.query("""
        CREATE INDEX document_name_index IF NOT EXISTS FOR (d:Document) ON (d.name)
        """)
        await db.query("""
        CREATE INDEX document_created_index IF NOT EXISTS FOR (d:Document) ON (d.createdDateTime)
        """)
        logger.info("Constraints and indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating constraints/indexes: {str(e)}")
        raise
    finally:
        await db.close()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post("/data")
async def insert_data(db: Neo4jConnection = Depends(get_db)):
    """Insert all data with complete schema similar to PostgreSQL version"""
    try:
        logger.info("Starting complete data insertion")
        
        # Execute the query
        result = await db.query(insert_query, parameters)
        
        if result and result[0].get("result") == "SUCCESS":
            logger.info("data insertion completed successfully")
            return {"success": True, "message": "data inserted successfully"}
        else:
            logger.error("data insertion failed: No success result returned")
            raise HTTPException(status_code=400, detail="data insertion failed")
            
    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error inserting data: {str(e)}")

@app.get("/export/document/{document_id}")
async def export_document(document_id: str, db: Neo4jConnection = Depends(get_db)):
    """Export document with complete data structure like PostgreSQL version"""
    try:
        logger.info(f"Exporting document: {document_id}")
        
        # Comprehensive query to get all document data
        export_query = """
        MATCH (d:Document {id: $document_id})
        OPTIONAL MATCH (d)-[:CREATED_BY]->(createdBy:User)
        OPTIONAL MATCH (d)-[:LAST_MODIFIED_BY]->(lastModifiedBy:User)
        OPTIONAL MATCH (d)-[:STORED_IN]->(f:Folder)
        OPTIONAL MATCH (d)-[:HAS_METADATA]->(fm:FileMetadata)
        OPTIONAL MATCH (d)-[:HAS_VERSION]->(v:Version)
        RETURN 
            d.name as name,
            d.source as source,
            d.file_name as file_name,
            d.lastModifiedDateTime as lastModifiedDate,
            d.size as size,
            d.id as id,
            d.siteId as site_id,
            d.driveId as drive_id,
            d.label as label,
            d.type as type,
            d.downloadUrl as download_url,
            d.createdDateTime as created_date_time,
            d.lastModifiedDateTime as last_modified_date_time,
            d.webUrl as web_url,
            d.status as status,
            createdBy.id as createdBy_id,
            createdBy.email as createdBy_email,
            createdBy.displayName as createdBy_displayName,
            lastModifiedBy.id as lastModifiedBy_id,
            lastModifiedBy.email as lastModifiedBy_email,
            lastModifiedBy.displayName as lastModifiedBy_displayName,
            f.id as parentReference_id,
            f.name as parentReference_name,
            f.path as parentReference_path,
            f.driveType as parentReference_driveType,
            f.driveId as parentReference_driveId,
            f.siteId as parentReference_siteId,
            fm.mimeType as file_mimeType,
            fm.quickXorHash as file_hashes_quickXorHash,
            fm.createdDateTime as fileSystemInfo_createdDateTime,
            fm.lastModifiedDateTime as fileSystemInfo_lastModifiedDateTime,
            fm.sharedScope as shared_scope,
            v.eTag as eTag,
            v.cTag as cTag
        """
        
        result = await db.query(export_query, {"document_id": document_id})
        
        if not result:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        document = result[0]
        
        # Convert Neo4j datetime objects if needed
        document = convert_neo4j_datetime(document)
        
        # Build response structure matching PostgreSQL format
        response = {
            "name": document["name"],
            "source": document["source"],
            "file_name": document["file_name"],
            "lastModifiedDate": document["lastModifiedDate"],
            "size": document["size"],
            "id": document["id"],
            "site_id": document["site_id"],
            "drive_id": document["drive_id"],
            "label": document["label"],
            "type": document["type"],
            "@microsoft.graph.downloadUrl": document["download_url"],
            "createdBy": {
                "id": document["createdBy_id"],
                "email": document["createdBy_email"],
                "displayName": document["createdBy_displayName"]
            } if document["createdBy_id"] else None,
            "createdDateTime": document["created_date_time"],
            "lastModifiedBy": {
                "id": document["lastModifiedBy_id"],
                "email": document["lastModifiedBy_email"],
                "displayName": document["lastModifiedBy_displayName"]
            } if document["lastModifiedBy_id"] else None,
            "lastModifiedDateTime": document["last_modified_date_time"],
            "parentReference": {
                "id": document["parentReference_id"],
                "name": document["parentReference_name"],
                "path": document["parentReference_path"],
                "driveType": document["parentReference_driveType"],
                "driveId": document["parentReference_driveId"],
                "siteId": document["parentReference_siteId"]
            } if document["parentReference_id"] else None,
            "webUrl": document["web_url"],
            "cTag": document["cTag"],
            "eTag": document["eTag"],
            "file": {
                "hashes": {"quickXorHash": document["file_hashes_quickXorHash"]},
                "mimeType": document["file_mimeType"]
            } if document["file_mimeType"] else None,
            "fileSystemInfo": {
                "createdDateTime": document["fileSystemInfo_createdDateTime"],
                "lastModifiedDateTime": document["fileSystemInfo_lastModifiedDateTime"]
            } if document["fileSystemInfo_createdDateTime"] else None,
            "shared": {
                "scope": document["shared_scope"]
            } if document["shared_scope"] else None,
            "status": document["status"]
        }
        
        logger.info(f"Successfully exported document: {document_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error exporting document {document_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error exporting document: {str(e)}")

@app.delete("/data/")
async def delete_all_data(db: Neo4jConnection = Depends(get_db)):
    """Delete all data from the Neo4j database"""
    try:
        logger.info("Starting data deletion")
        
        # Delete all nodes and relationships
        delete_query = """
        MATCH (n)
        DETACH DELETE n
        """
        
        await db.query(delete_query)
        
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
