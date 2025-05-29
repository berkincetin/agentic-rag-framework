# Document Processing System

The Document Processing System is a comprehensive solution for processing, indexing, and searching documents in the Agentic RAG application. It supports multiple document formats and integrates seamlessly with the existing document search functionality.

## Features

- **Multi-format Support**: PDF, Word (DOC/DOCX), and text files
- **Intelligent Text Splitting**: Uses LangChain's RecursiveCharacterTextSplitter
- **Vector Embeddings**: OpenAI's text-embedding-3-small model
- **Chroma Integration**: Compatible with existing DocumentSearchTool
- **Batch Processing**: Process multiple documents or entire directories
- **Metadata Tracking**: Comprehensive metadata for processed documents
- **Error Handling**: Robust error handling and logging
- **Turkish Support**: Full support for Turkish characters and content

## Directory Structure

```
data/
├── raw/                    # Upload your documents here
├── processed/              # Processed document metadata
├── chroma_stores/          # Vector store collections
│   ├── academic_documents/
│   ├── student_documents/
│   └── general_documents/
└── processing_metadata.json # Processing status tracking
```

## Supported File Formats

| Format | Extension | Loader | Description |
|--------|-----------|--------|-------------|
| PDF | `.pdf` | PyPDFLoader | PDF documents |
| Word | `.docx` | Docx2txtLoader | Microsoft Word (newer format) |
| Word | `.doc` | UnstructuredWordDocumentLoader | Microsoft Word (legacy format) |
| Text | `.txt` | TextLoader | Plain text files with UTF-8 encoding |

## Installation

Install the additional dependencies for document processing:

```bash
pip install langchain-chroma pypdf docx2txt unstructured python-magic
```

## Quick Start

### 1. Basic Usage

```python
from app.document_processing import DocumentProcessor

# Initialize processor
processor = DocumentProcessor(
    data_dir="data",
    embedding_model="text-embedding-3-small",
    chunk_size=1000,
    chunk_overlap=200
)

# Process a single document
result = processor.process_document(
    file_path="data/raw/my_document.pdf",
    collection_name="my_collection"
)

# Process all documents in a directory
result = processor.process_directory(
    directory_path="data/raw",
    collection_name="batch_collection",
    recursive=True
)
```

### 2. Using the CLI Script

```bash
# Process a single file
python scripts/process_documents.py process-file "data/raw/document.pdf" "academic_documents"

# Process a directory
python scripts/process_documents.py process-dir "data/raw" "general_documents" --recursive

# List collections
python scripts/process_documents.py list-collections

# Search documents
python scripts/process_documents.py search "artificial intelligence" "academic_documents" --top-k 5

# Get processing status
python scripts/process_documents.py status

# Get collection information
python scripts/process_documents.py collection-info "academic_documents"
```

### 3. Integration with DocumentSearchTool

The processed documents are automatically compatible with the existing DocumentSearchTool:

```python
from app.tools.document_search import DocumentSearchTool

# Configure to use processed documents
config = {
    "collection_name": "academic_documents",
    "persist_directory": "./data/chroma_stores/academic_documents",
    "embedding_model": "text-embedding-3-small",
    "top_k": 5
}

# Initialize and use the search tool
search_tool = DocumentSearchTool(config)
result = await search_tool.execute("machine learning research")
```

## Configuration

### Document Processing Configuration

Edit `configs/document_processing.yaml` to customize processing settings:

```yaml
default_settings:
  data_dir: "data"
  embedding_model: "text-embedding-3-small"
  chunk_size: 1000
  chunk_overlap: 200

collections:
  academic_documents:
    description: "Academic papers and research documents"
    persist_directory: "./chroma_db/academic"
    chunk_size: 1500
    chunk_overlap: 300
```

### Bot Configuration

Update your bot configuration files to use the processed documents:

```yaml
# configs/academic_bot.yaml
tools:
  - type: DocumentSearchTool
    enabled: true
    config:
      collection_name: "academic_documents"
      persist_directory: "./data/chroma_stores/academic_documents"
      embedding_model: "text-embedding-3-small"
      top_k: 10
```

## Advanced Usage

### Custom Metadata

Add custom metadata to processed documents:

```python
custom_metadata = {
    "department": "Computer Science",
    "academic_year": "2024",
    "language": "Turkish"
}

result = processor.process_document(
    file_path="data/raw/course_material.pdf",
    collection_name="student_documents",
    custom_metadata=custom_metadata
)
```

### Batch Processing with Progress Tracking

```python
# Process large directories with progress tracking
result = processor.process_directory(
    directory_path="data/raw/academic_papers",
    collection_name="research_papers",
    recursive=True
)

print(f"Processed {result['successful_count']} files successfully")
print(f"Failed to process {result['failed_count']} files")

# Check detailed status
status = processor.get_processing_status()
for file_path, metadata in status['files'].items():
    if metadata['status'] == 'error':
        print(f"Error in {file_path}: {metadata['error']}")
```

### Collection Management

```python
# List all collections
collections = processor.list_collections()
print("Available collections:", collections)

# Get detailed collection information
for collection in collections:
    info = processor.get_collection_info(collection)
    print(f"{collection}: {info['document_count']} documents")

# Delete a collection
result = processor.delete_collection("old_collection")
```

## Best Practices

### 1. Document Organization

- Place raw documents in `data/raw/` directory
- Organize by category (academic, student, admin)
- Use descriptive filenames
- Maintain consistent naming conventions

### 2. Collection Strategy

- Use separate collections for different document types
- Academic documents: `academic_documents`
- Student materials: `student_documents`
- Administrative docs: `admin_documents`
- General resources: `general_documents`

### 3. Chunk Size Optimization

- **Academic papers**: 1500 characters (complex content)
- **Student materials**: 800 characters (digestible chunks)
- **Administrative docs**: 1200 characters (structured content)
- **General documents**: 1000 characters (balanced approach)

### 4. Processing Workflow

1. Upload documents to `data/raw/`
2. Process documents using appropriate collection
3. Verify processing status
4. Test search functionality
5. Update bot configurations if needed

## Troubleshooting

### Common Issues

1. **File encoding errors**: Ensure text files use UTF-8 encoding
2. **Large file processing**: Files over 100MB may cause memory issues
3. **Permission errors**: Check file permissions in data directories
4. **Missing dependencies**: Install all required packages

### Error Handling

The system provides comprehensive error handling:

```python
result = processor.process_document(file_path, collection_name)
if not result["success"]:
    print(f"Processing failed: {result['error']}")
    
    # Check processing status for details
    status = processor.get_processing_status(file_path)
    print(f"Status: {status}")
```

### Logging

Enable detailed logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- **Batch processing**: More efficient than processing files individually
- **Chunk size**: Larger chunks = fewer embeddings but less granular search
- **Memory usage**: Large documents may require more memory
- **Processing time**: Depends on document size and OpenAI API response time

## Integration Examples

See `examples/document_processing_example.py` for comprehensive usage examples including:

- Document processing workflow
- Integration with DocumentSearchTool
- Error handling patterns
- Performance optimization techniques

## API Reference

For detailed API documentation, see the docstrings in:
- `app/document_processing/document_processor.py`
- `scripts/process_documents.py`
