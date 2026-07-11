# MedPath-RAG

## Project Description

MedPath-RAG is an AI-powered Medical Information Assistant designed to provide evidence-based information on **Diabetes** and **Cancer Pathology** using **Retrieval-Augmented Generation (RAG)** and **MedGemma**.

The application combines trusted medical knowledge from organizations such as the World Health Organization (WHO), American Diabetes Association (ADA), National Cancer Institute (NCI), and PubMed with modern AI technologies to deliver accurate, context-aware responses.

Instead of relying solely on a Large Language Model, the system first retrieves relevant medical information from a curated medical knowledge base using semantic search powered by BioBERT embeddings and the FAISS vector database. The retrieved context is then provided to MedGemma, which generates a medically relevant response with supporting evidence.

The project currently focuses on the following diseases:

### Diabetes

* Type 1 Diabetes
* Type 2 Diabetes
* Gestational Diabetes

### Cancer

* Leukemia
* Melanoma
* Lung Cancer

The primary objective is to build a reliable AI assistant that can support medical education by answering pathology-related questions based on trusted medical literature.

---

# Project Objectives

* Develop an AI-powered medical information assistant.
* Implement a Retrieval-Augmented Generation (RAG) pipeline.
* Use MedGemma for medical response generation.
* Retrieve information from trusted medical sources.
* Reduce AI hallucinations by grounding responses in retrieved evidence.
* Display source references for every generated answer.
* Provide an easy-to-use web interface for users.
* Maintain logs and analytics using Google Sheets.

---

# Development Guidelines

## 1. Coding Standards

* Follow modular programming principles.
* Write reusable and maintainable code.
* Use meaningful variable and function names.
* Keep functions focused on a single responsibility.
* Add comments where necessary.
* Follow PEP 8 coding standards for Python.

---

## 2. Project Structure

Each team member must work only within their assigned module.

Do not modify another member's module unless it is required for integration.

---

## 3. GitHub Workflow

* Never commit directly to the `main` branch.
* Create a feature branch for every module.
* Commit changes with meaningful commit messages.
* Push changes to your feature branch.
* Create a Pull Request.
* Merge only after code review.

---

## 4. Data Collection Guidelines

Collect medical information only from trusted sources:

* World Health Organization (WHO)
* American Diabetes Association (ADA)
* National Cancer Institute (NCI)
* PubMed
* NCBI Bookshelf
* Peer-reviewed Medical Journals
* Standard Pathology Textbooks

Avoid using:

* Blogs
* Wikipedia as the primary source
* Quora
* Reddit
* AI-generated medical content without verification

---

## 5. Data Processing Guidelines

* Preserve original PDF files.
* Clean extracted text before chunking.
* Remove duplicate content.
* Maintain document metadata.
* Generate consistent text chunks for embedding.

---

## 6. Embedding Guidelines

* Use BioBERT for embedding generation.
* Generate embeddings only after text cleaning.
* Validate embeddings before storing them in FAISS.

---

## 7. Retrieval Guidelines

* Store embeddings using FAISS.
* Retrieve the Top-5 most relevant chunks.
* Provide retrieved context to MedGemma.
* Do not generate responses without retrieved evidence.

---

## 8. Response Guidelines

Every response should:

* Be medically relevant.
* Be based on retrieved context.
* Avoid unsupported claims.
* Include the source of information whenever possible.

If sufficient evidence is unavailable, the system should indicate that it cannot answer confidently rather than guessing.

---

## 9. Security Guidelines

* Store secrets using environment variables (`.env`).
* Validate all user inputs.
* Use JWT for authentication (if login is implemented).
* Never expose API keys or credentials in the repository.
* Protect sensitive configuration files using `.gitignore`.

---

## 10. Testing Guidelines

Each module must be tested independently before integration.

Testing should include:

* PDF extraction
* Text cleaning
* Chunk generation
* Embedding generation
* FAISS retrieval
* MedGemma response generation
* FastAPI endpoints
* Streamlit interface

---

## 11. Documentation Guidelines

Every module should include:

* Purpose
* Input
* Output
* Dependencies
* Usage instructions

The repository should always contain updated documentation, architecture diagrams, and installation instructions.

---

# Project Workflow

```
Medical Documents
       ↓
PDF Extraction
       ↓
Text Cleaning
       ↓
Chunk Generation
       ↓
BioBERT Embeddings
       ↓
FAISS Vector Database
       ↓
User Query
       ↓
Semantic Retrieval (Top-5)
       ↓
Prompt Construction
       ↓
MedGemma
       ↓
Evidence-Based Medical Response
       ↓
Source Citations
       ↓
Streamlit Web Application
       ↓
Google Sheets Logging
```

---

# Expected Outcome

The completed system will function as an AI-powered Medical Information Assistant capable of answering questions related to Diabetes and Cancer Pathology using trusted medical literature and Retrieval-Augmented Generation, while providing reliable, evidence-based responses with supporting references.
