#!/usr/bin/env python3
"""
CLI script for processing documents using the DocumentProcessor.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.document_processing import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Process documents for the Agentic RAG system"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process single file command
    process_file_parser = subparsers.add_parser(
        "process-file", help="Process a single document file"
    )
    process_file_parser.add_argument(
        "file_path", help="Path to the document file to process"
    )
    process_file_parser.add_argument(
        "collection_name", help="Name of the Chroma collection to store the document"
    )
    process_file_parser.add_argument(
        "--persist-dir", help="Directory to persist Chroma data (optional)"
    )

    # Process directory command
    process_dir_parser = subparsers.add_parser(
        "process-dir", help="Process all documents in a directory"
    )
    process_dir_parser.add_argument(
        "directory_path", help="Path to the directory containing documents"
    )
    process_dir_parser.add_argument(
        "collection_name", help="Name of the Chroma collection to store the documents"
    )
    process_dir_parser.add_argument(
        "--persist-dir", help="Directory to persist Chroma data (optional)"
    )
    process_dir_parser.add_argument(
        "--recursive", action="store_true", help="Process subdirectories recursively"
    )

    # List collections command
    list_parser = subparsers.add_parser(
        "list-collections", help="List all available collections"
    )

    # Collection info command
    info_parser = subparsers.add_parser(
        "collection-info", help="Get information about a collection"
    )
    info_parser.add_argument("collection_name", help="Name of the collection")

    # Search command
    search_parser = subparsers.add_parser(
        "search", help="Search documents in a collection"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "collection_name", help="Name of the collection to search"
    )
    search_parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results to return (default: 5)"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Get processing status")
    status_parser.add_argument(
        "--file-path", help="Specific file path to check (optional)"
    )

    # Delete collection command
    delete_parser = subparsers.add_parser(
        "delete-collection", help="Delete a collection"
    )
    delete_parser.add_argument(
        "collection_name", help="Name of the collection to delete"
    )
    delete_parser.add_argument(
        "--confirm", action="store_true", help="Confirm deletion without prompting"
    )

    # Common arguments
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Base directory for document storage (default: data)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Size of text chunks for splitting (default: 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between chunks (default: 200)",
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-small",
        help="OpenAI embedding model (default: text-embedding-3-small)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize document processor
    processor = DocumentProcessor(
        data_dir=args.data_dir,
        embedding_model=args.embedding_model,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    try:
        if args.command == "process-file":
            result = processor.process_document(
                args.file_path,
                args.collection_name,
                args.persist_dir,
            )
            print_result(result)

        elif args.command == "process-dir":
            result = processor.process_directory(
                args.directory_path,
                args.collection_name,
                args.persist_dir,
                recursive=args.recursive,
            )
            print_result(result)

        elif args.command == "list-collections":
            collections = processor.list_collections()
            if collections:
                print("Available collections:")
                for collection in collections:
                    print(f"  - {collection}")
            else:
                print("No collections found.")

        elif args.command == "collection-info":
            info = processor.get_collection_info(args.collection_name)
            print_result(info)

        elif args.command == "search":
            result = processor.search_documents(
                args.query,
                args.collection_name,
                args.top_k,
            )
            print_search_results(result)

        elif args.command == "status":
            status = processor.get_processing_status(args.file_path)
            print_result(status)

        elif args.command == "delete-collection":
            if not args.confirm:
                response = input(
                    f"Are you sure you want to delete collection '{args.collection_name}'? (y/N): "
                )
                if response.lower() != "y":
                    print("Deletion cancelled.")
                    return

            result = processor.delete_collection(args.collection_name)
            print_result(result)

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        sys.exit(1)


def print_result(result):
    """Print a result dictionary in a formatted way."""
    if isinstance(result, dict):
        if result.get("success", True):
            print("✅ Success!")
            for key, value in result.items():
                if key != "success":
                    print(f"  {key}: {value}")
        else:
            print("❌ Error!")
            print(f"  Error: {result.get('error', 'Unknown error')}")
    else:
        print(result)


def print_search_results(result):
    """Print search results in a formatted way."""
    if not result.get("success", True):
        print("❌ Search failed!")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        return

    results = result.get("results", [])
    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} results for query: '{result.get('query', '')}'")
    print("-" * 80)

    for i, doc in enumerate(results, 1):
        print(f"\n📄 Result {i}:")
        print(f"  Source: {doc['metadata'].get('source_file', 'Unknown')}")
        print(f"  Chunk: {doc['metadata'].get('chunk_index', 'N/A')}")
        print(f"  Content: {doc['content'][:200]}...")
        if len(doc["content"]) > 200:
            print("  [Content truncated]")


if __name__ == "__main__":
    main()
