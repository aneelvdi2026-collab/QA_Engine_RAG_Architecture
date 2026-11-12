# QA_Engine_RAG_Architecture
QA Engine with RAG architecture backend 


End-to-End RAG Q&A ApplicationThis repository contains a full-stack Retrieval-Augmented Generation (RAG) system built with a modular architecture. It integrates a React frontend, a Node.js gateway, a FastAPI service, and a PostgreSQL database leveraging pgvector for semantic search.Architecture & Project StructureAI_QA_Engine_Project: Handles document loading, text chunking, embedding generation (text-embedding-3-small with 384 dimensions), and database table creation / insertion into PostgreSQL (pgvector).Fast_API_Project: The core AI microservice handling query embedding generation, cosine similarity vector search against the embeddings table, and answer synthesis using OpenAI's gpt-4o-mini.Node_Backend_Project: The backend gateway routing requests between the frontend and the FastAPI service.React_UI_Project: The user interface (ChatInterface.jsx) allowing users to query documents, view retrieved matches, inspect similarity scores, and review the generated context block.1. Database Setup (pgvector)Ensure PostgreSQL is installed with the pgvector extension enabled. Run the following SQL script to create the embeddings table (without the metadata column):SQL-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table with 384-dimensional vector support
DROP TABLE IF EXISTS embeddings;

CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding VECTOR(384)
);
2. Component Setup & Installation CommandsComponent 1: AI_QA_Engine_Project (Data Ingestion & Table Population)Bash# Navigate to project folder
cd AI_QA_Engine_Project

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install psycopg2-binary pgvector openai langchain langchain-community

# Configure environment variables (create a .env file or export in terminal)
export DATABASE_URL="postgresql://username:password@localhost:5432/your_database"
export OPENAI_API_KEY="your-openai-api-key"

# Run ingestion script to load files and populate pgvector
python ingest.py
Component 2: Fast_API_Project (FastAPI Retrieval & LLM Service)Bash# Navigate to project folder
cd Fast_API_Project

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn psycopg2-binary pgvector openai pydantic httpx

# Configure environment variables
export DATABASE_URL="postgresql://username:password@localhost:5432/your_database"
export OPENAI_API_KEY="your-openai-api-key"

# Run the FastAPI server
uvicorn main:app --reload --port 8000
Component 3: Node_Backend_Project (Node.js Gateway)Bash# Navigate to project folder
cd Node_Backend_Project

# Install dependencies
npm install express cors dotenv axios

# Create a .env file if required
echo "PORT=5000" > .env
echo "FASTAPI_URL=http://localhost:8000" >> .env

# Run the Node.js application
npm start
# Or using nodemon for development:
npx nodemon server.js
Component 4: React_UI_Project (React.js Frontend Interface)Bash# Navigate to project folder
cd React_UI_Project

# Install packages
npm install

# Run the development server (Vite)
npm run dev
End-to-End (E2E) Workflow ExplanationDocument Ingestion (AI_QA_Engine_Project):Raw text/markdown files inside the data/ directory are loaded, validated, and split into chunks.OpenAI's text-embedding-3-small model generates 384-dimensional vector embeddings for each chunk (via the dimensions=384 parameter).Chunks and their corresponding vectors are stored directly in the PostgreSQL embeddings table.Query Execution (React_UI_Project $\rightarrow$ Node_Backend_Project $\rightarrow$ Fast_API_Project):The user submits a question through the React UI (ChatInterface.jsx).The request is passed through the Node.js gateway to the FastAPI backend service (/semantic-search).FastAPI converts the incoming user query into a 384-dimensional embedding vector using OpenAI.Vector Similarity Search & Synthesis:FastAPI executes a cosine similarity query against PostgreSQL using the <=> operator from pgvector to fetch the top 5 most relevant text chunks from the embeddings table.Retrieved text chunks are concatenated to form the Generated Context Block.OpenAI's gpt-4o-mini model synthesizes a precise, context-aware answer.The response containing the synthesized answer, retrieved source text matches, similarity scores, and debug context is returned back through the gateway to render cleanly in the React UI.
