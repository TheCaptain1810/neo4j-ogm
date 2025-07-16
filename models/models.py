from neomodel import (
    StructuredNode, StringProperty, IntegerProperty, 
    BooleanProperty, RelationshipTo, RelationshipFrom,
    UniqueIdProperty, DateTimeProperty
)
from typing import Optional


class User(StructuredNode):
    """User node model"""
    uid = StringProperty(unique_index=True, required=True)
    email = StringProperty(required=True)
    displayName = StringProperty(required=True)
    
    # Relationships
    created_documents = RelationshipFrom('Document', 'CREATED_BY')
    modified_documents = RelationshipFrom('Document', 'LAST_MODIFIED_BY')


class Folder(StructuredNode):
    """Folder node model"""
    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    path = StringProperty(required=True)
    driveType = StringProperty(required=True)
    driveId = StringProperty(required=True)
    siteId = StringProperty(required=True)
    
    # Relationships
    documents = RelationshipFrom('Document', 'STORED_IN')


class Session(StructuredNode):
    """Session node model"""
    sessionId = StringProperty(unique_index=True, required=True)
    sessionName = StringProperty(required=True)
    createdAt = StringProperty(required=True)
    createdBy = StringProperty(required=True)
    fileCount = IntegerProperty(required=True)
    completedAt = StringProperty()
    status = StringProperty(required=True)
    warnings = IntegerProperty(required=True)
    rowCount = IntegerProperty(required=True)
    
    # Relationships
    documents = RelationshipFrom('Document', 'IN_SESSION')


class FileMetadata(StructuredNode):
    """FileMetadata node model"""
    documentId = StringProperty(unique_index=True, required=True)
    mimeType = StringProperty(required=True)
    quickXorHash = StringProperty(required=True)
    sharedScope = StringProperty(required=True)
    createdDateTime = StringProperty(required=True)
    lastModifiedDateTime = StringProperty(required=True)
    
    # Relationships
    document = RelationshipFrom('Document', 'HAS_METADATA')


class Version(StructuredNode):
    """Version node model"""
    documentId = StringProperty(unique_index=True, required=True)
    eTag = StringProperty(required=True)
    cTag = StringProperty(required=True)
    timestamp = StringProperty(required=True)
    versionNumber = IntegerProperty(required=True)
    
    # Relationships
    document = RelationshipFrom('Document', 'HAS_VERSION')


class Document(StructuredNode):
    """Document node model"""
    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    label = StringProperty(required=True)
    size = IntegerProperty(required=True)
    file_name = StringProperty()
    source = StringProperty(required=True)
    type = StringProperty(required=True)
    createdDateTime = StringProperty(required=True)
    lastModifiedDateTime = StringProperty(required=True)
    webUrl = StringProperty(required=True)
    downloadUrl = StringProperty(required=True)
    driveId = StringProperty(required=True)
    siteId = StringProperty(required=True)
    status = StringProperty(required=True)
    description = StringProperty()
    version = StringProperty(required=True)
    
    # Relationships
    created_by = RelationshipTo(User, 'CREATED_BY')
    last_modified_by = RelationshipTo(User, 'LAST_MODIFIED_BY')
    stored_in = RelationshipTo(Folder, 'STORED_IN')
    metadata = RelationshipTo(FileMetadata, 'HAS_METADATA')
    version_info = RelationshipTo(Version, 'HAS_VERSION')
    session = RelationshipTo(Session, 'IN_SESSION')


class Classifier(StructuredNode):
    """Classifier node model"""
    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    isHierarchy = BooleanProperty(required=True)
    parentId = StringProperty()
    prompt = StringProperty(required=True)
    description = StringProperty(required=True)


class ClassifierData(StructuredNode):
    """ClassifierData node model"""
    classifierId = StringProperty(unique_index=True, required=True)
    code = StringProperty(required=True)
    description = StringProperty(required=True)
    prompt = StringProperty()


class Enricher(StructuredNode):
    """Enricher node model"""
    name = StringProperty(unique_index=True, required=True)
    searchTerm = StringProperty(required=True)
    body = StringProperty(required=True)
    active = BooleanProperty(required=True)
    value = StringProperty()


class BGSClassification(StructuredNode):
    """BGS Classification node model"""
    documentId = StringProperty(unique_index=True, required=True)
    code = StringProperty(required=True)
    explanation = StringProperty(required=True)
    tooltip = StringProperty(required=True)
    appliedAt = StringProperty(required=True)


class UserEdit(StructuredNode):
    """User Edit node model"""
    documentId = StringProperty(unique_index=True, required=True)
    field = StringProperty(required=True)
    originalValue = StringProperty(required=True)
    editedValue = StringProperty(required=True)
    editedBy = StringProperty(required=True)
    editedAt = StringProperty(required=True)
    reason = StringProperty()
