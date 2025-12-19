from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import uuid
from groq import Groq
import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from dotenv import load_dotenv

# modèle d'embeddings
#modèle de Sentence Transformers (HuggingFace)
#4️⃣ RETRIEVAL – Récupérer les passages pertinents
embedder = SentenceTransformer("all-MiniLM-L6-v2")
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq()

app = Flask(__name__)
CORS(app)

# ====== STOCKAGE DES SOURCES PDF ======
SOURCES = []

# Initialisation de l'index FAISS global
dimension = 384
index = faiss.IndexFlatL2(dimension)

# ====== VECTOR_DB - Structure améliorée ======
CHUNKS_METADATA = []  # [{source_id, chunk_text, chunk_index}]

def call_llm(prompt: str) -> str:
    """Appel Groq LLM avec le prompt complet."""
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=800,
        temperature=0.3,
    )
    return completion.choices[0].message.content

#Prend une liste d’IDs de sources PDF.Combine le texte complet de toutes ces sources.Renvoie le texte combiné et les noms des sources.

def get_combined_text_from_sources(selected_ids):
    """Récupère le texte combiné de toutes les sources sélectionnées."""
    combined_text = ""
    source_names = []
    
    for s in SOURCES:
        if s["id"] in selected_ids:
            combined_text += s.get("text", "") + "\n\n"
            source_names.append(s["name"])
    
    return combined_text.strip(), source_names

#Divise le texte en morceaux (chunks) de max 300 mots.Essayez de respecter les paragraphes, 
# puis les phrases si un paragraphe est trop long.
# Chaque chunk sera utilisé pour générer un embedding
def smart_chunk_text(text, max_words=300):
    """Divise le texte en chunks intelligents (par paragraphes/phrases)."""
    # Diviser par paragraphes d'abord
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        words = para.split()
        word_count = len(words)
        
        # Si le paragraphe est trop long, le diviser par phrases
        if word_count > max_words:
            sentences = para.replace('!', '.').replace('?', '.').split('.')
            for sent in sentences:
                sent = sent.strip()
                if sent:
                    sent_words = len(sent.split())
                    if current_word_count + sent_words > max_words and current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = [sent]
                        current_word_count = sent_words
                    else:
                        current_chunk.append(sent)
                        current_word_count += sent_words
        else:
            # Ajouter le paragraphe entier
            if current_word_count + word_count > max_words and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [para]
                current_word_count = word_count
            else:
                current_chunk.append(para)
                current_word_count += word_count
    
    # Ajouter le dernier chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


# ---------- 1. UPLOAD PDF ----------
@app.post("/upload_pdf")
def upload_pdf():
    global index, CHUNKS_METADATA
    
    file = request.files.get("file")
    if not file:
        return {"error": "No file provided"}, 400

    try:
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        return {"error": f"Failed to read PDF: {e}"}, 500

    # Utiliser le chunking intelligent
    chunks = smart_chunk_text(text, max_words=300)
    
    if not chunks:
        return {"error": "No text extracted from PDF"}, 400

    # Generate embeddings depuis les chaunks genere du texte des pdfs
    embeddings = embedder.encode(chunks)
#index.add() ajoute ces vecteurs dans l’index FAISS.
    # Add to global FAISS index
    start_idx = len(CHUNKS_METADATA)
    index.add(np.array(embeddings))

    # Store source info
    source_id = str(uuid.uuid4())
    SOURCES.append({
        "id": source_id,
        "name": file.filename,
        "text": text,
        "chunk_count": len(chunks)
    })

    # Store chunk metadata
    for i, chunk in enumerate(chunks):
        CHUNKS_METADATA.append({
            "source_id": source_id,
            "chunk_text": chunk,
            "global_index": start_idx + i
        })

    print(f"✅ PDF uploaded: {file.filename} - {len(chunks)} chunks created")
    return {"id": source_id, "name": file.filename, "chunks": len(chunks)}


# ---------- 2. LIST SOURCES ----------
@app.get("/list_sources")
def list_sources():
    return jsonify([{
        "id": s["id"], 
        "name": s["name"],
        "chunks": s.get("chunk_count", 0)
    } for s in SOURCES])


# ---------- 3. ASK QUESTION (QA) ----------
# ---------- 3. ASK QUESTION (QA) - VERSION CORRIGÉE ----------
@app.post("/ask")
def ask():
    data = request.json or {}
    question = data.get("question", "")
    selected_ids = data.get("selected_ids", [])

    if not question:
        return {"error": "Question is required"}, 400

    if not selected_ids:
        return {"error": "No sources selected"}, 400

    print(f"\n🔍 Question: {question}")
    print(f"📚 Sources sélectionnées: {len(selected_ids)}")

    # Filter chunks from ALL selected sources
    valid_chunks = [
        chunk for chunk in CHUNKS_METADATA 
        if chunk["source_id"] in selected_ids
    ]

    if not valid_chunks:
        print("⚠️  Aucun chunk disponible pour ces sources")
        return {
            "answer": "No content found in selected sources.",
            "chunks": []  # ← IMPORTANT: retourner une liste vide
        }

    print(f"✅ Chunks disponibles: {len(valid_chunks)}")

    # Vectorize the question
    question_embedding = embedder.encode([question])

    # Search in FAISS
    k = min(20, len(valid_chunks))
    distances, neighbors = index.search(question_embedding, k)

    # Retrieve relevant chunks
    retrieved_chunks = []
    for idx, dist in zip(neighbors[0], distances[0]):
        matching_chunks = [
            c for c in valid_chunks 
            if c["global_index"] == idx
        ]
        
        if matching_chunks:
            retrieved_chunks.append(matching_chunks[0]["chunk_text"])
        
        if len(retrieved_chunks) >= 8:
            break

    if not retrieved_chunks:
        print("⚠️  Aucun chunk pertinent trouvé")
        return {
            "answer": "No relevant information found in selected sources.",
            "chunks": []  # ← IMPORTANT: retourner une liste vide
        }

    print(f"📄 Chunks récupérés: {len(retrieved_chunks)}")

    # Build prompt
    context = "\n\n---\n\n".join(retrieved_chunks[:5])
    
    prompt = f"""Tu es un assistant qui répond aux questions en te basant UNIQUEMENT sur le contexte fourni.

CONTEXTE (provenant de toutes les sources sélectionnées) :
{context}

QUESTION :
{question}

INSTRUCTIONS :
- Utilise TOUTES les informations pertinentes du contexte ci-dessus
- Si la réponse se trouve dans plusieurs parties du contexte, synthétise-les
- Si l'information n'est pas dans le contexte, dis-le clairement
- Réponds en français

RÉPONSE :
"""

    # Call LLM
    answer = call_llm(prompt)
    print(f"✅ Réponse générée: {answer[:100]}...\n")
    
    # ← CORRECTION CRITIQUE: Retourner les chunks comme liste de strings
    return {
        "answer": answer,
        "chunks": retrieved_chunks  # Liste de strings, pas de dicts
    }

# ---------- 4. SUMMARY (Résumé) ----------
@app.post("/summarize")
def summarize():
    data = request.json or {}
    selected_ids = data.get("selected_ids", [])

    if not selected_ids:
        return {"error": "No sources selected"}, 400

    print(f"\n📝 Résumé demandé pour {len(selected_ids)} source(s)")

    # Get ALL chunks from selected sources
    selected_chunks = [
        chunk for chunk in CHUNKS_METADATA 
        if chunk["source_id"] in selected_ids
    ]

    if not selected_chunks:
        return {"error": "No content found in selected sources"}, 400

    # Get source names
    source_names = [s["name"] for s in SOURCES if s["id"] in selected_ids]
    print(f"📚 Sources: {', '.join(source_names)}")
    print(f"📦 Total chunks: {len(selected_chunks)}")

    # Prendre un échantillon représentatif de chunks de CHAQUE source
    chunks_per_source = {}
    for chunk in selected_chunks:
        sid = chunk["source_id"]
        if sid not in chunks_per_source:
            chunks_per_source[sid] = []
        chunks_per_source[sid].append(chunk["chunk_text"])

    # Calculer combien de chunks prendre par source pour rester sous la limite
    max_total_chars = 10000
    num_sources = len(chunks_per_source)
    max_chars_per_source = max_total_chars // num_sources
    
    # Construire le texte en prenant des chunks de chaque source
    combined_chunks = []
    
    for sid, chunks in chunks_per_source.items():
        source_name = next(s["name"] for s in SOURCES if s["id"] == sid)
        combined_chunks.append(f"\n=== Document: {source_name} ===\n")
        
        # Ajouter des chunks jusqu'à atteindre la limite par source
        current_chars = 0
        chunks_added = 0
        for chunk in chunks:
            chunk_text = chunk.strip()
            if current_chars + len(chunk_text) < max_chars_per_source:
                combined_chunks.append(chunk_text)
                current_chars += len(chunk_text)
                chunks_added += 1
            else:
                break
        
        print(f"  → {source_name}: {chunks_added} chunks, {current_chars} chars")
    
    combined_text = "\n\n".join(combined_chunks)
    
    print(f"📄 Texte final: {len(combined_text)} caractères")

    prompt = f"""Tu dois résumer le contenu suivant qui provient de {len(source_names)} document(s) : {', '.join(source_names)}

CONTENU À RÉSUMER :
{combined_text}

INSTRUCTIONS :
- Fais un résumé complet et structuré qui couvre TOUS les documents mentionnés
- Pour chaque document, résume ses points principaux
- Organise le résumé par document ou par thème
- Mentionne explicitement le nom de chaque document dans ton résumé
- Si les documents traitent de sujets similaires, compare-les

RÉSUMÉ :
"""

    answer = call_llm(prompt)
    print(f"✅ Résumé généré\n")
    return {"result": answer}


# ---------- 5. QUIZ (QCM) ----------
@app.post("/quiz")
def quiz():
    data = request.json or {}
    selected_ids = data.get("selected_ids", [])

    if not selected_ids:
        return {"error": "No sources selected"}, 400

    print(f"\n🎯 Quiz demandé pour {len(selected_ids)} source(s)")

    # Get ALL chunks from selected sources
    selected_chunks = [
        chunk for chunk in CHUNKS_METADATA 
        if chunk["source_id"] in selected_ids
    ]

    if not selected_chunks:
        return {"error": "No content found in selected sources"}, 400

    # Get source names
    source_names = [s["name"] for s in SOURCES if s["id"] in selected_ids]
    print(f"📚 Sources: {', '.join(source_names)}")
    print(f"📦 Total chunks: {len(selected_chunks)}")

    # Prendre des chunks de CHAQUE source pour le quiz
    chunks_per_source = {}
    for chunk in selected_chunks:
        sid = chunk["source_id"]
        if sid not in chunks_per_source:
            chunks_per_source[sid] = []
        chunks_per_source[sid].append(chunk["chunk_text"])

    # Calculer combien de chunks prendre par source
    max_total_chars = 12000  # Augmenté pour avoir plus de contexte
    num_sources = len(chunks_per_source)
    max_chars_per_source = max_total_chars // num_sources
    
    # Construire le texte en incluant des chunks de chaque source
    combined_chunks = []
    
    for sid, chunks in chunks_per_source.items():
        source_name = next(s["name"] for s in SOURCES if s["id"] == sid)
        combined_chunks.append(f"\n{'='*60}")
        combined_chunks.append(f"DOCUMENT SOURCE: {source_name}")
        combined_chunks.append(f"{'='*60}\n")
        
        # Ajouter des chunks jusqu'à atteindre la limite par source
        current_chars = 0
        chunks_added = 0
        for chunk in chunks:
            chunk_text = chunk.strip()
            if current_chars + len(chunk_text) < max_chars_per_source:
                combined_chunks.append(f"[Section {chunks_added + 1}]")
                combined_chunks.append(chunk_text)
                combined_chunks.append("")  # Ligne vide pour séparation
                current_chars += len(chunk_text)
                chunks_added += 1
            else:
                break
        
        print(f"  → {source_name}: {chunks_added} chunks, {current_chars} chars")
    
    combined_text = "\n\n".join(combined_chunks)
    
    print(f"📄 Texte final: {len(combined_text)} caractères")

    # Calculer le nombre de questions par source
    questions_per_source = max(1, 5 // len(source_names))
    total_questions = questions_per_source * len(source_names)
    
    prompt = f"""Tu es un expert en création de quiz. Tu dois créer un QCM basé STRICTEMENT sur le contenu suivant.

RÈGLES ABSOLUES :
1. Les questions et réponses doivent venir DIRECTEMENT du texte fourni
2. Ne PAS inventer d'informations
3. Vérifie que chaque réponse correcte correspond exactement à une information du texte
4. Les mauvaises réponses doivent être plausibles mais clairement incorrectes

CONTENU SOURCE ({len(source_names)} document(s) : {', '.join(source_names)}) :
{combined_text}

INSTRUCTIONS DE GÉNÉRATION :
- Génère exactement {total_questions} questions QCM
- Répartis les questions équitablement entre tous les documents
- Pour chaque question :
  * Cite le document source
  * Pose une question claire basée sur une information factuelle du texte
  * Propose 4 options (A, B, C, D)
  * UNE SEULE réponse correcte qui correspond EXACTEMENT au texte
  * 3 réponses incorrectes mais plausibles
  * Indique la lettre de la bonne réponse (A, B, C ou D)

EXEMPLE DE FORMAT :
1. [Document: exemple.pdf] - Quelle est la définition de X selon le document ?
   A) Première définition incorrecte
   B) Définition correcte tirée du texte
   C) Deuxième définition incorrecte
   D) Troisième définition incorrecte
   Réponse correcte : B

GÉNÈRE LE QUIZ MAINTENANT (respecte strictement le format ci-dessus) :
"""

    print("🤖 Génération du quiz...")
    
    # Augmenter max_tokens pour avoir un quiz complet
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=1500,  # Plus de tokens pour le quiz
        temperature=0.3,  # Un peu de créativité pour les mauvaises réponses
    )
    answer = completion.choices[0].message.content
    
    print(f"✅ Quiz généré avec questions sur tous les documents\n")

    return {"result": answer}

@app.post("/transcribe")
def transcribe():
    if "file" not in request.files:
        return {"error": "No audio file provided"}, 400

    audio_file = request.files["file"]

    # On sauvegarde temporairement (Groq requiert un fichier)
    temp_path = "temp_audio.webm"
    audio_file.save(temp_path)

    try:
        # Appel Whisper Groq
        transcript = client.audio.transcriptions.create(
            file=open(temp_path, "rb"),
            model="whisper-large-v3",
            response_format="json"
        )

        # 🔥 Ici la vraie correction
        text = transcript.text.strip()

        return {"text": text}

    except Exception as e:
        return {"error": str(e)}, 500



if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=True)