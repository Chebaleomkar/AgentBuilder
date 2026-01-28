# RAG & Grounding System

AgentBuilder implements a high-fidelity Retrieval-Augmented Generation (RAG) system designed for enterprise SOPs and internal documentation.

---

## 🏗️ Architecture

The RAG pipeline follows a structured three-stage process:

1. **Indexing**: 
    - Text is extracted from uploads (PDF, DOCX, TXT).
    - Documents are chunked into semantic "Atoms".
    - Embeddings are generated using **Google Gemini `text-embedding-004`**.
    - Vectors are stored in **Pinecone** with namespace isolation per Agent.

2. **Retrieval**:
    - Queries are embedded with the same Gemini model.
    - Pinecone performs a similarity search within the agent's dedicated namespace.
    - Matches are filtered by a calibrated similarity threshold (default: `0.35`).

3. **Grounded Generation**:
    - Retrieved "Knowledge Atoms" are injected into the LLM context.
    - The LLM is forced to follow **Strict Grounding** instructions.
    - Citations are automatically requested for every fact sourced from the knowledge base.

---

## 🛡️ Strict Grounding Instructions

Every agent equipped with the `rag_search` tool is primed with a core directive:

> **IMPORTANT INSTRUCTION ON GROUNDING:**
> You have access to a verified KNOWLEDGE BASE. If the user asks about specific company policies, procedures, or internal documents:
> 1. You MUST first use the `rag_search` tool to find relevant "Knowledge Atoms".
> 2. If relevant atoms are found, provide an answer based **ONLY** on those atoms.
> 3. You MUST cite your source using the source name provided (e.g., [According to Source X...]).
> 4. If the information is NOT in the knowledge base, you MUST clearly state: *"No relevant information was found in the internal knowledge base regarding [subject]."*
> 5. **DO NOT** use your general pre-trained knowledge to answer specific policy questions if the context is missing.

---

## 🎨 Visualization in Playground

The AgentBuilder Playground (Prompt Studio) provides deep visibility into the RAG process:

- **Knowledge Atoms Viewer**: A horizontal scrollbar above the results shows the raw chunks retrieved from the database.
- **Confidence Scores**: Each atom displays a percentage score representing its vector similarity to the user's query.
- **Source Indicators**: Every chunk is labeled with its original document name (e.g., "Employee Handbook.pdf").

---

## ⚙️ Configuration (Environment)

To enable RAG, the following variables must be configured in `.env`:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Used for generating 768-dim embeddings. |
| `PINECONE_API_KEY` | Authentication for the vector database. |
| `PINECONE_INDEX_NAME` | The target index (must support 768 dimensions). |
| `PINECONE_ENVIRONMENT` | e.g., `gcp-starter`. |

---

## 🛠️ Calibration

The similarity threshold in `app/services/rag_service.py` is currently calibrated to **0.35**. 
- **Higher (0.5+)**: More precise, but may miss relevant information in conversational queries.
- **Lower (0.2 - 0.3)**: Highly inclusive, but may introduce noise if the query is vague.

We recommend **0.35 - 0.40** for most SOP-based assistants.
