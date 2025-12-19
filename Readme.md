# 🤖 Système RAG Dynamique (Retrieval-Augmented Generation)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Backend-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq--LLaMA--3.3-orange.svg)](https://groq.com/)
[![FAISS](https://img.shields.io/badge/VectorDB-FAISS-green.svg)](https://github.com/facebookresearch/faiss)

Ce projet implémente un système de **Génération Augmentée par Récupération (RAG)** complet. Il permet d'uploader des PDF ou des fichiers audio, de les indexer en temps réel et d'interroger un LLM (Llama 3.3 via Groq) en garantissant que les réponses sont basées exclusivement sur vos documents.

---

## 🧠 Architecture du Système

Le système transforme les documents en connaissances via ce pipeline :



1.  **Ingestion & Extraction** : Lecture des PDF via `pdfplumber` ou transcription audio via `Whisper-large-v3`.
2.  **Smart Chunking** : Découpage intelligent du texte en segments de ~300 mots pour optimiser la pertinence.
3.  **Vectorisation** : Création d'embeddings de 384 dimensions avec `SentenceTransformer` (`all-MiniLM-L6-v2`).
4.  **Stockage & Retrieval** : Recherche de similarité vectorielle ultra-rapide avec **FAISS**.
5.  **Génération** : Inférence sur **Groq** avec un prompt structuré pour éviter les hallucinations.
6.  **Évaluation** : Suite de tests automatisée utilisant les métriques **RAGAS**.

---

## 📂 Structure du Projet

```text
rag_project/
├── backend/
│   ├── app.py              # Serveur Flask principal (Logique RAG)
│   ├── evaluate_rag.py     # Script d'évaluation RAGAS
│   ├── run_tests.py        # Interface CLI pour lancer les tests
│   ├── test_questions.py   # Banques de questions (Basic, Extended, Advanced)
│   ├── vectorstore/        # Index FAISS persistant (index.faiss, index.pkl)
│   ├── evaluation_results/ # Rapports de performance générés
│   ├── requirements.txt    # Liste des dépendances Python
│   └── .env                # Clé API Groq (Fichier masqué)
└── frontend/               # Interface utilisateur React

## 🖼️ Graphical Abstract (Pipeline Pipeline)

The following diagram illustrates the end-to-end data flow, from document ingestion to LLM generation and RAGAS evaluation.

<img width="689" height="205" alt="image" src="https://github.com/user-attachments/assets/7c7a44ce-5fd7-4ed4-aa95-52edab18a1d5" />


RAGAS Evaluation: Faithfulness/Relevancy]

