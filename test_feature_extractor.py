"""
Test rapido del Feature Extractor
"""
import sys
import os
sys.path.insert(0, '/home/sandro/mygest')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')

import django
django.setup()

from ai_classifier.services.ml.feature_extractor import FeatureExtractor

# Testo di esempio (simula un cedolino)
sample_text = """
CEDOLINO PAGA - GENNAIO 2024

Dipendente: ROSSI MARIO
Codice Fiscale: RSSMRA85M01H501U
Azienda: ACME SRL - P.IVA 12345678901

Retribuzione Lorda: € 2.500,00
Contributi INPS: € 500,00
IRPEF: € 400,00
Netto: € 1.600,00

Data Pagamento: 27/01/2024
Numero: CED-2024-001
"""

print("🧪 TEST FEATURE EXTRACTOR")
print("=" * 60)

# Inizializza extractor
extractor = FeatureExtractor()

# Estrai features
features = extractor.extract_features(
    text=sample_text,
    filename="cedolino_gennaio_2024.pdf",
    metadata={'pages': 1, 'method': 'native'}
)

print("\n📊 FEATURES ESTRATTE:")
print("-" * 60)

# Text features
print("\n1️⃣ TEXT FEATURES:")
print(f"  • Fitted: {features['text_features'].get('vectorizer_fitted', False)}")
if not features['text_features'].get('vectorizer_fitted'):
    print("  ℹ️  TF-IDF non fitted (normale prima del training)")

# NER features
print("\n2️⃣ NER FEATURES:")
ner = features['ner_features']
print(f"  • Persone: {ner.get('persons_count', 0)} -> {ner.get('persons', [])}")
print(f"  • Organizzazioni: {ner.get('organizations_count', 0)} -> {ner.get('organizations', [])}")
print(f"  • Date: {ner.get('dates_count', 0)}")
print(f"  • Money: {ner.get('money_count', 0)}")

# Pattern features
print("\n3️⃣ PATTERN FEATURES:")
patterns = features['pattern_features']
print(f"  • Codici Fiscali: {patterns.get('codici_fiscali_count', 0)} -> {patterns.get('codici_fiscali', [])}")
print(f"  • Partite IVA: {patterns.get('partite_iva_count', 0)} -> {patterns.get('partite_iva', [])}")
print(f"  • Date: {patterns.get('date_count', 0)} -> {patterns.get('date_found', [])[:3]}")
print(f"  • Importi: {patterns.get('importi_count', 0)} -> {patterns.get('importi_found', [])[:3]}")
print(f"  • Numeri doc: {patterns.get('numeri_documento_count', 0)} -> {patterns.get('numeri_documento', [])}")
print(f"  • Keywords matched: {patterns.get('keywords_matched', {})}")

# Filename features
print("\n4️⃣ FILENAME FEATURES:")
fname = features['filename_features']
print(f"  • Filename: {fname.get('filename', '')}")
print(f"  • Words: {fname.get('words_count', 0)} -> {fname.get('words_in_filename', [])[:5]}")
print(f"  • Keyword matches: {fname.get('keyword_matches', [])}")
print(f"  • Date in filename: {fname.get('date_in_filename', [])}")
print(f"  • Year: {fname.get('year_in_filename', [])}")

# Statistical features
print("\n5️⃣ STATISTICAL FEATURES:")
stats = features['statistical_features']
print(f"  • Caratteri: {stats.get('char_count', 0)}")
print(f"  • Parole: {stats.get('word_count', 0)}")
print(f"  • Parole uniche: {stats.get('unique_words', 0)}")
print(f"  • Lunghezza media parola: {stats.get('avg_word_length', 0):.2f}")
print(f"  • Densità digit: {stats.get('digit_density', 0):.2%}")
print(f"  • Densità maiuscole: {stats.get('upper_density', 0):.2%}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETATO")
print(f"📦 Features totali estratte: {features.get('text_length', 0)} char di testo")
