import os
import sqlite3
import sqlite_vec
from typing import List
from pathlib import Path
import argparse
import logging
import hashlib

# Requires: pip install sqlite-vec sentence-transformers
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def init_db(db_path: Path):
    """Initialize SQLite database with sqlite-vec extension."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Establish connection and load extension
    db = sqlite3.connect(db_path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    
    # Create chunks metadata table
    db.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL,
            file_mtime REAL NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL
        )
    """)
    
    # Create vector table (assuming 384 dimensions for all-MiniLM-L6-v2)
    # Using virtual table vss0 for vector search if needed, but sqlite_vec uses vec0
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
            chunk_embedding float[384]
        )
    """)
    
    db.commit()
    return db

def chunk_text(text: str, max_chars: int = 1500) -> List[str]:
    """
    Very basic chunking strategy. 
    In a real RAG system, consider Markdown headers or semantic boundaries.
    """
    # Simply split by paragraphs and aggregate until max_chars
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def build_index(src_dir: Path, db_path: Path):
    """Main function to chunk markdown and build the vector DB."""
    if not src_dir.exists():
        logging.error(f"Source directory '{src_dir}' not found.")
        return

    # Load local SentenceTransformer model
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    logging.info(f"Loading embedding model: {model_name}...")
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        logging.error(f"Failed to load sentence-transformers. Did you `pip install sentence-transformers`? Error: {e}")
        return

    db = init_db(db_path)
    cursor = db.cursor()

    # Track files already in DB to handle updates
    cursor.execute("SELECT filepath, file_mtime FROM chunks GROUP BY filepath")
    existing_files = {row[0]: row[1] for row in cursor.fetchall()}

    processed_count = 0
    skipped_count = 0

    for filepath in src_dir.rglob('*.md'):
        if not filepath.is_file(): continue
        
        path_str = str(filepath.relative_to(src_dir))
        mtime = filepath.stat().st_mtime
        
        # Skip if file hasn't changed since last insert
        if path_str in existing_files and existing_files[path_str] == mtime:
            skipped_count += 1
            continue

        # If it exists but changed, delete old chunks
        if path_str in existing_files:
            # Delete from vec table using the internal rowid match
            cursor.execute("DELETE FROM vec_chunks WHERE rowid IN (SELECT id FROM chunks WHERE filepath = ?)", (path_str,))
            cursor.execute("DELETE FROM chunks WHERE filepath = ?", (path_str,))
            
        logging.info(f"Processing {path_str}...")
        try:
            content = filepath.read_text(encoding='utf-8')
            chunks = chunk_text(content)
            
            # Generate embeddings for all chunks in the document
            embeddings = model.encode(chunks)
            
            # Insert into database
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Insert metadata
                cursor.execute(
                    "INSERT INTO chunks (filepath, file_mtime, chunk_index, content) VALUES (?, ?, ?, ?)",
                    (path_str, mtime, i, chunk)
                )
                chunk_id = cursor.lastrowid
                
                # Insert vector (sqlite-vec uses float array format, we cast to bytes if needed or pass list depending on bindings)
                # Note: precise sqlite-vec python bindings for inserts check docs, usually it accepts bytes or lists depending on the adapter.
                # Assuming the python wrapper `sqlite_vec` registers appropriate adapters for numpy arrays/lists.
                
                # sqlite_vec vec0 tables require the rowid to match if we want to join them
                cursor.execute(
                    "INSERT INTO vec_chunks (rowid, chunk_embedding) VALUES (?, ?)", 
                    (chunk_id, sqlite_vec.serialize_float32(embedding.tolist()))
                )
                
            db.commit()
            processed_count += 1
            
        except Exception as e:
            logging.error(f"Error processing {path_str}: {e}")
            db.rollback()

    logging.info(f"RAG DB Build complete. Processed {processed_count} files, skipped {skipped_count} unmodified files.")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build SQLite-vec RAG Database from Markdown files")
    parser.add_argument("--src-dir", required=True, help="Directory containing markdown files")
    parser.add_argument("--db-path", default="knowledge_rag.sqlite", help="Output SQLite database path")
    
    args = parser.parse_args()
    build_index(Path(args.src_dir), Path(args.db_path))
