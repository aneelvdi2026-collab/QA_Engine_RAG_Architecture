# 🤖 End-to-End RAG Q&A Application

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

A full-stack **Retrieval-Augmented Generation (RAG)** Question & Answering system built with a modular microservice architecture. Ingest custom documents into PostgreSQL (`pgvector`), perform sub-second cosine similarity searches using 384-dimensional embeddings, and synthesize accurate, context-grounded answers via OpenAI's `gpt-4o-mini`.

---

## 📑 Table of Contents
- [Architecture Overview](#-architecture-overview)
- [Repository Structure](#-repository-structure)
- [Prerequisites](#-prerequisites)
- [Step 1: Database Setup (`pgvector`)](#-step-1-database-setup-pgvector)
- [Step 2: Project Folder & Component Setup](#-step-2-project-folder--component-setup)
- [Step 3: Running the Full Stack](#-step-3-running-the-full-stack)
- [End-to-End (E2E) Data Flow](#-end-to-end-e2e-data-flow)
- [Troubleshooting](#-troubleshooting)

---

## 🏗️ Architecture Overview

```text
+-------------------+       +-----------------------+       +----------------------+
|                   |       |                       |       |                      |
|  React_UI_Project | ----> | Node_Backend_Project  | ----> |   Fast_API_Project   |
|  (Port: 5173)     | <---- | (Gateway Port: 5000)  | <---- |   (AI Port: 8000)    |
|                   |       |                       |       |                      |
+-------------------+       +-----------------------+       +----------+-----------+
                                                                       |
                                                                       | Cosine Search (<=>)
                                                                       v
+-----------------------+                                   +----------------------+
|                       |       384-Dim Embeddings          |                      |
| AI_QA_Engine_Project  | --------------------------------> | PostgreSQL + pgvector|
| (Data Ingestion CLI)  |                                   | Table: `embeddings`  |
|                       |                                   |                      |
+-----------------------+                                   +----------------------+
```

---

## 📂 Repository Structure

| Component | Directory Name | Tech Stack | Default Port | Responsibility |
| :--- | :--- | :--- | :---: | :--- |
| **Ingestion Engine** | `AI_QA_Engine_Project` | Python, LangChain, OpenAI | *CLI Script* | Loads files from `data/`, chunks text, creates 384-dim embeddings, and populates PostgreSQL. |
| **AI Retrieval API** | `Fast_API_Project` | Python, FastAPI, `psycopg2` | `8000` | Embeds user queries, executes `pgvector` similarity searches, and synthesizes answers via `gpt-4o-mini`. |
| **API Gateway** | `Node_Backend_Project` | Node.js, Express, Axios | `5000` | Acts as the middleware gateway routing requests between the UI and FastAPI service. |
| **Frontend UI** | `React_UI_Project` | React, Vite | `5173` | Interactive chat UI (`ChatInterface.jsx`) displaying answers, similarity scores, and debug context. |

---

## 📋 Prerequisites

Before setting up the workspace, ensure you have the following installed:
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **PostgreSQL 15+** with the **`pgvector`** extension installed
- An active **OpenAI API Key**

---

## 🗄️ Step 1: Database Setup (`pgvector`)

Connect to your PostgreSQL instance (`psql` or pgAdmin) and initialize the database and `embeddings` table:

```sql
-- 1. Create and connect to the database
CREATE DATABASE rag_db;
\c rag_db

-- 2. Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 3. Create the embeddings table (384 dimensions)
DROP TABLE IF EXISTS embeddings;

CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(384)
);

-- 4. Optional: Create an HNSW index for high-speed cosine similarity search
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## 🛠️ Step 2: Project Folder & Component Setup

Create a root workspace directory (e.g., `RAG_QA_System`) and set up each of the four component folders inside it:

```bash
mkdir RAG_QA_System && cd RAG_QA_System
```

### 1. `AI_QA_Engine_Project` (Data Ingestion & Table Population)

```bash
mkdir -p AI_QA_Engine_Project/data && cd AI_QA_Engine_Project

# Create & activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install psycopg2-binary pgvector openai langchain langchain-community langchain-core

# Create .env file
cat <<EOF > .env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/rag_db
OPENAI_API_KEY=sk-your-openai-api-key
EOF

# Place your .txt, .md, or .csv documents inside AI_QA_Engine_Project/data/
# Run ingestion script to populate the `embeddings` table
python ingest.py

cd ..
```

### 2. `Fast_API_Project` (FastAPI Retrieval & LLM Service)

```bash
mkdir Fast_API_Project && cd Fast_API_Project

# Create & activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install fastapi uvicorn psycopg2-binary pgvector openai pydantic httpx python-dotenv

# Create .env file
cat <<EOF > .env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/rag_db
OPENAI_API_KEY=sk-your-openai-api-key
EOF

cd ..
```

### 3. `Node_Backend_Project` (Node.js Gateway)

```bash
mkdir Node_Backend_Project && cd Node_Backend_Project

# Initialize Node project and install packages
npm init -y
npm install express cors dotenv axios
npm install --save-dev nodemon

# Create .env file
cat <<EOF > .env
PORT=5000
FASTAPI_URL=http://localhost:8000
EOF

cd ..
```

### 4. `React_UI_Project` (React.js Frontend Interface)

```bash
# Scaffold React project with Vite
npm create vite@latest React_UI_Project -- --template react
cd React_UI_Project

# Install dependencies
npm install

# Place ChatInterface.jsx inside src/components/ChatInterface.jsx and import it in src/App.jsx
cd ..
```

---

## 🚀 Step 3: Running the Full Stack

Open **three separate terminal windows** inside your `RAG_QA_System` root directory to run the services concurrently:

| Terminal | Service | Directory | Command | URL |
| :--- | :--- | :--- | :--- | :--- |
| **Terminal 1** | **FastAPI Service** | `Fast_API_Project/` | `uvicorn main:app --reload --port 8000` | `http://localhost:8000/docs` |
| **Terminal 2** | **Node.js Gateway** | `Node_Backend_Project/` | `npx nodemon server.js` *(or `npm start`)* | `http://localhost:5000` |
| **Terminal 3** | **React Frontend** | `React_UI_Project/` | `npm run dev` | `http://localhost:5173` |

> **Tip:** Make sure your Python virtual environment (`source venv/bin/activate`) is activated in **Terminal 1** before running `uvicorn`.

---

## 🔄 End-to-End (E2E) Data Flow

1. **Ingestion (`AI_QA_Engine_Project`)**:
   - Reads raw `.txt`, `.md`, and `.csv` files from `data/` with automatic `utf-8` / `latin-1` encoding fallbacks.
   - Splits documents into semantic text chunks and calls OpenAI's `text-embedding-3-small` with `dimensions=384`.
   - Inserts `(content, embedding)` rows directly into the PostgreSQL `embeddings` table.
2. **User Query (`React_UI_Project` $\rightarrow$ `Node_Backend_Project` $\rightarrow$ `Fast_API_Project`)**:
   - The user enters a question in `ChatInterface.jsx`.
   - The request routes through the Node.js gateway to FastAPI's `POST /semantic-search` endpoint.
   - FastAPI embeds the incoming query into a 384-dimensional vector.
3. **Retrieval & Generation (`Fast_API_Project`)**:
   - Queries PostgreSQL using the `pgvector` cosine distance operator (`<=>`) to retrieve the top 5 matching text chunks.
   - Concatenates the matches into a **Generated Context Block** and passes it alongside the user's question to `gpt-4o-mini`.
   - Returns the synthesized answer, source matches, cosine similarity percentages, and raw context block back to the React UI.

---

## 🔧 Troubleshooting

<details>
<summary><strong>Error: <code>different vector dimensions 384 and 1536</code></strong></summary>

- **Cause:** `text-embedding-3-small` defaults to 1536 dimensions if `dimensions=384` is omitted.
- **Fix:** Ensure `dimensions=384` is explicitly passed in both `AI_QA_Engine_Project` (ingestion) and `Fast_API_Project` (query embedding) to match `embedding VECTOR(384)`.
</details>

<details>
<summary><strong>Error: <code>Invalid 'input': input cannot be an empty array</code> (400 Bad Request)</strong></summary>

- **Cause:** No valid text files were found in `AI_QA_Engine_Project/data/` or files were empty.
- **Fix:** Confirm non-empty `.txt`, `.md`, or `.csv` files exist in the `data/` folder and verify your relative path resolution using `pathlib`.
</details>

<details>
<summary><strong>Error: Blocked by CORS Policy in Browser Console</strong></summary>

- **Cause:** The frontend (`localhost:5173`) is making requests to a backend port (`8000` or `5000`) without CORS headers enabled.
- **Fix:** Ensure `CORSMiddleware` is configured in `Fast_API_Project/main.py` and `app.use(cors())` is enabled in `Node_Backend_Project/server.js`.
</details>