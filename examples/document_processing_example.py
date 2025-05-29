#!/usr/bin/env python3
"""
Example script demonstrating document processing functionality.
This script shows how to use the DocumentProcessor class to process documents
and integrate them with the document search functionality.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.document_processing import DocumentProcessor
from app.tools.document_search import DocumentSearchTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_documents():
    """Create sample documents for testing."""
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample text document
    sample_txt = data_dir / "sample_document.txt"
    with open(sample_txt, 'w', encoding='utf-8') as f:
        f.write("""
Atlas University Document Processing System

This is a sample document for testing the document processing functionality
of the Agentic RAG system developed by Atlas University in Istanbul, Turkey.

The system supports multiple document formats including PDF, Word documents,
and plain text files. It uses LangChain for document processing and OpenAI
embeddings for creating vector representations.

Key Features:
- Support for PDF, DOCX, DOC, and TXT files
- Automatic text chunking with configurable parameters
- Vector embeddings using OpenAI's text-embedding-3-small model
- Integration with Chroma vector database
- Batch processing capabilities
- Comprehensive error handling and logging

The processed documents can be searched using the document_search tool,
which provides semantic search capabilities across the document collection.

This system is designed to support Turkish and English languages,
making it suitable for the multilingual environment at Atlas University.

Türkçe metin desteği de bulunmaktadır. Sistem, Türkçe karakterleri
doğru şekilde işleyebilir ve arama yapabilir.
        """)
    
    # Sample academic document
    academic_txt = data_dir / "academic_sample.txt"
    with open(academic_txt, 'w', encoding='utf-8') as f:
        f.write("""
Research Paper: Artificial Intelligence in Education

Abstract:
This paper explores the applications of artificial intelligence in educational
settings, with a focus on personalized learning systems and intelligent
tutoring systems.

Introduction:
Artificial Intelligence (AI) has emerged as a transformative technology in
various domains, including education. The integration of AI in educational
systems offers unprecedented opportunities to enhance learning experiences
and improve educational outcomes.

Literature Review:
Previous studies have shown that AI-powered educational systems can adapt
to individual learning styles and provide personalized feedback to students.
Machine learning algorithms can analyze student performance data to identify
learning patterns and predict academic success.

Methodology:
This study employs a mixed-methods approach, combining quantitative analysis
of student performance data with qualitative interviews of educators and
students who have used AI-powered learning systems.

Results:
The findings indicate that students using AI-enhanced learning platforms
showed significant improvement in learning outcomes compared to traditional
teaching methods. The personalized approach led to increased engagement
and better retention of knowledge.

Conclusion:
AI has the potential to revolutionize education by providing personalized,
adaptive learning experiences. However, careful consideration must be given
to ethical implications and the need for human oversight in educational AI systems.

Keywords: Artificial Intelligence, Education, Personalized Learning,
Machine Learning, Educational Technology
        """)
    
    logger.info(f"Created sample documents in {data_dir}")
    return [sample_txt, academic_txt]


def demonstrate_document_processing():
    """Demonstrate the document processing functionality."""
    logger.info("=== Document Processing Demonstration ===")
    
    # Create sample documents
    sample_files = create_sample_documents()
    
    # Initialize document processor
    processor = DocumentProcessor(
        data_dir="data",
        embedding_model="text-embedding-3-small",
        chunk_size=500,  # Smaller chunks for demo
        chunk_overlap=100,
    )
    
    # Process individual documents
    logger.info("\n1. Processing individual documents:")
    
    for file_path in sample_files:
        collection_name = "demo_collection"
        logger.info(f"Processing: {file_path}")
        
        result = processor.process_document(
            str(file_path),
            collection_name,
            custom_metadata={"demo": True, "processed_by": "example_script"}
        )
        
        if result["success"]:
            logger.info(f"✅ Successfully processed {file_path.name}")
            logger.info(f"   Chunks created: {result['chunk_count']}")
            logger.info(f"   Total characters: {result['total_characters']}")
        else:
            logger.error(f"❌ Failed to process {file_path.name}: {result['error']}")
    
    # Process directory
    logger.info("\n2. Processing directory:")
    
    result = processor.process_directory(
        "data/raw",
        "batch_demo_collection",
        custom_metadata={"batch_processed": True}
    )
    
    if result["success"]:
        logger.info(f"✅ Batch processing completed")
        logger.info(f"   Total files: {result['total_files']}")
        logger.info(f"   Successful: {result['successful_count']}")
        logger.info(f"   Failed: {result['failed_count']}")
    else:
        logger.error(f"❌ Batch processing failed: {result['error']}")
    
    # List collections
    logger.info("\n3. Listing collections:")
    collections = processor.list_collections()
    for collection in collections:
        logger.info(f"   📁 {collection}")
    
    # Get collection info
    logger.info("\n4. Collection information:")
    for collection in collections:
        info = processor.get_collection_info(collection)
        if "error" not in info:
            logger.info(f"   Collection: {collection}")
            logger.info(f"     Documents: {info['document_count']}")
            logger.info(f"     Contributing files: {info['contributing_files']}")
    
    # Test search functionality
    logger.info("\n5. Testing search functionality:")
    
    test_queries = [
        "artificial intelligence in education",
        "Atlas University",
        "Türkçe metin",
        "document processing"
    ]
    
    for query in test_queries:
        logger.info(f"\n   Query: '{query}'")
        result = processor.search_documents(
            query,
            "demo_collection",
            top_k=2
        )
        
        if result["success"]:
            logger.info(f"   Found {result['count']} results:")
            for i, doc in enumerate(result["results"], 1):
                content_preview = doc["content"][:100].replace('\n', ' ')
                logger.info(f"     {i}. {content_preview}...")
        else:
            logger.error(f"   Search failed: {result['error']}")
    
    # Get processing status
    logger.info("\n6. Processing status:")
    status = processor.get_processing_status()
    logger.info(f"   Total files processed: {status['total_files']}")
    logger.info(f"   Successful: {status['successful']}")
    logger.info(f"   Failed: {status['failed']}")
    
    return processor


def demonstrate_integration_with_document_search():
    """Demonstrate integration with the existing DocumentSearchTool."""
    logger.info("\n=== Integration with DocumentSearchTool ===")
    
    # Configure the document search tool to use our processed documents
    config = {
        "collection_name": "demo_collection",
        "embedding_model": "text-embedding-3-small",
        "persist_directory": "./data/chroma_stores/demo_collection",
        "top_k": 3
    }
    
    # Initialize the document search tool
    search_tool = DocumentSearchTool(config)
    
    # Test queries
    test_queries = [
        "What is artificial intelligence?",
        "Atlas University features",
        "Turkish language support"
    ]
    
    logger.info("Testing DocumentSearchTool with processed documents:")
    
    for query in test_queries:
        logger.info(f"\n   Query: '{query}'")
        
        # Use the async execute method
        import asyncio
        result = asyncio.run(search_tool.execute(query))
        
        if result["success"]:
            logger.info(f"   Found {result['count']} documents:")
            for i, doc in enumerate(result["documents"], 1):
                content_preview = doc["content"][:80].replace('\n', ' ')
                source = doc["metadata"].get("source_file", "Unknown")
                logger.info(f"     {i}. Source: {Path(source).name}")
                logger.info(f"        Content: {content_preview}...")
        else:
            logger.error(f"   Search failed: {result['error']}")


def cleanup_demo_data():
    """Clean up demo data (optional)."""
    logger.info("\n=== Cleanup (Optional) ===")
    
    processor = DocumentProcessor(data_dir="data")
    
    # List collections before cleanup
    collections = processor.list_collections()
    demo_collections = [c for c in collections if "demo" in c.lower()]
    
    if demo_collections:
        logger.info("Demo collections found:")
        for collection in demo_collections:
            logger.info(f"   📁 {collection}")
        
        response = input("\nDo you want to delete demo collections? (y/N): ")
        if response.lower() == 'y':
            for collection in demo_collections:
                result = processor.delete_collection(collection)
                if result["success"]:
                    logger.info(f"✅ Deleted collection: {collection}")
                else:
                    logger.error(f"❌ Failed to delete {collection}: {result['error']}")
    else:
        logger.info("No demo collections found.")


def main():
    """Main demonstration function."""
    logger.info("Starting Document Processing Demonstration")
    logger.info("=" * 60)
    
    try:
        # Demonstrate document processing
        processor = demonstrate_document_processing()
        
        # Demonstrate integration with document search
        demonstrate_integration_with_document_search()
        
        # Optional cleanup
        cleanup_demo_data()
        
        logger.info("\n" + "=" * 60)
        logger.info("Document Processing Demonstration Completed Successfully!")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
