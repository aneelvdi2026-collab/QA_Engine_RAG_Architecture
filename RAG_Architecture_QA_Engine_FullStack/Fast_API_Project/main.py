import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import logging
import dotenv
from fastapi.middleware.cors import CORSMiddleware

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG AI Service", version="1.0")
# 2. Add CORS middleware configuration right below app initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Allows Vite & React dev servers
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Allows all headers (Content-Type, Authorization, etc.)
)

# Environment variables & Clients
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:mysecretpassword@localhost:5433/postgres")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic schema for incoming requests
class SearchRequest(BaseModel):
    query: str

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        register_vector(conn)
        logger.info("Database connection is successful")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

def load_multi_file(directory_path: str):
    """
    Robustly loads text and markdown files from a directory, 
    handling encodings, hidden files, and empty documents.
    """
    path = Path(directory_path)
    
    if not path.exists() or not path.is_dir():
        logger.warning(f"Directory '{directory_path}' does not exist or is not a directory.")
        return []

    documents = []
    
    for file_path in path.glob('**/*'):
        if not file_path.is_file() or file_path.name.startswith('.'):
            continue
            
        if file_path.suffix.lower() in ['.txt', '.md', '.csv']:
            content = None
            for encoding in ['utf-8', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error opening file {file_path.name}: {e}")
                    break

            if content and content.strip():
                documents.append({
                    "page_content": content,
                    "metadata": {"filename": file_path.name}
                })
            else:
                logger.warning(f"Skipping empty or unreadable file: {file_path.name}")

    logger.info(f"Successfully loaded {len(documents)} valid documents from {directory_path}")
    return documents

@app.post("/semantic-search")
def semantic_search(req: SearchRequest):
    try:
        # 1. Generate embedding for query
        logger.info("Generating query embedding...")
        query_embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[req.query],
            dimensions=384  # Matches VECTOR(384) in PostgreSQL
        )
        query_embedding = query_embedding_response.data[0].embedding
        logger.info("Query embedding is successful")

        # 2. Connect to database and query pgvector
        conn = get_db_connection()
        cursor = conn.cursor()

        # Perform cosine similarity search (using <=> operator)
        # Adjust table name/columns if your schema varies slightly
        cursor.execute(
            """
            SELECT content, 1 - (embedding <=> %s::vector) AS similarity
            FROM embeddings
            ORDER BY embedding <=> %s::vector
            LIMIT 5;
            """,
            (query_embedding, query_embedding)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        retrieved_matches = []
        context_parts = []
        for row in rows:
            content, similarity = row
            retrieved_matches.append({
                "content": content,
                #"metadata": metadata,
                "score": float(similarity)
            })
            context_parts.append(content)

        generated_context = "\n\n".join(context_parts)

        logger.info("Generated Context is successful")

        # 3. Generate synthesized answer using LLM
        if not context_parts:
            answer = "I couldn't find any relevant documents in the database to answer your question."
        else:
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Answer the user's question using ONLY the provided context. If the answer cannot be found in the context, state that clearly."
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{generated_context}\n\nQuestion: {req.query}"
                    }
                ],
                temperature=0.2
            )
            answer = completion.choices[0].message.content

        logger.info("Generate synthesized answer using LLM is successful")


        return {
            "answer": answer,
            "generated_context": generated_context,
            "matches": retrieved_matches
        }

    except Exception as e:
        logger.error(f"Error during retrieval: {e}")
        raise HTTPException(status_code=500, detail=str(e))