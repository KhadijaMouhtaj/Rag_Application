"""
Script de lancement des tests d'évaluation RAG
Permet de choisir quel type d'évaluation lancer
"""

import sys
from evaluate_rag import evaluate_rag
from test_questions import (
    BASIC_QUESTIONS,
    EXTENDED_QUESTIONS,
    ADVANCED_QUESTIONS,
    ALL_QUESTIONS,
    print_questions_summary
)

def print_menu():
    """Affiche le menu de sélection"""
    print("\n" + "="*70)
    print("🧪 MENU D'ÉVALUATION RAG")
    print("="*70)
    print("\nChoisissez le type d'évaluation :\n")
    print("  1. Évaluation de base (3 questions)")
    print("  2. Évaluation étendue (8 questions)")
    print("  3. Évaluation avancée (3 questions complexes)")
    print("  4. Évaluation complète (14 questions)")
    print("  5. Afficher les questions disponibles")
    print("  0. Quitter\n")
    print("="*70)

def run_evaluation(questions, test_name):
    """Lance une évaluation avec les questions données"""
    print(f"\n🚀 Lancement: {test_name}")
    print(f"📝 Nombre de questions: {len(questions)}")
    print("-"*70)
    
    results = evaluate_rag(questions=questions, save=True)
    
    if results:
        print(f"\n✅ {test_name} terminée avec succès!")
        return True
    else:
        print(f"\n❌ {test_name} a échoué")
        return False

def main():
    """Fonction principale"""
    
    while True:
        print_menu()
        
        try:
            choice = input("Votre choix (0-5): ").strip()
            
            if choice == "0":
                print("\n👋 Au revoir!")
                sys.exit(0)
            
            elif choice == "1":
                run_evaluation(BASIC_QUESTIONS, "Évaluation de base")
            
            elif choice == "2":
                run_evaluation(EXTENDED_QUESTIONS, "Évaluation étendue")
            
            elif choice == "3":
                run_evaluation(ADVANCED_QUESTIONS, "Évaluation avancée")
            
            elif choice == "4":
                run_evaluation(ALL_QUESTIONS, "Évaluation complète")
            
            elif choice == "5":
                print("\n")
                print_questions_summary()
            
            else:
                print("\n⚠️  Choix invalide. Veuillez entrer un nombre entre 0 et 5.")
            
            # Demander si on veut continuer
            if choice in ["1", "2", "3", "4"]:
                continue_choice = input("\n🔄 Lancer une autre évaluation ? (o/n): ").strip().lower()
                if continue_choice != "o":
                    print("\n👋 Au revoir!")
                    sys.exit(0)
        
        except KeyboardInterrupt:
            print("\n\n👋 Interruption par l'utilisateur. Au revoir!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    print("="*70)
    print("🔬 SYSTÈME D'ÉVALUATION RAG")
    print("="*70)
    print("\n💡 Ce script vous permet de tester votre RAG avec différents")
    print("   niveaux de complexité de questions.\n")
    
    main()