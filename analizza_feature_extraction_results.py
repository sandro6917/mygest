#!/usr/bin/env python
"""
Script per analizzare i risultati REALI del feature extraction
dall'ultima sessione di training.

Carica il vectorizer e mostra:
- Vocabulary completo (500 parole)
- Feature names
- Statistiche TF-IDF
- Esempi di trasformazione su documenti reali
"""

import os
import sys
import pickle
import django
import numpy as np
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import Documento
from ai_classifier.services.ml.feature_extractor import FeatureExtractor


def load_latest_vectorizer():
    """Carica l'ultimo vectorizer dal training."""
    ml_models_dir = Path(__file__).parent / 'ml_models'
    
    # Trova l'ultimo vectorizer
    vectorizer_files = sorted(ml_models_dir.glob('vectorizer_*.pkl'), reverse=True)
    
    if not vectorizer_files:
        print("❌ Nessun vectorizer trovato!")
        return None
    
    latest_vectorizer = vectorizer_files[0]
    print(f"📦 Caricamento vectorizer: {latest_vectorizer.name}")
    
    with open(latest_vectorizer, 'rb') as f:
        vectorizer = pickle.load(f)
    
    return vectorizer, latest_vectorizer.name


def analyze_vocabulary(vectorizer):
    """Analizza il vocabulary del TF-IDF vectorizer."""
    print("\n" + "="*80)
    print("📚 VOCABULARY TF-IDF (Top 500 parole)")
    print("="*80)
    
    if not hasattr(vectorizer, 'vocabulary_'):
        print("⚠️  Vectorizer non ancora fittato!")
        return
    
    # Ottieni vocabulary
    vocab = vectorizer.vocabulary_
    
    print(f"\n✅ Totale parole nel vocabulary: {len(vocab)}")
    print(f"✅ Max features configurato: {vectorizer.max_features}")
    print(f"✅ Ngram range: {vectorizer.ngram_range}")
    print(f"✅ Min DF: {vectorizer.min_df}")
    print(f"✅ Max DF: {vectorizer.max_df}")
    
    # Inverti vocabulary (index -> word)
    idx_to_word = {idx: word for word, idx in vocab.items()}
    
    # Ordina per indice
    sorted_words = [idx_to_word[i] for i in sorted(idx_to_word.keys())]
    
    print(f"\n📋 Prime 50 parole del vocabulary:")
    print("-" * 80)
    for i in range(min(50, len(sorted_words))):
        print(f"  {i:3d}. {sorted_words[i]}")
    
    print(f"\n📋 Ultime 50 parole del vocabulary:")
    print("-" * 80)
    start = max(0, len(sorted_words) - 50)
    for i in range(start, len(sorted_words)):
        print(f"  {i:3d}. {sorted_words[i]}")
    
    # Cerca parole specifiche per tipo documento
    print(f"\n🔍 Parole chiave per tipo documento:")
    print("-" * 80)
    
    keywords_by_type = {
        'UNILAV': ['unilav', 'comunicazione', 'obbligatoria', 'rapporto', 'lavoro', 
                   'assunzione', 'lavoratore', 'centro', 'impiego', 'codice'],
        'CEDOLINO': ['cedolino', 'busta', 'paga', 'retribuzione', 'stipendio', 
                     'competenze', 'tfr', 'inps', 'contributi', 'netto'],
        'F24': ['f24', 'tributo', 'agenzia', 'entrate', 'ravvedimento', 
                'saldo', 'acconto', 'versare', 'compensazione'],
        'FATTURA': ['fattura', 'invoice', 'iva', 'imponibile', 'totale', 
                    'scadenza', 'pagamento', 'numero', 'cliente'],
    }
    
    for doc_type, keywords in keywords_by_type.items():
        print(f"\n  {doc_type}:")
        found = []
        for kw in keywords:
            if kw in vocab:
                idx = vocab[kw]
                found.append(f"{kw}[{idx}]")
        
        if found:
            print(f"    ✅ Trovate: {', '.join(found[:10])}")
            if len(found) > 10:
                print(f"    ... e altre {len(found) - 10}")
        else:
            print(f"    ⚠️  Nessuna keyword trovata")
    
    return vocab, idx_to_word


def analyze_feature_extraction_on_real_docs():
    """Analizza feature extraction su documenti REALI dal database."""
    print("\n" + "="*80)
    print("🔬 FEATURE EXTRACTION SU DOCUMENTI REALI")
    print("="*80)
    
    # Carica FeatureExtractor
    extractor = FeatureExtractor()
    
    # Prendi alcuni documenti di esempio per ogni tipo
    doc_types = ['UNILAV', 'CEDOL', 'F24', 'FATTURA']
    
    for doc_type in doc_types:
        print(f"\n📄 Tipo Documento: {doc_type}")
        print("-" * 80)
        
        # Cerca documenti di questo tipo
        docs = Documento.objects.filter(
            tipo__codice=doc_type
        ).exclude(
            file=''
        ).order_by('-data_creazione')[:2]  # Prime 2
        
        if not docs:
            print(f"  ⚠️  Nessun documento trovato per tipo {doc_type}")
            continue
        
        for doc in docs:
            print(f"\n  📋 {doc.codice} - {doc.titolo[:50]}")
            
            # Estrai testo (se disponibile)
            if hasattr(doc, 'estratto_testo') and doc.estratto_testo:
                text = doc.estratto_testo
            else:
                # Prova OCR al volo
                try:
                    from ai_classifier.services.ocr.pdf_text_extractor import PDFTextExtractor
                    pdf_extractor = PDFTextExtractor()
                    file_path = doc.file.path
                    
                    if os.path.exists(file_path):
                        result = pdf_extractor.extract_text(file_path)
                        text = result['text']
                    else:
                        print(f"    ⚠️  File non trovato: {file_path}")
                        continue
                except Exception as e:
                    print(f"    ❌ Errore estrazione testo: {e}")
                    continue
            
            # Estrai features
            try:
                features = extractor.extract_features(text, doc.file.name)
                
                print(f"    ✅ Features estratte:")
                
                # TF-IDF
                if 'text_features' in features:
                    non_zero = sum(1 for v in features['text_features'].values() if v > 0)
                    print(f"      - TF-IDF: {non_zero} parole non-zero (su 500)")
                    
                    # Top 10 parole con peso più alto
                    top_words = sorted(
                        features['text_features'].items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:10]
                    
                    print(f"      - Top 10 parole:")
                    for word, weight in top_words:
                        print(f"          '{word}': {weight:.4f}")
                
                # NER
                if 'ner_features' in features:
                    ner = features['ner_features']
                    print(f"      - NER:")
                    print(f"          Persons: {ner.get('persons_count', 0)}")
                    print(f"          Organizations: {ner.get('organizations_count', 0)}")
                    print(f"          Locations: {ner.get('locations_count', 0)}")
                    print(f"          Dates: {ner.get('dates_count', 0)}")
                    print(f"          Money: {ner.get('money_count', 0)}")
                
                # Patterns
                if 'pattern_features' in features:
                    patt = features['pattern_features']
                    print(f"      - Patterns:")
                    print(f"          Codici Fiscali: {patt.get('codici_fiscali_count', 0)}")
                    print(f"          Partite IVA: {patt.get('partite_iva_count', 0)}")
                    print(f"          Date: {patt.get('date_count', 0)}")
                    print(f"          Importi: {patt.get('importi_count', 0)}")
                    print(f"          Numeri Documento: {patt.get('numeri_documento_count', 0)}")
                
                # Filename
                if 'filename_features' in features:
                    fname = features['filename_features']
                    print(f"      - Filename:")
                    print(f"          Words: {fname.get('words_count', 0)}")
                    print(f"          Keywords match: {fname.get('keyword_match', 0)}")
                    print(f"          Date in filename: {fname.get('date_in_filename', 0)}")
                
                # Statistical
                if 'statistical_features' in features:
                    stats = features['statistical_features']
                    print(f"      - Statistical:")
                    print(f"          Word count: {stats.get('word_count', 0)}")
                    print(f"          Unique words: {stats.get('unique_words', 0)}")
                    print(f"          Avg word length: {stats.get('avg_word_length', 0):.2f}")
                
                # Feature vector finale
                feature_vector = extractor.get_feature_vector(features)
                print(f"\n      📊 Feature Vector:")
                print(f"          Shape: {feature_vector.shape}")
                print(f"          Non-zero values: {np.count_nonzero(feature_vector)}")
                print(f"          Min: {feature_vector.min():.4f}")
                print(f"          Max: {feature_vector.max():.4f}")
                print(f"          Mean: {feature_vector.mean():.4f}")
                
            except Exception as e:
                print(f"    ❌ Errore feature extraction: {e}")
                import traceback
                traceback.print_exc()


def main():
    """Main function."""
    print("\n" + "="*80)
    print("🎯 ANALISI FEATURE EXTRACTION - RISULTATI REALI")
    print("="*80)
    
    # 1. Carica vectorizer
    result = load_latest_vectorizer()
    if not result:
        return
    
    vectorizer, vectorizer_name = result
    
    # 2. Analizza vocabulary
    analyze_vocabulary(vectorizer)
    
    # 3. Analizza feature extraction su documenti reali
    analyze_feature_extraction_on_real_docs()
    
    print("\n" + "="*80)
    print("✅ ANALISI COMPLETATA!")
    print("="*80)


if __name__ == '__main__':
    main()
