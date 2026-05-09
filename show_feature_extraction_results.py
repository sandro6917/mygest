#!/usr/bin/env python
"""
Analisi Feature Extraction su file UNILAV reale.
Mostra TUTTI i dettagli di cosa viene estratto.
"""

import os
import sys
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')

import django
django.setup()

from ai_classifier.services.ml.feature_extractor import FeatureExtractor
from ai_classifier.services.ml.ocr_service import OCRService
import numpy as np


def analyze_file(pdf_path):
    """Analizza un file PDF con feature extraction completa."""
    
    if not os.path.exists(pdf_path):
        print(f"❌ File non trovato: {pdf_path}")
        return
    
    filename = os.path.basename(pdf_path)
    
    print("\n" + "="*80)
    print(f"📄 FILE: {filename}")
    print("="*80)
    print(f"Path: {pdf_path}")
    print(f"Size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
    
    # Step 1: OCR
    print(f"\n🔍 STEP 1: ESTRAZIONE TESTO (OCR)")
    print("-" * 80)
    
    ocr_service = OCRService()
    
    try:
        ocr_result = ocr_service.extract_text_from_file(pdf_path)
        text = ocr_result['text']
        
        print(f"✅ Testo estratto:")
        print(f"   Caratteri: {len(text)}")
        print(f"   Parole: {len(text.split())}")
        print(f"   Righe: {len(text.splitlines())}")
        print(f"   Metodo: {ocr_result.get('method', 'N/A')}")
        
        # Preview testo
        print(f"\n📝 Preview testo (primi 1000 caratteri):")
        print("-" * 80)
        print(text[:1000])
        if len(text) > 1000:
            print(f"\n... (altri {len(text) - 1000} caratteri)")
        
    except Exception as e:
        print(f"❌ Errore OCR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Feature Extraction
    print(f"\n\n🔬 STEP 2: FEATURE EXTRACTION")
    print("="*80)
    
    extractor = FeatureExtractor()
    
    try:
        features = extractor.extract_features(text, filename)
        
        # ========== 1. TF-IDF ==========
        print(f"\n1️⃣  TF-IDF TEXT FEATURES (500 dimensioni)")
        print("="*80)
        
        if 'text_features' in features:
            text_features = features['text_features']
            
            # Check se vectorizer è fittato
            if text_features.get('vectorizer_fitted') == False:
                print("⚠️  Vectorizer non ancora fittato (serve training)")
                print(f"\n📝 Preview testo processato:")
                print("-" * 80)
                print(text_features.get('text_preview', '')[:500])
            
            elif 'tfidf_vector' in text_features:
                tfidf_dict = text_features['tfidf_vector']
                non_zero = len(tfidf_dict)
                
                print(f"✅ Parole con peso non-zero: {non_zero}/500 ({non_zero/5:.1f}%)")
                
                # Top 30 parole
                top_words = sorted(
                    tfidf_dict.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:30]
                
                print(f"\n📊 Top 30 parole per peso TF-IDF:")
                print("-" * 80)
                for i, (word, weight) in enumerate(top_words, 1):
                    bar_length = int(weight * 50)
                    bar = "█" * bar_length
                    print(f"   {i:2d}. {word:25s} {weight:.6f} {bar}")
            else:
                print("⚠️  Errore TF-IDF:", text_features.get('error', 'Sconosciuto'))
        else:
            print("⚠️  Nessuna feature TF-IDF estratta")
        
        # ========== 2. NER ==========
        print(f"\n\n2️⃣  NER FEATURES (Named Entity Recognition - 5 dimensioni)")
        print("="*80)
        
        if 'ner_features' in features:
            ner = features['ner_features']
            
            print(f"Conteggi entità trovate:")
            print("-" * 80)
            print(f"   👤 Persone (PER):        {ner.get('persons_count', 0):3d} trovate → valore: {min(ner.get('persons_count', 0)/10, 1.0):.4f}")
            print(f"   🏢 Organizzazioni (ORG): {ner.get('organizations_count', 0):3d} trovate → valore: {min(ner.get('organizations_count', 0)/10, 1.0):.4f}")
            print(f"   📍 Luoghi (LOC/GPE):     {ner.get('locations_count', 0):3d} trovati → valore: {min(ner.get('locations_count', 0)/5, 1.0):.4f}")
            print(f"   📅 Date (DATE):          {ner.get('dates_count', 0):3d} trovate → valore: {min(ner.get('dates_count', 0)/20, 1.0):.4f}")
            print(f"   💰 Valori (MONEY):       {ner.get('money_count', 0):3d} trovati → valore: {min(ner.get('money_count', 0)/20, 1.0):.4f}")
            
            # Esempi dettagliati
            if ner.get('persons_count', 0) > 0 and 'persons' in ner:
                print(f"\n   👤 Persone riconosciute:")
                persons = ner['persons']
                for i, person in enumerate(persons, 1):
                    print(f"      {i}. {person}")
            
            if ner.get('organizations_count', 0) > 0 and 'organizations' in ner:
                print(f"\n   🏢 Organizzazioni riconosciute:")
                orgs = ner['organizations']
                for i, org in enumerate(orgs, 1):
                    print(f"      {i}. {org}")
            
            if ner.get('locations_count', 0) > 0 and 'locations' in ner:
                print(f"\n   📍 Luoghi riconosciuti:")
                locs = ner['locations']
                for i, loc in enumerate(locs[:10], 1):
                    print(f"      {i}. {loc}")
                if len(locs) > 10:
                    print(f"      ... e altri {len(locs) - 10}")
        
        # ========== 3. PATTERN ==========
        print(f"\n\n3️⃣  PATTERN FEATURES (Regex Matching - 5 dimensioni)")
        print("="*80)
        
        if 'pattern_features' in features:
            patt = features['pattern_features']
            
            cf_count = patt.get('codici_fiscali_count', 0)
            piva_count = patt.get('partite_iva_count', 0)
            date_count = patt.get('date_count', 0)
            importi_count = patt.get('importi_count', 0)
            num_doc_count = patt.get('numeri_documento_count', 0)
            
            print(f"Pattern matchati:")
            print("-" * 80)
            print(f"   🆔 Codici Fiscali:       {cf_count:3d} trovati → valore: {min(cf_count/5, 1.0):.4f}")
            print(f"   🏛️  Partite IVA:          {piva_count:3d} trovate → valore: {min(piva_count/5, 1.0):.4f}")
            print(f"   📅 Date:                 {date_count:3d} trovate → valore: {min(date_count/20, 1.0):.4f}")
            print(f"   💶 Importi:              {importi_count:3d} trovati → valore: {min(importi_count/20, 1.0):.4f}")
            print(f"   📋 Numeri Documento:     {num_doc_count:3d} trovati → valore: {min(num_doc_count/5, 1.0):.4f}")
            
            # Esempi
            if cf_count > 0 and 'codici_fiscali' in patt:
                print(f"\n   🆔 Codici Fiscali trovati:")
                cfs = patt['codici_fiscali']
                for i, cf in enumerate(cfs, 1):
                    print(f"      {i}. {cf}")
            
            if piva_count > 0 and 'partite_iva' in patt:
                print(f"\n   🏛️  Partite IVA trovate:")
                pivas = patt['partite_iva']
                for i, piva in enumerate(pivas, 1):
                    print(f"      {i}. {piva}")
            
            if date_count > 0 and 'date_found' in patt:
                print(f"\n   📅 Date trovate:")
                dates = patt['date_found']
                for i, date in enumerate(dates, 1):
                    print(f"      {i}. {date}")
            
            if importi_count > 0 and 'importi_found' in patt:
                print(f"\n   💶 Importi trovati:")
                importi = patt['importi_found']
                for i, importo in enumerate(importi, 1):
                    print(f"      {i}. {importo}")
            
            if num_doc_count > 0 and 'numeri_documento' in patt:
                print(f"\n   📋 Numeri Documento trovati:")
                nums = patt['numeri_documento']
                for i, num in enumerate(nums, 1):
                    print(f"      {i}. {num}")
        
        # ========== 4. FILENAME ==========
        print(f"\n\n4️⃣  FILENAME FEATURES (3 dimensioni)")
        print("="*80)
        
        if 'filename_features' in features:
            fname = features['filename_features']
            
            words = fname.get('words_count', 0)
            keyword = fname.get('keyword_match', 0)
            date_fname = fname.get('date_in_filename', 0)
            
            # Gestisci se sono liste
            if isinstance(date_fname, list):
                date_fname = 1.0 if date_fname else 0.0
            if isinstance(keyword, list):
                keyword = 1.0 if keyword else 0.0
            
            print(f"Analisi filename: '{filename}'")
            print("-" * 80)
            print(f"   📝 Parole in filename:   {words:3d} → valore: {min(words/20, 1.0):.4f}")
            print(f"   🔑 Keyword match:        {'SÌ' if keyword > 0 else 'NO':3s} → valore: {keyword:.4f}")
            print(f"   📅 Data in filename:     {'SÌ' if date_fname > 0 else 'NO':3s} → valore: {date_fname:.4f}")
            
            if 'matched_keywords' in fname and fname['matched_keywords']:
                print(f"\n   🔑 Keywords matchate: {', '.join(fname['matched_keywords'])}")
            
            if 'filename_words' in fname and fname['filename_words']:
                print(f"\n   📝 Parole estratte: {', '.join(fname['filename_words'][:15])}")
        
        # ========== 5. STATISTICAL ==========
        print(f"\n\n5️⃣  STATISTICAL FEATURES (6 dimensioni)")
        print("="*80)
        
        if 'statistical_features' in features:
            stats = features['statistical_features']
            
            word_count = stats.get('word_count', 0)
            unique_words = stats.get('unique_words', 0)
            avg_len = stats.get('avg_word_length', 0)
            special = stats.get('special_char_density', 0)
            digit = stats.get('digit_density', 0)
            upper = stats.get('upper_density', 0)
            
            print(f"Statistiche testuali:")
            print("-" * 80)
            print(f"   📊 Parole totali:        {word_count:5d} → valore: {min(word_count/5000, 1.0):.6f}")
            print(f"   🔤 Parole unique:        {unique_words:5d} → valore: {min(unique_words/2000, 1.0):.6f}")
            print(f"   📏 Lungh. media parola:  {avg_len:5.2f} → valore: {avg_len/20:.6f}")
            print(f"   ✨ Densità car. spec.:   {special:.6f}")
            print(f"   🔢 Densità cifre:        {digit:.6f}")
            print(f"   🔠 Densità maiuscole:    {upper:.6f}")
            
            print(f"\n   📈 Rapporti:")
            if word_count > 0:
                print(f"      Parole unique/totali: {unique_words/word_count*100:.1f}%")
                print(f"      Vocabolario ricchezza: {'Alto' if unique_words/word_count > 0.5 else 'Medio' if unique_words/word_count > 0.3 else 'Basso'}")
        
        # ========== FEATURE VECTOR FINALE ==========
        print(f"\n\n📊 FEATURE VECTOR FINALE (519 dimensioni)")
        print("="*80)
        
        feature_vector = extractor.get_feature_vector(features)
        
        print(f"\n✅ Riepilogo vettore:")
        print("-" * 80)
        print(f"   Shape:          {feature_vector.shape}")
        print(f"   Type:           {feature_vector.dtype}")
        print(f"   Total features: {len(feature_vector)}")
        print(f"   Non-zero:       {np.count_nonzero(feature_vector)} ({np.count_nonzero(feature_vector)/519*100:.1f}%)")
        print(f"   Min value:      {feature_vector.min():.8f}")
        print(f"   Max value:      {feature_vector.max():.8f}")
        print(f"   Mean:           {feature_vector.mean():.8f}")
        print(f"   Std dev:        {feature_vector.std():.8f}")
        
        print(f"\n📋 Breakdown per categoria:")
        print("-" * 80)
        tfidf_nz = np.count_nonzero(feature_vector[:500])
        ner_nz = np.count_nonzero(feature_vector[500:505])
        patt_nz = np.count_nonzero(feature_vector[505:510])
        fname_nz = np.count_nonzero(feature_vector[510:513])
        stats_nz = np.count_nonzero(feature_vector[513:519])
        
        print(f"   1. TF-IDF (dim 0-499):       {tfidf_nz:3d}/500 non-zero ({tfidf_nz/5:.1f}%)")
        print(f"   2. NER (dim 500-504):        {ner_nz:3d}/5   non-zero ({ner_nz/5*100:.1f}%)")
        print(f"   3. Pattern (dim 505-509):    {patt_nz:3d}/5   non-zero ({patt_nz/5*100:.1f}%)")
        print(f"   4. Filename (dim 510-512):   {fname_nz:3d}/3   non-zero ({fname_nz/3*100:.1f}%)")
        print(f"   5. Statistical (dim 513-518):{stats_nz:3d}/6   non-zero ({stats_nz/6*100:.1f}%)")
        
        print(f"\n🔝 Top 20 features con valore più alto:")
        print("-" * 80)
        top_indices = np.argsort(feature_vector)[-20:][::-1]
        for i, idx in enumerate(top_indices, 1):
            if idx < 500:
                category = "TF-IDF"
            elif idx < 505:
                category = "NER"
            elif idx < 510:
                category = "Pattern"
            elif idx < 513:
                category = "Filename"
            else:
                category = "Statistical"
            
            bar_length = int(feature_vector[idx] * 30)
            bar = "█" * bar_length
            print(f"   {i:2d}. Dim {idx:3d} ({category:12s}): {feature_vector[idx]:.8f} {bar}")
        
        print(f"\n✅ FEATURE EXTRACTION COMPLETATA!")
        
    except Exception as e:
        print(f"❌ Errore feature extraction: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main."""
    pdf_file = "/home/sandro/mygest/UNILAV_1700026200007595.pdf"
    
    print("\n" + "="*80)
    print("🔬 ANALISI FEATURE EXTRACTION - RISULTATI REALI")
    print("="*80)
    
    analyze_file(pdf_file)
    
    print("\n" + "="*80)
    print("✅ ANALISI COMPLETATA")
    print("="*80)


if __name__ == '__main__':
    main()
