# 🤖 Advanced Retrieval-Augmented Generation (RAG) System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Backend-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq--LLaMA--3.3-orange.svg)](https://groq.com/)
[![FAISS](https://img.shields.io/badge/VectorDB-FAISS-green.svg)](https://github.com/facebookresearch/faiss)

## 📌 Project Overview
This repository contains a full-stack **Retrieval-Augmented Generation (RAG)** application designed to provide grounded, hallucination-free answers based on user-provided documents. The system supports dynamic PDF ingestion, audio transcription, and automated evaluation.

---

## 🖼️ Graphical Abstract (Pipeline Pipeline)

The following diagram illustrates the end-to-end data flow, from document ingestion to LLM generation and RAGAS evaluation.

<img width="689" height="205" alt="image" src="https://github.com/user-attachments/assets/7c7a44ce-5fd7-4ed4-aa95-52edab18a1d5" />


```mermaid
graph TD
    A[User Input: PDF / Audio] --> B{Backend Processing}
    B -->|pdfplumber| C[Text Extraction]
    B -->|Whisper-v3| D[Audio Transcription]
    C --> E[Smart Semantic Chunking]
    D --> E
    E --> F[Sentence Transformers: all-MiniLM-L6-v2]
    F --> G[(FAISS Vector Database)]
    H[User Question] --> I[Query Embedding]
    I --> J[Top-k Similarity Search]
    J --> K[Context Retrieval]
    K --> L[Prompt Construction & Grounding]
    L --> M[Groq: LLaMA 3.3 70B]
    M --> N[Final Answer]
    N --> O[RAGAS Evaluation: Faithfulness/Relevancy]
