# Data Directory

This directory contains all document processing related files and data for the Agentic RAG system.

## Directory Structure

```
data/
├── raw/                    # Place your documents here for processing
│   ├── academic/          # Academic papers and research documents
│   ├── student/           # Course materials and student resources
│   ├── admin/             # Administrative documents and policies
│   └── general/           # General purpose documents
├── processed/             # Processed document metadata and logs
├── chroma_stores/         # Vector store collections (auto-created)
│   ├── academic_documents/
│   ├── student_documents/
│   ├── admin_documents/
│   └── general_documents/
└── processing_metadata.json # Processing status tracking (auto-created)
```

## Usage Instructions

### 1. Upload Documents

Place your documents in the appropriate subdirectory under `raw/`:

- **Academic documents**: `raw/academic/`
- **Student materials**: `raw/student/`
- **Administrative docs**: `raw/admin/`
- **General documents**: `raw/general/`

### 2. Supported Formats

- PDF files (`.pdf`)
- Microsoft Word documents (`.doc`, `.docx`)
- Plain text files (`.txt`)

### 3. Processing Commands

```bash
# Process academic documents
python scripts/process_documents.py process-dir "data/raw/academic" "academic_documents"

# Process student materials
python scripts/process_documents.py process-dir "data/raw/student" "student_documents"

# Process administrative documents
python scripts/process_documents.py process-dir "data/raw/admin" "admin_documents"

# Process general documents
python scripts/process_documents.py process-dir "data/raw/general" "general_documents"
```

### 4. Verify Processing

```bash
# Check processing status
python scripts/process_documents.py status

# List available collections
python scripts/process_documents.py list-collections

# Get collection information
python scripts/process_documents.py collection-info "academic_documents"
```

## File Naming Conventions

For better organization and metadata tracking:

- Use descriptive filenames
- Include date if relevant: `2024_course_syllabus.pdf`
- Use underscores instead of spaces: `machine_learning_paper.pdf`
- Include language indicator if needed: `policy_document_tr.pdf`

## Notes

- The `chroma_stores/` and `processing_metadata.json` files are automatically created during processing
- Processed documents are stored as vector embeddings and can be searched using the document search functionality
- All processing is logged and tracked for debugging and status monitoring
- Turkish characters are fully supported in document content and filenames
