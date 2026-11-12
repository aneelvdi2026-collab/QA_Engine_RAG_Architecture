from ast import main
import os
import sys
import logging
import dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from pypdf import PdfReader
#from openai.document_loaders import TextLoader
import os
from pathlib import Path
from langchain_core.documents import Document

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import CrossEncoder

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from pathlib import Path
import logging
import psycopg2
from openai import OpenAI

dotenv.load_dotenv()


#log_path = Path(os.getenv("LOG_PATH"))

# Configure the root logger
logging.basicConfig(
    filename="rag_ingest.log",  # Combine Path and string using /
    encoding="utf-8",
    filemode="a",                          # Append to the file ('w' overwrites)
    level=logging.INFO,                    # Minimum severity level to record
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create a module-level logger
logger = logging.getLogger(__name__)

dotenv.load_dotenv()


DATA_FILE_PATH = Path(__file__).parent / "data" 

#----------------------------------------------------

#Load documents from /data directory and  convert the text to lang chain document-- step1

#---------------------------------------------------

def load_multi_file(directory_path: str) -> list[Document]:
    """
    Robustly loads text and markdown files from a directory, 
    handling encodings, hidden files, and empty documents.
    """
    path = Path(directory_path)
    
    if not path.exists() or not path.is_dir():
        print(f"Warning: Directory '{directory_path}' does not exist or is not a directory.")
        return []

    documents = []
    
    # Recursively traverse all files in the directory
    for file_path in path.glob('**/*'):
        # Skip directories and hidden system files (e.g., .DS_Store)
        if not file_path.is_file() or file_path.name.startswith('.'):
            continue
            
        # Filter for supported text-based extensions
        if file_path.suffix.lower() in ['.txt', '.md', '.csv']:
            content = None
            
            # Try UTF-8 first, fallback to latin-1 if encoding fails
            for encoding in ['utf-8', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break # Break out of encoding loop if successful
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Error opening file {file_path.name}: {e}")
                    break

            # If content was read successfully and isn't empty
            if content and content.strip():
                doc = Document(
                    page_content=content,
                    metadata={"source": str(file_path), "filename": file_path.name}
                )
                documents.append(doc)
            else:
                print(f"Skipping empty or unreadable file: {file_path.name}")

    print(f"Successfully loaded {len(documents)} valid documents from {directory_path}")
    return documents


#----------------------------------------------------

#convert documents to chunks -- step2

#---------------------------------------------------

def create_chunks(docs):
    """
    Create chunks from the loaded documents.

    Args:
        docs (str): The combined content of the loaded documents.

    Returns:
        list: A list of chunked text.
    """
    logger.info("inside create_chunks method")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)
    
    #print(chunks[0])
    return chunks

#----------------------------------------------------

#convert chunks to embedding vectors for storing in vector db -- step3

#---------------------------------------------------

def convert_to_embedding_vectors(chunks):
    """
    Convert the chunks to embeddings using OpenAIEmbeddings.

    Args:
        chunks (list): A list of chunked text.

    Returns:
        list: A list of embeddings.
    """

    logger.info("inside convert_to_embedding_vectors method")

    #embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2") #text-embedding-3-large
    #embedding_vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
     # 1. Generate embedding for query (ensure input is a clean string)

     # 1. Check if chunks list is empty
    if not chunks:
        print("Warning: No chunks provided for embedding generation.")
        # Handle the empty case (e.g., return an error or empty result)

    # 2. Extract texts and ensure no empty strings are passed
    texts = [chunk.page_content for chunk in chunks if chunk.page_content and chunk.page_content.strip()]

    if not texts:
        raise ValueError("Chunks contain no valid text to embed.")

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 3. Call OpenAI embeddings
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
        dimensions=384
    )

    # 3. Extract the embedding vector array from each item in response.data
    embedding_vectors = [item.embedding for item in response.data]

    # Now embedding_vectors is a clean list of lists: [[0.12, -0.03, ...], [0.05, 0.22, ...]]
    # Ensure you access the data array returned by the OpenAI API response
    logger.info("Size of the embedding vectors: %d", len(embedding_vectors))
    return embedding_vectors

#----------------------------------------------------

# Store the embeddings in Vector Database-- step4
#---------------------------------------------------

def save_to_pgvector_database(embeddings,chunks):
    """
    Save the embeddings to a PostgreSQL database with pgvector extension.

    Args:
        embeddings (list): A list of embeddings.

    """
    logger.info("inside save_to_pgvector_database")
    dbname = os.getenv("DB_NAME", "your_db_name")
    username = os.getenv("DB_USER", "your_username")
    password = os.getenv("DB_PASSWORD", "your_password")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")

    # Connect to your PostgreSQL database
    conn = psycopg2.connect(
        dbname=dbname,
        user=username,
        password=password,
        host=host,
        port=port
    )
    
    cursor = conn.cursor()

    # Create a table for storing embeddings if it doesn't exist

    cursor.execute("""
        DROP TABLE IF EXISTS embeddings;
        CREATE TABLE embeddings (
            id serial PRIMARY KEY,
            embedding vector(384),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            content TEXT
        );
    """)
    #conn.commit()
    
    # 2. Enable the pgvector extension (pre-installed in pgvector/pgvector images)
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    #connection.commit()

      # Create HNSW index in the table `sentence_embeddings` for efficient similarity search
    cursor.execute("""
        CREATE INDEX 
        ON embeddings 
        USING hnsw (embedding vector_l2_ops) 
        WITH (m = 16, ef_construction = 64);
    """)

    for embedding in embeddings:
        #cursor.execute("INSERT INTO embeddings (embedding, content) VALUES (%s, %s)", (embedding, "Sample content"))
        cursor.execute("INSERT INTO embeddings (embedding, content) VALUES (%s, %s)",
                        (embedding, chunks[embeddings.index(embedding)].page_content  if chunks else "Sample content"))
    

    #connection.commit()
    logger.info("save_to_pgvector_database completed")
    conn.commit()
    cursor.close()
    conn.close()



def main():

    from pathlib import Path

    # Get the absolute path to the directory containing main.py
    BASE_DIR = Path(__file__).resolve().parent

    # Build a safe, absolute path to your data folder
    data_path = BASE_DIR / "data"  # Or BASE_DIR / "AI_QA_Engine_Project" / "data" if needed

    #docs = load_multi_file(str(data_path))

    try: 
        logger.info("Ingestion process is triggered.")
        docs = load_multi_file(data_path)
        logger.info("Data loading is completed.")
        logger.info(docs[0])
        chunks = create_chunks(docs)
        logger.info("Chunking process is completed.")
        logger.info(chunks[0].page_content)
        embeddings = convert_to_embedding_vectors(chunks)
        save_to_pgvector_database(embeddings, chunks)       
    except Exception as e:
            logger.info(f"Error during retrieval: {e}")   


if __name__ == "__main__":
    main()
