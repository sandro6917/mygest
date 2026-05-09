#!/usr/bin/env python
"""
Script per testare il feature extraction su documenti reali
del database ADESSO (non dai file di training).

Mostra esattamente cosa viene estratto da ogni documento.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import Documento
from ai_classifier.services.ml.feature_extractor import FeatureExtractor
from ai_classifier.services.ml.ocr_service import OCRService
import numpy as np


def analyze_document(documento_id):
    """Analizza un singolo documento."""
    try:
        doc = Documento.objects.get(pk=documento_id)
    except Documento.DoesNotExist:
        print(f"❌ Documento {documento_id} non trovato!")
        return
    
    print("\n" + "="*80)
    print(f"📄 DOCUMENTO: {doc.codice}")
    print("="*80)
    print(f"Titolo: {doc.titolo}")
    print(f"Tipo: {doc.tipo.nome if doc.tipo else 'N/A'}")
    print(f"Cliente: {doc.cliente.anagrafica.nome if doc.cliente else 'N/A'}")
    print(f"File: {doc.file.name if doc.file else 'N/A'}")
    
    if not doc.file:
        print("\n⚠️  Nessun file allegato!")
        return
    
    # Estrai testo con OCR
    print(f"\n🔍 Estrazione testo con OCR...")
    
    ocr_service = OCRService()
    
    try:
        file_path = doc.file.path
        
        if not os.path.exists(file_path):
            print(f"❌ File non trovato: {file_path}")
            return
        
        ocr_result = ocr_service.extract_text_from_file(file_path)
        text = ocr_result['text']
        
        print(f"✅ Testo estratto: {len(text)} caratteri")
        print(f"   Metodo OCR: {ocr_result.get('method', 'N/A')}")
        print(f"   Confidence: {ocr_result.get('confidence', 'N/A')}")
        
        # Mostra preview testo (primi 500 caratteri)
        print(f"\n📝 Preview testo estratto (primi 500 caratteri):")
        print("-" * 80)
        print(text[:500])
        if len(text) > 500:
            print(f"\n... (altri {len(text) - 500} caratteri)")
        
    except Exception as e:
        print(f"❌ Errore OCR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Feature Extraction
    print(f"\n🔬 Feature Extraction...")
    print("="*80)
    
    extractor = FeatureExtractor()
    
    try:
        features = extractor.extract_features(text, doc.file.name)
        
        # 1. TF-IDF Features
        print(f"\n1️⃣  TF-IDF TEXT FEATURES (500 dimensioni)")
        print("-" * 80)
        
        if 'text_features' in features:
            text_features = features['text_features']
            non_zero = sum(1 for v in text_features.values() if v > 0)
            
            print(f"   Parole con peso non-zero: {non_zero}/500")
            
            # Top 20 parole
            top_words = sorted(
                text_features.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            
            print(f"\n   📊 Top 20 parole per peso TF-IDF:")
            for i, (word, weight) in enumerate(top_words, 1):
                print(f"      {i:2d}. '{word}': {weight:.6f}")
        
        # 2. NER Features
        print(f"\n2️⃣  NER FEATURES (5 dimensioni)")
        print("-" * 80)
        
        if 'ner_features' in features:
            ner = features['ner_features']
            
            print(f"   Persons (PER):        {ner.get('persons_count', 0):3d} → {ner.get('persons_count', 0)/10:.2f}")
            print(f"   Organizations (ORG):  {ner.get('organizations_count', 0):3d} → {ner.get('organizations_count', 0)/10:.2f}")
            print(f"   Locations (LOC/GPE):  {ner.get('locations_count', 0):3d} → {ner.get('locations_count', 0)/5:.2f}")
            print(f"   Dates (DATE):         {ner.get('dates_count', 0):3d} → {ner.get('dates_count', 0)/20:.2f}")
            print(f"   Money (MONEY):        {ner.get('money_count', 0):3d} → {ner.get('money_count', 0)/20:.2f}")
            
            # Mostra esempi se disponibili
            if 'persons_examples' in ner and ner['persons_examples']:
                print(f"\n   👤 Persone trovate: {', '.join(ner['persons_examples'][:5])}")
            if 'organizations_examples' in ner and ner['organizations_examples']:
                print(f"   🏢 Organizzazioni: {', '.join(ner['organizations_examples'][:5])}")
            if 'locations_examples' in ner and ner['locations_examples']:
                print(f"   📍 Luoghi: {', '.join(ner['locations_examples'][:5])}")
        
        # 3. Pattern Features
        print(f"\n3️⃣  PATTERN FEATURES (5 dimensioni)")
        print("-" * 80)
        
        if 'pattern_features' in features:
            patt = features['pattern_features']
            
            cf_count = patt.get('codici_fiscali_count', 0)
            piva_count = patt.get('partite_iva_count', 0)
            date_count = patt.get('date_count', 0)
            importi_count = patt.get('importi_count', 0)
            num_doc_count = patt.get('numeri_documento_count', 0)
            
            print(f"   Codici Fiscali:       {cf_count:3d} → {min(cf_count/5, 1.0):.2f}")
            print(f"   Partite IVA:          {piva_count:3d} → {min(piva_count/5, 1.0):.2f}")
            print(f"   Date:                 {date_count:3d} → {min(date_count/20, 1.0):.2f}")
            print(f"   Importi:              {importi_count:3d} → {min(importi_count/20, 1.0):.2f}")
            print(f"   Numeri Documento:     {num_doc_count:3d} → {min(num_doc_count/5, 1.0):.2f}")
            
            # Esempi
            if 'codici_fiscali_examples' in patt and patt['codici_fiscali_examples']:
                print(f"\n   🆔 CF trovati: {', '.join(patt['codici_fiscali_examples'][:3])}")
            if 'date_examples' in patt and patt['date_examples']:
                print(f"   📅 Date trovate: {', '.join(patt['date_examples'][:5])}")
            if 'importi_examples' in patt and patt['importi_examples']:
                print(f"   💰 Importi trovati: {', '.join(patt['importi_examples'][:5])}")
        
        # 4. Filename Features
        print(f"\n4️⃣  FILENAME FEATURES (3 dimensioni)")
        print("-" * 80)
        
        if 'filename_features' in features:
            fname = features['filename_features']
            
            words = fname.get('words_count', 0)
            keyword = fname.get('keyword_match', 0)
            date_fname = fname.get('date_in_filename', 0)
            
            print(f"   Words in filename:    {words:3d} → {min(words/20, 1.0):.2f}")
            print(f"   Keyword match:        {keyword:.2f}")
            print(f"   Date in filename:     {date_fname:.2f}")
            
            if 'matched_keywords' in fname and fname['matched_keywords']:
                print(f"\n   🔑 Keywords matchate: {', '.join(fname['matched_keywords'])}")
        
        # 5. Statistical Features
        print(f"\n5️⃣  STATISTICAL FEATURES (6 dimensioni)")
        print("-" * 80)
        
        if 'statistical_features' in features:
            stats = features['statistical_features']
            
            word_count = stats.get('word_count', 0)
            unique_words = stats.get('unique_words', 0)
            avg_len = stats.get('avg_word_length', 0)
            special = stats.get('special_char_density', 0)
            digit = stats.get('digit_density', 0)
            upper = stats.get('upper_density', 0)
            
            print(f"   Word count:           {word_count:5d} → {min(word_count/5000, 1.0):.4f}")
            print(f"   Unique words:         {unique_words:5d} → {min(unique_words/2000, 1.0):.4f}")
            print(f"   Avg word length:      {avg_len:5.2f} → {avg_len/20:.4f}")
            print(f"   Special char density: {special:.4f}")
            print(f"   Digit density:        {digit:.4f}")
            print(f"   Upper density:        {upper:.4f}")
        
        # Feature Vector Finale
        print(f"\n📊 FEATURE VECTOR FINALE (519 dimensioni)")
        print("="*80)
        
        feature_vector = extractor.get_feature_vector(features)
        
        print(f"   Shape:          {feature_vector.shape}")
        print(f"   Type:           {feature_vector.dtype}")
        print(f"   Non-zero:       {np.count_nonzero(feature_vector)}/519 ({np.count_nonzero(feature_vector)/519*100:.1f}%)")
        print(f"   Min value:      {feature_vector.min():.6f}")
        print(f"   Max value:      {feature_vector.max():.6f}")
        print(f"   Mean:           {feature_vector.mean():.6f}")
        print(f"   Std dev:        {feature_vector.std():.6f}")
        
        # Breakdown per categoria
        print(f"\n   📋 Breakdown per categoria:")
        print(f"      TF-IDF (0-499):      {np.count_nonzero(feature_vector[:500])}/500 non-zero")
        print(f"      NER (500-504):       {np.count_nonzero(feature_vector[500:505])}/5 non-zero")
        print(f"      Pattern (505-509):   {np.count_nonzero(feature_vector[505:510])}/5 non-zero")
        print(f"      Filename (510-512):  {np.count_nonzero(feature_vector[510:513])}/3 non-zero")
        print(f"      Statistical (513-518): {np.count_nonzero(feature_vector[513:519])}/6 non-zero")
        
        # Top 10 features con valore più alto
        print(f"\n   🔝 Top 10 features con valore più alto:")
        top_indices = np.argsort(feature_vector)[-10:][::-1]
        for i, idx in enumerate(top_indices, 1):
            category = (
                "TF-IDF" if idx < 500 else
                "NER" if idx < 505 else
                "Pattern" if idx < 510 else
                "Filename" if idx < 513 else
                "Statistical"
            )
            print(f"      {i:2d}. Index {idx:3d} ({category}): {feature_vector[idx]:.6f}")
        
    except Exception as e:
        print(f"❌ Errore feature extraction: {e}")
        import traceback
        traceback.print_exc()


def list_recent_documents():
    """Lista documenti recenti per ogni tipo."""
    print("\n" + "="*80)
    print("📋 DOCUMENTI DISPONIBILI PER ANALISI")
    print("="*80)
    
    doc_types = ['UNILAV', 'CEDOL', 'F24', 'FATTURA', 'LIBUNI']
    
    for tipo_code in doc_types:
        print(f"\n📁 Tipo: {tipo_code}")
        print("-" * 80)
        
        docs = Documento.objects.filter(
            tipo__codice=tipo_code
        ).exclude(
            file=''
        ).order_by('-creato_il')[:5]
        
        if not docs:
            print(f"   ⚠️  Nessun documento trovato")
            continue
        
        for doc in docs:
            print(f"   ID {doc.id:5d}: {doc.codice:20s} - {doc.titolo[:40]:40s}")


def main():
    """Main function."""
    import sys
    
    print("\n" + "="*80)
    print("🔬 ANALISI FEATURE EXTRACTION - DOCUMENTI REALI")
    print("="*80)
    
    if len(sys.argv) < 2:
        print("\n⚠️  Uso: python analizza_feature_extraction_results.py <documento_id>")
        print("   oppure: python analizza_feature_extraction_results.py list")
        list_recent_documents()
        return
    
    if sys.argv[1] == 'list':
        list_recent_documents()
    else:
        try:
            doc_id = int(sys.argv[1])
            analyze_document(doc_id)
        except ValueError:
            print(f"❌ ID documento non valido: {sys.argv[1]}")


if __name__ == '__main__':
    main()
