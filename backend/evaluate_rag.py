"""
Script d'évaluation RAG avec RAGAS
Mesure la qualité des réponses générées par le système RAG
"""

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_correctness
from openai import OpenAI
from ragas.llms import llm_factory
import requests
import os
import json
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = "http://localhost:5000/ask"
RESULTS_DIR = "evaluation_results"

# Clé API OpenAI (pour l'évaluateur RAGAS)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ============================================================================
# QUESTIONS DE TEST
# ============================================================================

TEST_QUESTIONS = [
    {
        "question": "Qu'est-ce que la reconnaissance faciale ?",
        "ground_truth": "La reconnaissance faciale est une technologie biométrique qui permet d'identifier ou de vérifier l'identité d'une personne à partir des caractéristiques de son visage.",
        "category": "définition"
    },
    {
        "question": "Comment fonctionne un algorithme CNN dans la reconnaissance faciale ?",
        "ground_truth": "Un CNN fonctionne en appliquant des couches de convolution pour extraire des caractéristiques hiérarchiques du visage, suivies de couches de pooling pour réduire la dimensionnalité, et enfin des couches fully connected pour la classification.",
        "category": "technique"
    },
    {
        "question": "Quelles sont les étapes principales d'un système biométrique de reconnaissance faciale ?",
        "ground_truth": "Les étapes principales sont : acquisition de l'image, prétraitement et normalisation, détection et alignement du visage, extraction des caractéristiques, et comparaison/matching avec la base de données.",
        "category": "processus"
    },
]

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def create_results_directory():
    """Crée le dossier pour stocker les résultats d'évaluation"""
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        print(f"📁 Dossier créé: {RESULTS_DIR}/")

def save_results(results_dict, filename=None):
    """Sauvegarde les résultats dans un fichier JSON"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_{timestamp}.json"
    
    filepath = os.path.join(RESULTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Résultats sauvegardés: {filepath}")

def get_sources():
    """Récupère la liste des sources PDF uploadées"""
    print("📚 Récupération des sources disponibles...")
    try:
        sources_list = requests.get("http://localhost:5000/list_sources").json()
        selected_sources = [s["id"] for s in sources_list]
        
        print(f"✓ {len(selected_sources)} source(s) trouvée(s)")
        for s in sources_list:
            print(f"  - {s['name']}: {s['chunks']} chunks")
        
        if not selected_sources:
            print("⚠️  ATTENTION: Aucune source disponible!")
            print("   Uploadez des PDFs via l'interface avant d'évaluer.")
            return None
        
        return selected_sources
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des sources: {e}")
        print("   Vérifiez que le serveur Flask est démarré (python app.py)")
        return None

def ask_rag(question, selected_sources):
    """Interroge le système RAG et récupère la réponse + contexte"""
    payload = {"question": question, "selected_ids": selected_sources}
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"  ❌ Erreur HTTP {response.status_code}")
            return None, []
        
        data = response.json()
        answer = data.get("answer", "")
        chunks = data.get("chunks", [])
        
        if not chunks:
            chunks = ["Aucun contexte trouvé"]
        
        return answer, chunks
    
    except requests.exceptions.Timeout:
        print(f"  ⏱️  Timeout - La requête a pris trop de temps")
        return None, []
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return None, []

# ============================================================================
# ÉVALUATION PRINCIPALE
# ============================================================================

def evaluate_rag(questions=None, save=True):
    """
    Évalue le système RAG avec RAGAS
    
    Args:
        questions: Liste de questions à tester (utilise TEST_QUESTIONS par défaut)
        save: Si True, sauvegarde les résultats dans un fichier
    """
    
    if questions is None:
        questions = TEST_QUESTIONS
    
    # Créer le dossier de résultats
    if save:
        create_results_directory()
    
    # Récupérer les sources
    selected_sources = get_sources()
    if not selected_sources:
        return None
    
    # Préparer les listes pour le dataset
    test_questions = []
    ground_truths = []
    answers = []
    contexts = []
    categories = []
    
    # Interroger le RAG pour chaque question
    print(f"\n🔄 Interrogation du RAG ({len(questions)} questions)...")
    print("=" * 70)
    
    for i, item in enumerate(questions, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]
        category = item.get("category", "général")
        
        print(f"\n📝 Question {i}/{len(questions)}")
        print(f"   Catégorie: {category}")
        print(f"   Q: {question[:70]}...")
        
        answer, chunks = ask_rag(question, selected_sources)
        
        if answer is None:
            print(f"   ❌ Échec - Question ignorée")
            continue
        
        test_questions.append(question)
        ground_truths.append(ground_truth)
        answers.append(answer)
        contexts.append(chunks)
        categories.append(category)
        
        print(f"   ✓ Réponse: {answer[:80]}...")
        print(f"   ✓ Contexte: {len(chunks)} chunk(s)")
    
    if not test_questions:
        print("\n❌ Aucune question n'a pu être traitée")
        return None
    
    # Créer le dataset RAGAS
    print("\n📊 Préparation du dataset RAGAS...")
    dataset = Dataset.from_dict({
        "question": test_questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
    print(f"✓ Dataset créé: {len(dataset)} exemples validés")
    
    # Configuration du modèle d'évaluation
    print("\n🤖 Configuration du modèle d'évaluation...")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    evaluator_llm = llm_factory(
        "gpt-4o-mini",
        client=openai_client,
        temperature=0,
        max_tokens=4096
    )
    
    # Lancement de l'évaluation
    print("\n🔬 Lancement de l'évaluation RAGAS...")
    print("Métrique principale:")
    print("  - faithfulness: Fidélité au contexte (0-1)")
    print("    → Mesure si le RAG génère des hallucinations")
    print("    → C'est LA métrique critique pour la production")
    print("\n💡 Note: answer_correctness désactivée (problèmes d'embeddings)")
    print("⏳ Patientez, cela peut prendre quelques minutes...\n")
    
    try:
        results = evaluate(
            dataset,
            metrics=[
                faithfulness,  # Seule métrique fiable
            ],
            llm=evaluator_llm,
        )
        
        # Affichage des résultats
        print("\n" + "=" * 70)
        print("📈 RÉSULTATS DE L'ÉVALUATION RAGAS")
        print("=" * 70)
        
        if hasattr(results, 'to_pandas'):
            df = results.to_pandas()
            
            # Scores moyens
            print("\n📊 SCORES MOYENS PAR MÉTRIQUE")
            print("-" * 70)
            
            results_dict = {
                "timestamp": datetime.now().isoformat(),
                "total_questions": len(dataset),
                "metrics": {},
                "questions": []
            }
            
            for metric in ['faithfulness']:
                if metric in df.columns:
                    score = df[metric].mean()
                    emoji = "🟢" if score > 0.7 else "🟡" if score > 0.5 else "🔴"
                    
                    print(f"\n{emoji} {metric.upper()}")
                    print(f"   Score: {score:.4f} ({score*100:.2f}%)")
                    
                    if score > 0.8:
                        interpretation = "Excellent ! Pas d'hallucinations"
                        print(f"   → {interpretation}")
                        print(f"   → Le RAG reste fidèle aux documents sources")
                    elif score > 0.6:
                        interpretation = "Bon. Quelques déviations mineures"
                        print(f"   → {interpretation}")
                        print(f"   → Le modèle s'éloigne parfois légèrement du contexte")
                    else:
                        interpretation = "À améliorer. Le modèle invente des infos"
                        print(f"   → {interpretation}")
                        print(f"   → Risque d'hallucinations élevé")
                    
                    results_dict["metrics"][metric] = {
                        "score": float(score),
                        "interpretation": interpretation
                    }
            
            # Détails par question
            print("\n📋 DÉTAILS PAR QUESTION")
            print("-" * 70)
            
            for idx, row in df.iterrows():
                print(f"\n❓ Question {idx + 1}: {test_questions[idx][:60]}...")
                print(f"   Catégorie: {categories[idx]}")
                
                question_results = {
                    "question": test_questions[idx],
                    "category": categories[idx],
                    "answer": answers[idx][:200] + "...",
                    "scores": {}
                }
                
                if 'faithfulness' in row:
                    score = row['faithfulness']
                    emoji = "🟢" if score > 0.7 else "🟡" if score > 0.5 else "🔴"
                    print(f"   {emoji} Faithfulness: {score:.4f}")
                    question_results["scores"]["faithfulness"] = float(score)
                
                results_dict["questions"].append(question_results)
            
            # Analyse finale
            print("\n" + "=" * 70)
            print("💡 ANALYSE FINALE")
            print("=" * 70)
            
            faith_mean = df['faithfulness'].mean() if 'faithfulness' in df.columns else 0
            
            print(f"\n🎯 Fidélité au contexte (Faithfulness) : {faith_mean:.2%}")
            
            # Verdict basé uniquement sur faithfulness
            if faith_mean > 0.9:
                final_verdict = "EXCELLENT RAG - Prêt pour la production !"
                print(f"\n🌟 {final_verdict}")
                print("   ✓ Fidélité exceptionnelle au contexte")
                print("   ✓ Pas d'hallucinations détectées")
                print("   ✓ Le système peut être déployé en confiance")
            elif faith_mean > 0.8:
                final_verdict = "TRÈS BON RAG - Quasi production-ready"
                print(f"\n🟢 {final_verdict}")
                print("   ✓ Très bonne fidélité au contexte")
                print("   ✓ Hallucinations très rares")
                print("   → Quelques tests supplémentaires recommandés")
            elif faith_mean > 0.7:
                final_verdict = "BON RAG - Optimisations recommandées"
                print(f"\n✅ {final_verdict}")
                print("   ✓ Bonne fidélité générale au contexte")
                print("   ⚠️  Quelques déviations occasionnelles")
                print("   → Améliorer le prompt pour renforcer la fidélité")
            else:
                final_verdict = "RAG À AMÉLIORER - Risque d'hallucinations"
                print(f"\n⚠️  {final_verdict}")
                print("   ❌ Fidélité insuffisante au contexte")
                print("   ❌ Risque d'hallucinations trop élevé")
                print("   → Actions urgentes :")
                print("      1. Revoir le prompt système")
                print("      2. Améliorer la qualité du retrieval")
                print("      3. Augmenter k (nombre de chunks)")
                print("      4. Utiliser un modèle LLM plus puissant")
            
            results_dict["final_verdict"] = final_verdict
            results_dict["recommendations"] = []
            
            # Recommandations spécifiques par question
            print("\n📝 RECOMMANDATIONS PAR QUESTION:")
            problematic_questions = [
                (idx, categories[idx], row['faithfulness']) 
                for idx, row in df.iterrows() 
                if 'faithfulness' in row and row['faithfulness'] < 0.8
            ]
            
            if problematic_questions:
                print("   Questions avec score < 0.8 :")
                for idx, cat, score in problematic_questions:
                    print(f"   • Q{idx+1} ({cat}): {score:.2%} - À améliorer")
                    results_dict["recommendations"].append({
                        "question_id": idx + 1,
                        "category": cat,
                        "score": float(score),
                        "issue": "Fidélité insuffisante"
                    })
            else:
                print("   ✓ Toutes les questions ont un score > 0.8")
                print("   ✓ Pas de recommandations spécifiques")
            
            # Score moyen par catégorie
            print("\n📊 SCORES PAR CATÉGORIE:")
            category_scores = {}
            for idx, row in df.iterrows():
                cat = categories[idx]
                if cat not in category_scores:
                    category_scores[cat] = []
                if 'faithfulness' in row:
                    category_scores[cat].append(row['faithfulness'])
            
            for cat, scores in sorted(category_scores.items()):
                avg = sum(scores) / len(scores)
                emoji = "🟢" if avg > 0.8 else "🟡" if avg > 0.6 else "🔴"
                print(f"   {emoji} {cat:<20}: {avg:.2%} ({len(scores)} question(s))")
            
            results_dict["category_scores"] = {
                cat: float(sum(scores) / len(scores)) 
                for cat, scores in category_scores.items()
            }
            
            # Sauvegarder les résultats
            if save:
                save_results(results_dict)
            
            print("\n" + "=" * 70)
            print("✅ ÉVALUATION TERMINÉE")
            print("=" * 70)
            
            return results_dict
        
    except Exception as e:
        print(f"\n❌ Erreur pendant l'évaluation: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🔬 ÉVALUATION RAG AVEC RAGAS")
    print("=" * 70)
    
    results = evaluate_rag()
    
    if results:
        print(f"\n📊 Résultats disponibles dans le dossier: {RESULTS_DIR}/")