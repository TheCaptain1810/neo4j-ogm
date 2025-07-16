# Neo4j OGM Project

This project has been converted from using direct Cypher queries to using the `neomodel` Object Graph Mapper for better maintainability and type safety.

## Features

- **Object Graph Mapping**: Using `neomodel` for database operations
- **Type Safety**: Pydantic models with proper type annotations
- **Service Layer**: Clean separation of concerns with service classes
- **FastAPI**: RESTful API with automatic documentation

## Installation

1. Install the dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables in a `.env` file:

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

## Models

The OGM models are defined in `models/models.py`:

- **Document**: Main document entity with relationships to users, folders, metadata, etc.
- **User**: User information (created by, modified by)
- **Folder**: Folder/directory information
- **Session**: Processing session information
- **FileMetadata**: File-specific metadata
- **Version**: Document version information

## Services

The service layer in `services.py` provides business logic for:

- **DocumentService**: Document creation, retrieval, and deletion
- **UserService**: User management operations
- **SessionService**: Session management operations
- **ClassifierService**: Classifier management operations

## API Endpoints

### Insert Sample Data

```
POST /data
```

Creates a complete document structure with all related entities.

### Export Document

```
GET /export/document/{document_id}
```

Retrieves a document with all its related data in a structured format.

### Delete All Data

```
DELETE /data/
```

Removes all data from the Neo4j database.

## Running the Application

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API documentation will be available at `http://localhost:8000/docs`

## Key Benefits of OGM Conversion

1. **Type Safety**: Models are properly typed with Pydantic
2. **Maintainability**: No more raw Cypher queries scattered throughout the code
3. **Relationship Management**: Automatic handling of relationships between entities
4. **Validation**: Built-in data validation through Pydantic models
5. **IDE Support**: Better autocomplete and error detection

## Database Schema

The OGM automatically creates the following node types:

- Document
- User
- Folder
- Session
- FileMetadata
- Version

With relationships:

- Document CREATED_BY User
- Document LAST_MODIFIED_BY User
- Document STORED_IN Folder
- Document HAS_METADATA FileMetadata
- Document HAS_VERSION Version
- Document IN_SESSION Session

## Development Notes

- The `pyneo4j_ogm` package handles connection pooling automatically
- Models are registered and constraints are created on first use
- Relationships are defined using type annotations for better IDE support
