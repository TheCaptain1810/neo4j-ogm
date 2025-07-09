from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from neo4j import GraphDatabase
import os
from contextlib import asynccontextmanager
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# PYDANTIC MODELS
# ==========================================

class DocumentCreate(BaseModel):
    id: str
    name: str
    label: str
    size: int
    file_name: Optional[str] = None
    source: str
    type: str
    createdDateTime: datetime
    lastModifiedDateTime: datetime
    webUrl: str
    downloadUrl: str
    driveId: str
    siteId: str
    status: str = "N/A"
    description: Optional[str] = None

class DocumentResponse(DocumentCreate):
    pass

class FileMetadataCreate(BaseModel):
    mimeType: str
    quickXorHash: str
    sharedScope: str
    createdDateTime: datetime
    lastModifiedDateTime: datetime

class VersionCreate(BaseModel):
    eTag: str
    cTag: str
    timestamp: datetime
    versionNumber: int

class UserCreate(BaseModel):
    id: str
    email: str
    displayName: str

class UserResponse(UserCreate):
    pass

class FolderCreate(BaseModel):
    id: str
    name: str
    path: str
    driveType: str
    driveId: str
    siteId: str

class SessionCreate(BaseModel):
    sessionId: str
    sessionName: str
    createdAt: datetime
    createdBy: str
    fileCount: int
    completedAt: Optional[datetime] = None
    status: str = "draft"
    warnings: int = 0
    rowCount: int = 0

class ClassifierCreate(BaseModel):
    id: str
    name: str
    isHierarchy: bool
    parentId: Optional[str] = None
    prompt: str
    description: str

class ClassifierDataCreate(BaseModel):
    classifierId: str
    code: str
    description: str
    prompt: Optional[str] = None

class ClassificationCreate(BaseModel):
    documentId: str
    classifierId: str
    code: str
    codeDescription: str
    certainty: str
    explanation: str
    appliedAt: datetime

class BGSClassificationCreate(BaseModel):
    documentId: str
    code: str
    explanation: str
    tooltip: str
    appliedAt: datetime

class BGSRecordCreate(BaseModel):
    bgsId: str
    bgsReference: str
    gridReferenceNorthings: int
    gridReferenceEastings: int
    quarterSheet: str
    registrationNumber: str

class OrganisationCreate(BaseModel):
    name: str
    originalName: str
    purpose: str
    type: str

class DateRecordCreate(BaseModel):
    date: str
    parsedDate: Optional[datetime] = None
    context: str
    documentId: str

class EnricherCreate(BaseModel):
    name: str
    searchTerm: str
    body: str
    active: bool = True

class ExtractionCreate(BaseModel):
    enricherName: str
    searchTerm: str
    value: str
    documentId: str
    extractedAt: datetime

class AddressCreate(BaseModel):
    fullAddress: str
    components: List[str]
    documentId: str
    addressType: str

class UserEditCreate(BaseModel):
    documentId: str
    field: str
    originalValue: str
    editedValue: str
    editedBy: str
    editedAt: datetime
    reason: Optional[str] = None

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    offset: int = 0

class CertaintyLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class StatusType(str, Enum):
    DRAFT = "draft"
    COMPLETED = "completed"
    PROCESSING = "processing"

# ==========================================
# NEO4J DATABASE CONNECTION
# ==========================================

class Neo4jConnection:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def execute_query(self, query: str, parameters: dict = None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
    
    def execute_write_query(self, query: str, parameters: dict = None):
        with self.driver.session() as session:
            result = session.write_transaction(lambda tx: tx.run(query, parameters))
            return result

# Database instance
db = None

# ==========================================
# LIFECYCLE MANAGEMENT
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    db = Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password)
    
    # Create constraints and indexes
    await create_constraints_and_indexes()
    
    logger.info("Connected to Neo4j database")
    yield
    
    # Shutdown
    if db:
        db.close()
    logger.info("Disconnected from Neo4j database")

# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Document Management System API",
    description="Neo4j-based document management system with FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# DATABASE SETUP FUNCTIONS
# ==========================================

async def create_constraints_and_indexes():
    """Create all constraints and indexes defined in the schema"""
    constraints_and_indexes = [
        # Unique constraints
        "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.sessionId IS UNIQUE",
        "CREATE CONSTRAINT classifier_id_unique IF NOT EXISTS FOR (c:Classifier) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT folder_id_unique IF NOT EXISTS FOR (f:Folder) REQUIRE f.id IS UNIQUE",
        
        # Performance indexes
        "CREATE INDEX document_name_index IF NOT EXISTS FOR (d:Document) ON (d.name)",
        "CREATE INDEX document_created_index IF NOT EXISTS FOR (d:Document) ON (d.createdDateTime)",
        "CREATE INDEX bgs_id_index IF NOT EXISTS FOR (b:BGSRecord) ON (b.bgsId)",
        "CREATE INDEX bgs_reference_index IF NOT EXISTS FOR (b:BGSRecord) ON (b.bgsReference)",
        "CREATE INDEX classification_code_index IF NOT EXISTS FOR (c:Classification) ON (c.code)",
        "CREATE INDEX organisation_name_index IF NOT EXISTS FOR (o:Organisation) ON (o.name)",
        "CREATE INDEX extraction_value_index IF NOT EXISTS FOR (e:Extraction) ON (e.value)",
        
        # Full-text search indexes
        "CREATE FULLTEXT INDEX document_search IF NOT EXISTS FOR (d:Document) ON EACH [d.name, d.description]",
        "CREATE FULLTEXT INDEX organisation_search IF NOT EXISTS FOR (o:Organisation) ON EACH [o.name, o.purpose]",
        "CREATE FULLTEXT INDEX address_search IF NOT EXISTS FOR (a:Address) ON EACH [a.fullAddress]"
    ]
    
    for query in constraints_and_indexes:
        try:
            db.execute_query(query)
        except Exception as e:
            logger.warning(f"Failed to create constraint/index: {e}")

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_db():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    return db


# ROOT ENDPOINT
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Hello, World!"}


# ==========================================
# DOCUMENT ENDPOINTS
# ==========================================

@app.post("/documents/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate, db_conn = Depends(get_db)):
    """Create a new document in the database"""
    query = """
    CREATE (d:Document {
        id: $id,
        name: $name,
        label: $label,
        size: $size,
        file_name: $file_name,
        source: $source,
        type: $type,
        createdDateTime: $createdDateTime,
        lastModifiedDateTime: $lastModifiedDateTime,
        webUrl: $webUrl,
        downloadUrl: $downloadUrl,
        driveId: $driveId,
        siteId: $siteId,
        status: $status,
        description: $description
    })
    RETURN d
    """
    
    try:
        result = db_conn.execute_write_query(query, document.dict())
        return document
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating document: {str(e)}")

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db_conn = Depends(get_db)):
    """Get a document by ID"""
    query = """
    MATCH (d:Document {id: $document_id})
    RETURN d
    """
    
    result = db_conn.execute_query(query, {"document_id": document_id})
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(**result[0]['d'])

@app.get("/documents/", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_conn = Depends(get_db)
):
    """List all documents with pagination"""
    query = """
    MATCH (d:Document)
    RETURN d
    ORDER BY d.createdDateTime DESC
    SKIP $offset
    LIMIT $limit
    """
    
    result = db_conn.execute_query(query, {"limit": limit, "offset": offset})
    return [DocumentResponse(**record['d']) for record in result]

@app.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document: DocumentCreate,
    db_conn = Depends(get_db)
):
    """Update a document"""
    query = """
    MATCH (d:Document {id: $document_id})
    SET d += $properties
    RETURN d
    """
    
    properties = document.dict()
    properties.pop('id', None)  # Don't update ID
    
    result = db_conn.execute_write_query(query, {
        "document_id": document_id,
        "properties": properties
    })
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, db_conn = Depends(get_db)):
    """Delete a document and all its relationships"""
    query = """
    MATCH (d:Document {id: $document_id})
    DETACH DELETE d
    RETURN count(d) as deleted_count
    """
    
    result = db_conn.execute_write_query(query, {"document_id": document_id})
    
    if not result or result[0]['deleted_count'] == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}

# ==========================================
# SEARCH ENDPOINTS
# ==========================================

@app.post("/search/documents")
async def search_documents(search_query: SearchQuery, db_conn = Depends(get_db)):
    """Full-text search for documents"""
    query = """
    CALL db.index.fulltext.queryNodes('document_search', $query)
    YIELD node, score
    RETURN node, score
    ORDER BY score DESC
    SKIP $offset
    LIMIT $limit
    """
    
    try:
        result = db_conn.execute_query(query, search_query.dict())
        return [
            {
                "document": DocumentResponse(**record['node']),
                "score": record['score']
            }
            for record in result
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search error: {str(e)}")

# ==========================================
# USER ENDPOINTS
# ==========================================

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db_conn = Depends(get_db)):
    """Create a new user"""
    query = """
    CREATE (u:User {
        id: $id,
        email: $email,
        displayName: $displayName
    })
    RETURN u
    """
    
    try:
        result = db_conn.execute_write_query(query, user.dict())
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db_conn = Depends(get_db)):
    """Get a user by ID"""
    query = """
    MATCH (u:User {id: $user_id})
    RETURN u
    """
    
    result = db_conn.execute_query(query, {"user_id": user_id})
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**result[0]['u'])

# ==========================================
# SESSION ENDPOINTS
# ==========================================

@app.post("/sessions/")
async def create_session(session: SessionCreate, db_conn = Depends(get_db)):
    """Create a new processing session"""
    query = """
    CREATE (s:Session {
        sessionId: $sessionId,
        sessionName: $sessionName,
        createdAt: $createdAt,
        createdBy: $createdBy,
        fileCount: $fileCount,
        completedAt: $completedAt,
        status: $status,
        warnings: $warnings,
        rowCount: $rowCount
    })
    RETURN s
    """
    
    try:
        result = db_conn.execute_write_query(query, session.dict())
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating session: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str, db_conn = Depends(get_db)):
    """Get a session by ID"""
    query = """
    MATCH (s:Session {sessionId: $session_id})
    RETURN s
    """
    
    result = db_conn.execute_query(query, {"session_id": session_id})
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return result[0]['s']

# ==========================================
# CLASSIFICATION ENDPOINTS
# ==========================================

@app.post("/classifications/")
async def create_classification(classification: ClassificationCreate, db_conn = Depends(get_db)):
    """Create a new classification for a document"""
    query = """
    MATCH (d:Document {id: $documentId})
    MATCH (c:Classifier {id: $classifierId})
    CREATE (cl:Classification {
        documentId: $documentId,
        classifierId: $classifierId,
        code: $code,
        codeDescription: $codeDescription,
        certainty: $certainty,
        explanation: $explanation,
        appliedAt: $appliedAt
    })
    CREATE (d)-[:HAS_CLASSIFICATION]->(cl)
    CREATE (cl)-[:USES_CLASSIFIER]->(c)
    RETURN cl
    """
    
    try:
        result = db_conn.execute_write_query(query, classification.dict())
        return classification
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating classification: {str(e)}")

@app.get("/documents/{document_id}/classifications")
async def get_document_classifications(document_id: str, db_conn = Depends(get_db)):
    """Get all classifications for a document"""
    query = """
    MATCH (d:Document {id: $document_id})-[:HAS_CLASSIFICATION]->(cl:Classification)
    MATCH (cl)-[:USES_CLASSIFIER]->(c:Classifier)
    RETURN cl, c
    """
    
    result = db_conn.execute_query(query, {"document_id": document_id})
    return [
        {
            "classification": record['cl'],
            "classifier": record['c']
        }
        for record in result
    ]

# ==========================================
# BGS ENDPOINTS
# ==========================================

@app.post("/bgs/records/")
async def create_bgs_record(bgs_record: BGSRecordCreate, db_conn = Depends(get_db)):
    """Create a BGS record"""
    query = """
    CREATE (b:BGSRecord {
        bgsId: $bgsId,
        bgsReference: $bgsReference,
        gridReferenceNorthings: $gridReferenceNorthings,
        gridReferenceEastings: $gridReferenceEastings,
        quarterSheet: $quarterSheet,
        registrationNumber: $registrationNumber
    })
    RETURN b
    """
    
    try:
        result = db_conn.execute_write_query(query, bgs_record.dict())
        return bgs_record
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating BGS record: {str(e)}")

@app.get("/bgs/records/{bgs_id}")
async def get_bgs_record(bgs_id: str, db_conn = Depends(get_db)):
    """Get a BGS record by ID"""
    query = """
    MATCH (b:BGSRecord {bgsId: $bgs_id})
    RETURN b
    """
    
    result = db_conn.execute_query(query, {"bgs_id": bgs_id})
    if not result:
        raise HTTPException(status_code=404, detail="BGS record not found")
    
    return result[0]['b']

# ==========================================
# MIGRATION ENDPOINTS
# ==========================================

@app.post("/migrate/bulk-documents")
async def bulk_migrate_documents(documents: List[DocumentCreate], db_conn = Depends(get_db)):
    """Bulk migrate documents to Neo4j"""
    query = """
    UNWIND $documents as doc
    CREATE (d:Document {
        id: doc.id,
        name: doc.name,
        label: doc.label,
        size: doc.size,
        file_name: doc.file_name,
        source: doc.source,
        type: doc.type,
        createdDateTime: doc.createdDateTime,
        lastModifiedDateTime: doc.lastModifiedDateTime,
        webUrl: doc.webUrl,
        downloadUrl: doc.downloadUrl,
        driveId: doc.driveId,
        siteId: doc.siteId,
        status: doc.status,
        description: doc.description
    })
    RETURN count(d) as created_count
    """
    
    try:
        documents_data = [doc.dict() for doc in documents]
        result = db_conn.execute_write_query(query, {"documents": documents_data})
        return {
            "message": f"Successfully migrated {result[0]['created_count']} documents",
            "count": result[0]['created_count']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error migrating documents: {str(e)}")

@app.post("/migrate/link-document-relationships")
async def link_document_relationships(db_conn = Depends(get_db)):
    """Create relationships between documents and other entities"""
    # This is a placeholder for relationship creation logic
    # You would implement specific relationship creation based on your data
    return {"message": "Relationship linking completed"}

# ==========================================
# ANALYTICS ENDPOINTS
# ==========================================

@app.get("/analytics/document-stats")
async def get_document_stats(db_conn = Depends(get_db)):
    """Get document statistics"""
    query = """
    MATCH (d:Document)
    RETURN 
        count(d) as total_documents,
        count(DISTINCT d.source) as unique_sources,
        count(DISTINCT d.type) as unique_types,
        min(d.createdDateTime) as earliest_document,
        max(d.createdDateTime) as latest_document
    """
    
    result = db_conn.execute_query(query)
    return result[0] if result else {}

@app.get("/analytics/classification-stats")
async def get_classification_stats(db_conn = Depends(get_db)):
    """Get classification statistics"""
    query = """
    MATCH (cl:Classification)
    RETURN 
        count(cl) as total_classifications,
        collect(DISTINCT cl.classifierId) as classifier_ids,
        collect(DISTINCT cl.certainty) as certainty_levels
    """
    
    result = db_conn.execute_query(query)
    return result[0] if result else {}

# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
async def health_check(db_conn = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        result = db_conn.execute_query("RETURN 1 as test")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)