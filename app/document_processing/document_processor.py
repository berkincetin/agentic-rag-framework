"""
Document processing system for the Agentic RAG application.
Handles PDF, Word, DOCX, and text format files with LangChain integration.
"""

import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Document processing system for the Agentic RAG application.
    Processes documents and stores them in Chroma vector store for search functionality.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf": PyPDFLoader,
        ".docx": Docx2txtLoader,
        ".doc": UnstructuredWordDocumentLoader,
        ".txt": TextLoader,
    }

    def __init__(
        self,
        data_dir: str = "data",
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the document processor.

        Args:
            data_dir: Base directory for document storage
            embedding_model: OpenAI embedding model to use
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
        """
        self.data_dir = Path(data_dir)
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Create directory structure
        self._create_directories()

        # Initialize components
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        # Initialize metadata tracking
        self.metadata_file = self.data_dir / "processing_metadata.json"
        self.processing_metadata = self._load_metadata()

        logger.info(f"DocumentProcessor initialized with data_dir: {self.data_dir}")

    def _create_directories(self) -> None:
        """Create necessary directory structure."""
        directories = [
            self.data_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "chroma_stores",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")

    def _load_metadata(self) -> Dict[str, Any]:
        """Load processing metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save processing metadata to file."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.processing_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def _get_document_loader(self, file_path: Path) -> Optional[Any]:
        """
        Get appropriate document loader for file type.

        Args:
            file_path: Path to the document

        Returns:
            Document loader instance or None if unsupported
        """
        extension = file_path.suffix.lower()
        loader_class = self.SUPPORTED_EXTENSIONS.get(extension)

        if not loader_class:
            logger.warning(f"Unsupported file type: {extension}")
            return None

        try:
            if extension == ".txt":
                return loader_class(str(file_path), encoding="utf-8")
            else:
                return loader_class(str(file_path))
        except Exception as e:
            logger.error(f"Error creating loader for {file_path}: {e}")
            return None

    def process_document(
        self,
        file_path: str,
        collection_name: str,
        persist_directory: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a single document and store it in Chroma vector store.

        Args:
            file_path: Path to the document to process
            collection_name: Name of the Chroma collection
            persist_directory: Directory to persist Chroma data
            custom_metadata: Additional metadata to attach to document chunks

        Returns:
            Dictionary containing processing results
        """
        file_path = Path(file_path)

        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            # Get document loader
            loader = self._get_document_loader(file_path)
            if not loader:
                error_msg = f"Unsupported file type: {file_path.suffix}"
                return {"success": False, "error": error_msg}

            # Load document
            logger.info(f"Loading document: {file_path}")
            documents = loader.load()

            if not documents:
                error_msg = f"No content extracted from: {file_path}"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg}

            # Split documents into chunks
            logger.info(f"Splitting document into chunks: {file_path}")
            chunks = self.text_splitter.split_documents(documents)

            # Add metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk.metadata.update(
                    {
                        "source_file": str(file_path),
                        "file_name": file_path.name,
                        "file_extension": file_path.suffix,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "processed_at": datetime.now().isoformat(),
                        "processor_version": "1.0.0",
                    }
                )

                if custom_metadata:
                    chunk.metadata.update(custom_metadata)

            # Initialize Chroma vector store
            if not persist_directory:
                persist_directory = str(
                    self.data_dir / "chroma_stores" / collection_name
                )

            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory,
            )

            # Add documents to vector store
            logger.info(
                f"Adding {len(chunks)} chunks to vector store: {collection_name}"
            )
            vector_store.add_documents(chunks)

            # Update metadata tracking
            file_key = str(file_path)
            self.processing_metadata[file_key] = {
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "processed_at": datetime.now().isoformat(),
                "collection_name": collection_name,
                "persist_directory": persist_directory,
                "chunk_count": len(chunks),
                "status": "success",
            }
            self._save_metadata()

            result = {
                "success": True,
                "file_path": str(file_path),
                "collection_name": collection_name,
                "persist_directory": persist_directory,
                "chunk_count": len(chunks),
                "total_characters": sum(len(chunk.page_content) for chunk in chunks),
            }

            logger.info(f"Successfully processed document: {file_path}")
            return result

        except Exception as e:
            error_msg = f"Error processing document {file_path}: {str(e)}"
            logger.error(error_msg)

            # Update metadata with error
            file_key = str(file_path)
            self.processing_metadata[file_key] = {
                "file_name": file_path.name,
                "processed_at": datetime.now().isoformat(),
                "status": "error",
                "error": str(e),
            }
            self._save_metadata()

            return {"success": False, "error": error_msg}

    def process_directory(
        self,
        directory_path: str,
        collection_name: str,
        persist_directory: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """
        Process all supported documents in a directory.

        Args:
            directory_path: Path to directory containing documents
            collection_name: Name of the Chroma collection
            persist_directory: Directory to persist Chroma data
            custom_metadata: Additional metadata to attach to document chunks
            recursive: Whether to process subdirectories

        Returns:
            Dictionary containing batch processing results
        """
        directory_path = Path(directory_path)

        if not directory_path.exists() or not directory_path.is_dir():
            error_msg = f"Directory not found: {directory_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        # Find all supported files
        pattern = "**/*" if recursive else "*"
        all_files = list(directory_path.glob(pattern))

        supported_files = [
            f
            for f in all_files
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]

        if not supported_files:
            error_msg = f"No supported files found in: {directory_path}"
            logger.warning(error_msg)
            return {"success": False, "error": error_msg}

        logger.info(f"Found {len(supported_files)} supported files to process")

        # Process each file
        results = []
        successful_count = 0
        failed_count = 0

        for file_path in supported_files:
            logger.info(
                f"Processing file {successful_count + failed_count + 1}/{len(supported_files)}: {file_path}"
            )

            result = self.process_document(
                str(file_path),
                collection_name,
                persist_directory,
                custom_metadata,
            )

            results.append(result)

            if result["success"]:
                successful_count += 1
            else:
                failed_count += 1

        batch_result = {
            "success": True,
            "directory_path": str(directory_path),
            "collection_name": collection_name,
            "total_files": len(supported_files),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "results": results,
        }

        logger.info(
            f"Batch processing completed: {successful_count} successful, {failed_count} failed"
        )
        return batch_result

    def get_processing_status(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get processing status for files.

        Args:
            file_path: Specific file path to check, or None for all files

        Returns:
            Dictionary containing processing status information
        """
        if file_path:
            file_key = str(Path(file_path))
            return self.processing_metadata.get(file_key, {"status": "not_processed"})

        return {
            "total_files": len(self.processing_metadata),
            "successful": len(
                [
                    m
                    for m in self.processing_metadata.values()
                    if m.get("status") == "success"
                ]
            ),
            "failed": len(
                [
                    m
                    for m in self.processing_metadata.values()
                    if m.get("status") == "error"
                ]
            ),
            "files": self.processing_metadata,
        }

    def list_collections(self) -> List[str]:
        """
        List all available Chroma collections.

        Returns:
            List of collection names
        """
        chroma_dir = self.data_dir / "chroma_stores"
        if not chroma_dir.exists():
            return []

        collections = []
        for item in chroma_dir.iterdir():
            if item.is_dir():
                collections.append(item.name)

        return sorted(collections)

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a specific collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary containing collection information
        """
        persist_directory = str(self.data_dir / "chroma_stores" / collection_name)

        try:
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory,
            )

            # Get collection statistics
            collection = vector_store._collection
            count = collection.count()

            # Find files that contributed to this collection
            contributing_files = [
                metadata
                for metadata in self.processing_metadata.values()
                if metadata.get("collection_name") == collection_name
                and metadata.get("status") == "success"
            ]

            return {
                "collection_name": collection_name,
                "persist_directory": persist_directory,
                "document_count": count,
                "contributing_files": len(contributing_files),
                "files": contributing_files,
            }

        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return {
                "collection_name": collection_name,
                "error": str(e),
            }

    def search_documents(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        persist_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search documents in a collection (for testing purposes).

        Args:
            query: Search query
            collection_name: Name of the collection to search
            top_k: Number of results to return
            persist_directory: Directory where Chroma data is persisted

        Returns:
            Dictionary containing search results
        """
        if not persist_directory:
            persist_directory = str(self.data_dir / "chroma_stores" / collection_name)

        try:
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory,
            )

            docs = vector_store.similarity_search(query, k=top_k)

            results = []
            for doc in docs:
                results.append(
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                    }
                )

            return {
                "success": True,
                "query": query,
                "collection_name": collection_name,
                "results": results,
                "count": len(results),
            }

        except Exception as e:
            error_msg = f"Error searching collection {collection_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        Delete a collection and its associated data.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            Dictionary containing deletion results
        """
        persist_directory = self.data_dir / "chroma_stores" / collection_name

        try:
            # Remove the directory
            if persist_directory.exists():
                import shutil

                shutil.rmtree(persist_directory)
                logger.info(f"Deleted collection directory: {persist_directory}")

            # Update metadata to remove references to this collection
            updated_metadata = {}
            for file_key, metadata in self.processing_metadata.items():
                if metadata.get("collection_name") != collection_name:
                    updated_metadata[file_key] = metadata

            self.processing_metadata = updated_metadata
            self._save_metadata()

            return {
                "success": True,
                "collection_name": collection_name,
                "message": f"Collection {collection_name} deleted successfully",
            }

        except Exception as e:
            error_msg = f"Error deleting collection {collection_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
