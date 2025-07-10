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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DOCUMENT_NOT_FOUND = "Document not found"
USER_NOT_FOUND = "User not found"
SESSION_NOT_FOUND = "Session not found"
CLASSIFIER_NOT_FOUND = "Classifier not found"
FOLDER_NOT_FOUND = "Folder not found"
BGS_RECORD_NOT_FOUND = "BGS record not found"
ORGANISATION_NOT_FOUND = "Organisation not found"
ENRICHER_NOT_FOUND = "Enricher not found"

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
    documentId: str
    mimeType: str
    quickXorHash: str
    sharedScope: str
    createdDateTime: datetime
    lastModifiedDateTime: datetime

class VersionCreate(BaseModel):
    documentId: str
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
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME") 
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        raise ValueError("Missing Neo4j environment variables. Check your .env file.")
    
    db = Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password)
    
    # Create constraints and indexes
    create_constraints_and_indexes()
    
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
    title="Neo4J - FastAPI",
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

def create_constraints_and_indexes():
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

def convert_neo4j_datetime(obj):
    """Convert Neo4j datetime objects to Python datetime objects"""
    from neo4j.time import DateTime as Neo4jDateTime
    
    if isinstance(obj, dict):
        return {key: convert_neo4j_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_neo4j_datetime(item) for item in obj]
    elif isinstance(obj, Neo4jDateTime):
        return obj.to_native()
    else:
        return obj

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
        db_conn.execute_write_query(query, document.dict())
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
        raise HTTPException(status_code=404, detail=DOCUMENT_NOT_FOUND)
    
    # Convert Neo4j datetime objects to Python datetime objects
    document_data = convert_neo4j_datetime(result[0]['d'])
    return DocumentResponse(**document_data)

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
    # Convert Neo4j datetime objects to Python datetime objects
    converted_result = [convert_neo4j_datetime(record['d']) for record in result]
    return [DocumentResponse(**doc_data) for doc_data in converted_result]

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
        raise HTTPException(status_code=404, detail=DOCUMENT_NOT_FOUND)
    
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
        raise HTTPException(status_code=404, detail=DOCUMENT_NOT_FOUND)
    
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
                "document": DocumentResponse(**convert_neo4j_datetime(record['node'])),
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
        db_conn.execute_write_query(query, user.dict())
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
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND)
    
    user_data = convert_neo4j_datetime(result[0]['u'])
    return UserResponse(**user_data)

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
        db_conn.execute_write_query(query, session.dict())
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
        raise HTTPException(status_code=404, detail=SESSION_NOT_FOUND)
    
    session_data = convert_neo4j_datetime(result[0]['s'])
    return session_data

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
        db_conn.execute_write_query(query, classification.dict())
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
            "classification": convert_neo4j_datetime(record['cl']),
            "classifier": convert_neo4j_datetime(record['c'])
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
        db_conn.execute_write_query(query, bgs_record.dict())
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
        raise HTTPException(status_code=404, detail=BGS_RECORD_NOT_FOUND)
    
    return convert_neo4j_datetime(result[0]['b'])

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
    if result:
        return convert_neo4j_datetime(result[0])
    return {}

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
    if result:
        return convert_neo4j_datetime(result[0])
    return {}

# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
async def health_check(db_conn = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db_conn.execute_query("RETURN 1 as test")
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

# ==========================================
# FOLDER ENDPOINTS
# ==========================================

@app.post("/folders/")
async def create_folder(folder: FolderCreate, db_conn = Depends(get_db)):
    """Create a new folder"""
    query = """
    CREATE (f:Folder {
        id: $id,
        name: $name,
        path: $path,
        driveType: $driveType,
        driveId: $driveId,
        siteId: $siteId
    })
    RETURN f
    """
    
    try:
        db_conn.execute_write_query(query, folder.dict())
        return folder
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating folder: {str(e)}")

@app.get("/folders/{folder_id}")
async def get_folder(folder_id: str, db_conn = Depends(get_db)):
    """Get a folder by ID"""
    query = """
    MATCH (f:Folder {id: $folder_id})
    RETURN f
    """
    
    result = db_conn.execute_query(query, {"folder_id": folder_id})
    if not result:
        raise HTTPException(status_code=404, detail=FOLDER_NOT_FOUND)
    
    return convert_neo4j_datetime(result[0]['f'])

# ==========================================
# FILE METADATA ENDPOINTS
# ==========================================

@app.post("/file-metadata/")
async def create_file_metadata(
    metadata: FileMetadataCreate,
    db_conn = Depends(get_db)
):
    """Create file metadata for a document"""
    query = """
    MATCH (d:Document {id: $documentId})
    CREATE (fm:FileMetadata {
        documentId: $documentId,
        mimeType: $mimeType,
        quickXorHash: $quickXorHash,
        sharedScope: $sharedScope,
        createdDateTime: $createdDateTime,
        lastModifiedDateTime: $lastModifiedDateTime
    })
    CREATE (d)-[:HAS_METADATA]->(fm)
    RETURN fm
    """
    
    try:
        db_conn.execute_write_query(query, metadata.dict())
        return metadata
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating file metadata: {str(e)}")

# ==========================================
# VERSION ENDPOINTS
# ==========================================

@app.post("/versions/")
async def create_version(
    version: VersionCreate,
    db_conn = Depends(get_db)
):
    """Create a version for a document"""
    query = """
    MATCH (d:Document {id: $documentId})
    CREATE (v:Version {
        documentId: $documentId,
        eTag: $eTag,
        cTag: $cTag,
        timestamp: $timestamp,
        versionNumber: $versionNumber
    })
    CREATE (d)-[:HAS_VERSION]->(v)
    RETURN v
    """
    
    try:
        db_conn.execute_write_query(query, version.dict())
        return version
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating version: {str(e)}")

# ==========================================
# CLASSIFIER ENDPOINTS
# ==========================================

@app.post("/classifiers/")
async def create_classifier(classifier: ClassifierCreate, db_conn = Depends(get_db)):
    """Create a new classifier"""
    query = """
    CREATE (c:Classifier {
        id: $id,
        name: $name,
        isHierarchy: $isHierarchy,
        parentId: $parentId,
        prompt: $prompt,
        description: $description
    })
    RETURN c
    """
    
    try:
        db_conn.execute_write_query(query, classifier.dict())
        return classifier
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating classifier: {str(e)}")

@app.get("/classifiers/{classifier_id}")
async def get_classifier(classifier_id: str, db_conn = Depends(get_db)):
    """Get a classifier by ID"""
    query = """
    MATCH (c:Classifier {id: $classifier_id})
    RETURN c
    """
    
    result = db_conn.execute_query(query, {"classifier_id": classifier_id})
    if not result:
        raise HTTPException(status_code=404, detail=CLASSIFIER_NOT_FOUND)
    
    return convert_neo4j_datetime(result[0]['c'])

# ==========================================
# CLASSIFIER DATA ENDPOINTS
# ==========================================

@app.post("/classifier-data/")
async def create_classifier_data(classifier_data: ClassifierDataCreate, db_conn = Depends(get_db)):
    """Create classifier data"""
    query = """
    MATCH (c:Classifier {id: $classifierId})
    CREATE (cd:ClassifierData {
        classifierId: $classifierId,
        code: $code,
        description: $description,
        prompt: $prompt
    })
    CREATE (c)-[:HAS_DATA]->(cd)
    RETURN cd
    """
    
    try:
        db_conn.execute_write_query(query, classifier_data.dict())
        return classifier_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating classifier data: {str(e)}")

# ==========================================
# BGS CLASSIFICATION ENDPOINTS
# ==========================================

@app.post("/bgs/classifications/")
async def create_bgs_classification(bgs_classification: BGSClassificationCreate, db_conn = Depends(get_db)):
    """Create a BGS classification for a document"""
    query = """
    MATCH (d:Document {id: $documentId})
    CREATE (bc:BGSClassification {
        documentId: $documentId,
        code: $code,
        explanation: $explanation,
        tooltip: $tooltip,
        appliedAt: $appliedAt
    })
    CREATE (d)-[:HAS_BGS_CLASSIFICATION]->(bc)
    RETURN bc
    """
    
    try:
        db_conn.execute_write_query(query, bgs_classification.dict())
        return bgs_classification
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating BGS classification: {str(e)}")

# ==========================================
# ORGANIZATION ENDPOINTS
# ==========================================

@app.post("/organisations/")
async def create_organisation(organisation: OrganisationCreate, db_conn = Depends(get_db)):
    """Create a new organisation"""
    query = """
    CREATE (o:Organisation {
        name: $name,
        originalName: $originalName,
        purpose: $purpose,
        type: $type
    })
    RETURN o
    """
    
    try:
        db_conn.execute_write_query(query, organisation.dict())
        return organisation
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating organisation: {str(e)}")

@app.get("/organisations/{organisation_name}")
async def get_organisation(organisation_name: str, db_conn = Depends(get_db)):
    """Get an organisation by name"""
    query = """
    MATCH (o:Organisation {name: $organisation_name})
    RETURN o
    """
    
    result = db_conn.execute_query(query, {"organisation_name": organisation_name})
    if not result:
        raise HTTPException(status_code=404, detail=ORGANISATION_NOT_FOUND)
    
    return convert_neo4j_datetime(result[0]['o'])

# ==========================================
# DATE RECORD ENDPOINTS
# ==========================================

@app.post("/date-records/")
async def create_date_record(date_record: DateRecordCreate, db_conn = Depends(get_db)):
    """Create a date record for a document"""
    query = """
    MATCH (d:Document {id: $documentId})
    CREATE (dr:DateRecord {
        date: $date,
        parsedDate: $parsedDate,
        context: $context,
        documentId: $documentId
    })
    CREATE (d)-[:HAS_DATE_RECORD]->(dr)
    RETURN dr
    """
    
    try:
        db_conn.execute_write_query(query, date_record.dict())
        return date_record
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating date record: {str(e)}")

# ==========================================
# ENRICHER ENDPOINTS
# ==========================================

@app.post("/enrichers/")
async def create_enricher(enricher: EnricherCreate, db_conn = Depends(get_db)):
    """Create a new enricher"""
    query = """
    CREATE (e:Enricher {
        name: $name,
        searchTerm: $searchTerm,
        body: $body,
        active: $active
    })
    RETURN e
    """
    
    try:
        db_conn.execute_write_query(query, enricher.dict())
        return enricher
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating enricher: {str(e)}")

@app.get("/enrichers/{enricher_name}")
async def get_enricher(enricher_name: str, db_conn = Depends(get_db)):
    """Get an enricher by name"""
    query = """
    MATCH (e:Enricher {name: $enricher_name})
    RETURN e
    """
    
    result = db_conn.execute_query(query, {"enricher_name": enricher_name})
    if not result:
        raise HTTPException(status_code=404, detail=ENRICHER_NOT_FOUND)
    
    return convert_neo4j_datetime(result[0]['e'])

# ==========================================
# EXTRACTION ENDPOINTS
# ==========================================

@app.post("/extractions/")
async def create_extraction(extraction: ExtractionCreate, db_conn = Depends(get_db)):
    """Create an extraction for a document"""
    query = """
    MATCH (d:Document {id: $documentId})
    MATCH (e:Enricher {name: $enricherName})
    CREATE (ex:Extraction {
        enricherName: $enricherName,
        searchTerm: $searchTerm,
        value: $value,
        documentId: $documentId,
        extractedAt: $extractedAt
    })
    CREATE (d)-[:HAS_EXTRACTION]->(ex)
    CREATE (ex)-[:USED_ENRICHER]->(e)
    RETURN ex
    """
    
    try:
        db_conn.execute_write_query(query, extraction.dict())
        return extraction
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating extraction: {str(e)}")

# ==========================================
# ADDRESS ENDPOINTS
# ==========================================

@app.post("/addresses/")
async def create_address(address: AddressCreate, db_conn = Depends(get_db)):
    """Create an address for a document"""
    query = """
    MATCH (d:Document {id: $documentId})
    CREATE (a:Address {
        fullAddress: $fullAddress,
        components: $components,
        documentId: $documentId,
        addressType: $addressType
    })
    CREATE (d)-[:HAS_ADDRESS]->(a)
    RETURN a
    """
    
    try:
        db_conn.execute_write_query(query, address.dict())
        return address
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating address: {str(e)}")

# ==========================================
# USER EDIT ENDPOINTS
# ==========================================

@app.post("/user-edits/")
async def create_user_edit(user_edit: UserEditCreate, db_conn = Depends(get_db)):
    """Create a user edit record"""
    query = """
    MATCH (d:Document {id: $documentId})
    MATCH (u:User {id: $editedBy})
    CREATE (ue:UserEdit {
        documentId: $documentId,
        field: $field,
        originalValue: $originalValue,
        editedValue: $editedValue,
        editedBy: $editedBy,
        editedAt: $editedAt,
        reason: $reason
    })
    CREATE (d)-[:HAS_USER_EDIT]->(ue)
    CREATE (ue)-[:EDITED_BY]->(u)
    RETURN ue
    """
    
    try:
        db_conn.execute_write_query(query, user_edit.dict())
        return user_edit
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user edit: {str(e)}")

# ==========================================
# ADDITIONAL MISSING ENDPOINTS
# ==========================================

@app.get("/users/")
async def list_users(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_conn = Depends(get_db)
):
    """List all users with pagination"""
    query = """
    MATCH (u:User)
    RETURN u
    ORDER BY u.displayName
    SKIP $offset
    LIMIT $limit
    """
    
    result = db_conn.execute_query(query, {"limit": limit, "offset": offset})
    converted_result = [convert_neo4j_datetime(record['u']) for record in result]
    return [UserResponse(**user_data) for user_data in converted_result]

@app.get("/sessions/")
async def list_sessions(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_conn = Depends(get_db)
):
    """List all sessions with pagination"""
    query = """
    MATCH (s:Session)
    RETURN s
    ORDER BY s.createdAt DESC
    SKIP $offset
    LIMIT $limit
    """
    
    result = db_conn.execute_query(query, {"limit": limit, "offset": offset})
    return [convert_neo4j_datetime(record['s']) for record in result]

@app.get("/classifiers/")
async def list_classifiers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_conn = Depends(get_db)
):
    """List all classifiers with pagination"""
    query = """
    MATCH (c:Classifier)
    RETURN c
    ORDER BY c.name
    SKIP $offset
    LIMIT $limit
    """
    
    result = db_conn.execute_query(query, {"limit": limit, "offset": offset})
    return [convert_neo4j_datetime(record['c']) for record in result]

@app.get("/bgs/records/")
async def list_bgs_records(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_conn = Depends(get_db)
):
    """List all BGS records with pagination"""
    query = """
    MATCH (b:BGSRecord)
    RETURN b
    ORDER BY b.bgsId
    SKIP $offset
    LIMIT $limit
    """
    
    result = db_conn.execute_query(query, {"limit": limit, "offset": offset})
    return [convert_neo4j_datetime(record['b']) for record in result]