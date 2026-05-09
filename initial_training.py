"""
Script Initial Training - Addestramento iniziale modello ML

Usage:
    python initial_training.py [--limit N] [--tipos TIPO1,TIPO2]

Esempi:
    python initial_training.py                    # Tutti i documenti
    python initial_training.py --limit 100        # Solo primi 100
    python initial_training.py --tipos F24,CED    # Solo F24 e Cedolini
"""
import sys
import os
import argparse
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')

import django
django.setup()

from django.db.models import Q, Count
from documenti.models import Documento, DocumentiTipo
from ai_classifier.services.ml.model_trainer import ModelTrainer


def main():
    parser = argparse.ArgumentParser(
        description="Training iniziale modello ML per classificazione documenti"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limita numero documenti (per test rapidi)'
    )
    parser.add_argument(
        '--tipos',
        type=str,
        default=None,
        help='Filtra per tipi documento (es: F24,CED,UNILAV)'
    )
    parser.add_argument(
        '--min-docs-per-type',
        type=int,
        default=5,
        help='Minimo documenti per tipo (default: 5)'
    )
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Auto-conferma senza chiedere (per esecuzione non-interattiva)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 INITIAL TRAINING - Sistema ML Auto-Apprendimento")
    print("=" * 70)
    print()
    
    # Query documenti
    print("📂 Caricamento documenti...")
    
    queryset = Documento.objects.filter(
        file__isnull=False
    ).exclude(
        file=''
    ).select_related('tipo', 'cliente', 'titolario_voce')
    
    # Filtra per tipo se specificato
    if args.tipos:
        tipo_codici = [t.strip() for t in args.tipos.split(',')]
        queryset = queryset.filter(tipo__codice__in=tipo_codici)
        print(f"   🔍 Filtro tipi: {', '.join(tipo_codici)}")
    
    # Limita se specificato (prima di filtrare per tipo count)
    if args.limit:
        queryset = queryset[:args.limit]
        print(f"   ⚡ Limit: {args.limit} documenti")
    
    # Carica tutti i documenti
    all_documents = list(queryset)
    
    # Filtra tipi con pochi documenti (post-caricamento)
    tipo_distribution_temp = {}
    for doc in all_documents:
        tipo = doc.tipo.codice if doc.tipo else 'UNK'
        tipo_distribution_temp[tipo] = tipo_distribution_temp.get(tipo, 0) + 1
    
    # Filtra documenti di tipi con almeno min_docs_per_type
    valid_tipos = [t for t, count in tipo_distribution_temp.items() if count >= args.min_docs_per_type]
    documents = [doc for doc in all_documents if (doc.tipo.codice if doc.tipo else 'UNK') in valid_tipos]
    
    if len(documents) != len(all_documents):
        removed = len(all_documents) - len(documents)
        print(f"   ⚠️  Rimossi {removed} documenti di tipi con < {args.min_docs_per_type} esempi")
    
    if not documents:
        print("❌ Nessun documento trovato!")
        return 1
    
    print(f"   ✅ Trovati {len(documents)} documenti")
    print()
    
    # Mostra distribuzione per tipo
    print("📊 DISTRIBUZIONE PER TIPO:")
    print("-" * 70)
    tipo_distribution = {}
    for doc in documents:
        tipo = doc.tipo.codice if doc.tipo else 'UNK'
        tipo_distribution[tipo] = tipo_distribution.get(tipo, 0) + 1
    
    for tipo, count in sorted(tipo_distribution.items(), key=lambda x: -x[1]):
        bar = "█" * min(count // 2, 50)
        print(f"  {tipo:12s} : {count:4d} doc  {bar}")
    print()
    
    # Conferma
    print("⚠️  ATTENZIONE: Il training può richiedere diversi minuti.")
    print("   Verranno elaborati:")
    print(f"   - {len(documents)} documenti")
    print(f"   - {len(tipo_distribution)} tipi documento")
    print()
    
    if not args.yes:
        risposta = input("Procedere? [s/N]: ")
        if risposta.lower() not in ['s', 'si', 'sì', 'y', 'yes']:
            print("❌ Training annullato")
            return 0
    else:
        print("✅ Auto-confermato (--yes flag)")
    
    print()
    print("=" * 70)
    
    # Inizializza trainer
    trainer = ModelTrainer(
        model_type='random_forest',
        test_size=0.2,
        use_smote=True,
    )
    
    # Training
    try:
        ml_model = trainer.train_initial_model(
            documents=documents,
            version=None,  # Auto-genera
        )
        
        print()
        print("=" * 70)
        print("✅ TRAINING COMPLETATO CON SUCCESSO!")
        print("=" * 70)
        print()
        print("📊 RISULTATI:")
        print(f"   Versione modello: {ml_model.version}")
        print(f"   Accuracy:         {ml_model.accuracy:.2%}")
        print(f"   Precision:        {ml_model.precision:.2%}")
        print(f"   Recall:           {ml_model.recall:.2%}")
        print(f"   F1-Score:         {ml_model.f1_score:.2%}")
        print(f"   Campioni training: {ml_model.training_samples}")
        print()
        print("💾 FILES SALVATI:")
        print(f"   Modello:     {ml_model.model_file_path}")
        print(f"   Vectorizer:  {ml_model.vectorizer_file_path}")
        print(f"   Encoders:    {ml_model.label_encoder_file_path}")
        print()
        print("🎯 PROSSIMI PASSI:")
        print("   1. Attiva il modello:")
        print(f"      python manage.py shell -c \"from ai_classifier.models import MLModel; MLModel.objects.get(id={ml_model.id}).activate()\"")
        print()
        print("   2. Testa una predizione:")
        print("      (Da implementare con Predictor Service)")
        print()
        
        return 0
    
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERRORE DURANTE IL TRAINING")
        print("=" * 70)
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
