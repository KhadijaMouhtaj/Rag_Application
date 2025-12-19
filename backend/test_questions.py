"""
Questions de test pour l'évaluation du RAG
Organisées par catégorie pour faciliter l'analyse
"""

# Questions de base (3 questions minimales)
BASIC_QUESTIONS = [
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

# Questions étendues (pour une évaluation plus complète)
EXTENDED_QUESTIONS = [
    {
        "question": "Quels sont les avantages de la reconnaissance faciale ?",
        "ground_truth": "Les avantages incluent : identification rapide et sans contact, difficile à falsifier, ne nécessite pas de coopération active de l'utilisateur, peut fonctionner à distance.",
        "category": "avantages"
    },
    {
        "question": "Quelles sont les limites ou défis de la reconnaissance faciale ?",
        "ground_truth": "Les limites incluent : sensibilité aux variations d'éclairage, poses et expressions faciales, problèmes de confidentialité et de vie privée, risque de biais selon l'origine ethnique.",
        "category": "limitations"
    },
    {
        "question": "Quelle est la différence entre vérification et identification en reconnaissance faciale ?",
        "ground_truth": "La vérification compare un visage avec un seul template pour confirmer l'identité (1:1), tandis que l'identification compare un visage avec toute une base de données pour trouver une correspondance (1:N).",
        "category": "concepts"
    },
    {
        "question": "Comment sont extraites les caractéristiques du visage ?",
        "ground_truth": "Les caractéristiques sont extraites via des descripteurs locaux (LBP, HOG) ou des réseaux de neurones profonds (CNN) qui transforment l'image en un vecteur d'embedding capturant les traits distinctifs du visage.",
        "category": "technique"
    },
    {
        "question": "Qu'est-ce que le pooling dans un CNN ?",
        "ground_truth": "Le pooling est une opération qui réduit la taille spatiale des cartes de caractéristiques en conservant les informations les plus importantes, comme le max pooling qui garde la valeur maximale dans chaque région.",
        "category": "technique"
    },
]

# Questions avancées (pour tester des cas complexes)
ADVANCED_QUESTIONS = [
    {
        "question": "Comment les réseaux de neurones convolutifs apprennent-ils à reconnaître les visages ?",
        "ground_truth": "Les CNN apprennent par rétropropagation sur un grand dataset d'images de visages avec leurs identités. Les premières couches détectent des motifs simples (contours, textures), puis les couches profondes combinent ces informations pour reconnaître des structures complexes comme les yeux, le nez, jusqu'à l'identité complète.",
        "category": "apprentissage"
    },
    {
        "question": "Quels sont les métriques utilisées pour évaluer un système de reconnaissance faciale ?",
        "ground_truth": "Les métriques principales incluent : le taux de faux positifs (FAR), le taux de faux négatifs (FRR), la précision (accuracy), le rappel (recall), et la courbe ROC qui montre le compromis entre FAR et FRR.",
        "category": "évaluation"
    },
    {
        "question": "Comment gérer les variations d'éclairage dans la reconnaissance faciale ?",
        "ground_truth": "Les variations d'éclairage sont gérées par des techniques de prétraitement comme la normalisation d'histogramme, l'égalisation adaptative, ou l'utilisation de représentations invariantes à l'illumination. Les CNN modernes apprennent aussi une certaine robustesse à ces variations.",
        "category": "robustesse"
    },
]

# Dataset complet (pour une évaluation exhaustive)
ALL_QUESTIONS = BASIC_QUESTIONS + EXTENDED_QUESTIONS + ADVANCED_QUESTIONS

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_questions_by_category(category):
    """Retourne toutes les questions d'une catégorie donnée"""
    return [q for q in ALL_QUESTIONS if q["category"] == category]

def get_question_categories():
    """Retourne la liste de toutes les catégories"""
    return list(set(q["category"] for q in ALL_QUESTIONS))

def print_questions_summary():
    """Affiche un résumé des questions disponibles"""
    print("📋 Questions de test disponibles:\n")
    print(f"  - BASIC_QUESTIONS: {len(BASIC_QUESTIONS)} questions")
    print(f"  - EXTENDED_QUESTIONS: {len(EXTENDED_QUESTIONS)} questions")
    print(f"  - ADVANCED_QUESTIONS: {len(ADVANCED_QUESTIONS)} questions")
    print(f"  - ALL_QUESTIONS: {len(ALL_QUESTIONS)} questions\n")
    
    categories = get_question_categories()
    print(f"📂 Catégories ({len(categories)}):")
    for cat in sorted(categories):
        count = len(get_questions_by_category(cat))
        print(f"  - {cat}: {count} question(s)")

if __name__ == "__main__":
    print_questions_summary()