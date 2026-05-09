#!/usr/bin/env python
"""
Estrae il testo completo di TUTTI i documenti usati per il training ML.
Salva ogni documento in formato markdown con metadati e feature extraction results.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')

import django
django.setup()

from documenti.models import Documento
from ai_classifier.services.ml.ocr_service import OCRService
from ai_classifier.services.ml.feature_extractor import FeatureExtractor
import numpy as np


def extract_all_training_documents():
    """Estrae testo di tutti i documenti usati per training."""
    
    print("\n" + "="*80)
    print("📚 ESTRAZIONE TESTI COMPLETI - DOCUMENTI TRAINING")
    print("="*80)
    
    # Query documenti con file e tipo documento
    # (questi sono i documenti usati per il training)
    documents = Documento.objects.filter(
        tipo__isnull=False
    ).exclude(
        file=''
    ).select_related(
        'tipo', 'cliente__anagrafica', 'titolario_voce'
    ).order_by('tipo__codice', 'creato_il')
    
    total = documents.count()
    
    print(f"\n📊 Documenti trovati: {total}")
    
    if total == 0:
        print("\n⚠️  Nessun documento trovato!")
        return
    
    # Raggruppa per tipo
    docs_by_type = {}
    for doc in documents:
        tipo_code = doc.tipo.codice if doc.tipo else 'SCONOSCIUTO'
        if tipo_code not in docs_by_type:
            docs_by_type[tipo_code] = []
        docs_by_type[tipo_code].append(doc)
    
    print(f"\n📁 Tipi documento trovati: {len(docs_by_type)}")
    for tipo, docs in docs_by_type.items():
        print(f"   - {tipo}: {len(docs)} documenti")
    
    # Inizializza services
    ocr_service = OCRService()
    feature_extractor = FeatureExtractor()
    
    # Output markdown
    output_lines = []
    output_lines.append("# 📄 Testi Completi Estratti - Dataset Training ML\n")
    output_lines.append(f"**Generato**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    output_lines.append(f"**Totale documenti**: {total}\n")
    output_lines.append(f"**Tipi documento**: {', '.join(docs_by_type.keys())}\n")
    output_lines.append("\n---\n")
    
    # Statistiche globali
    stats = {
        'totale_documenti': total,
        'totale_caratteri': 0,
        'totale_parole': 0,
        'documenti_per_tipo': {},
        'errori_ocr': 0,
        'metodi_ocr': {'native': 0, 'tesseract': 0, 'hybrid': 0},
    }
    
    # Processa ogni tipo
    for tipo_code, docs in sorted(docs_by_type.items()):
        print(f"\n{'='*80}")
        print(f"📂 TIPO DOCUMENTO: {tipo_code} ({len(docs)} documenti)")
        print(f"{'='*80}")
        
        output_lines.append(f"\n## 📂 Tipo Documento: {tipo_code}\n")
        output_lines.append(f"**Totale documenti**: {len(docs)}\n")
        output_lines.append("\n---\n")
        
        stats['documenti_per_tipo'][tipo_code] = {
            'totale': len(docs),
            'caratteri': 0,
            'parole': 0,
        }
        
        # Processa ogni documento
        for idx, doc in enumerate(docs, 1):
            print(f"\n   [{idx}/{len(docs)}] Processando: {doc.codice}")
            
            # Header documento
            output_lines.append(f"\n### 📄 Documento {idx}/{len(docs)}: `{doc.codice}`\n")
            output_lines.append("\n#### 📋 Metadati\n")
            output_lines.append("| Campo | Valore |\n")
            output_lines.append("|-------|--------|\n")
            output_lines.append(f"| **Codice** | `{doc.codice}` |\n")
            output_lines.append(f"| **Descrizione** | {doc.descrizione or 'N/A'} |\n")
            output_lines.append(f"| **Tipo** | {doc.tipo.nome if doc.tipo else 'N/A'} ({tipo_code}) |\n")
            output_lines.append(f"| **Cliente** | {doc.cliente.anagrafica.nome if doc.cliente else 'N/A'} |\n")
            output_lines.append(f"| **Data Documento** | {doc.data_documento or 'N/A'} |\n")
            output_lines.append(f"| **Data Creazione** | {doc.creato_il.strftime('%d/%m/%Y %H:%M') if doc.creato_il else 'N/A'} |\n")
            output_lines.append(f"| **File** | `{doc.file.name if doc.file else 'N/A'}` |\n")
            
            if doc.titolario_voce:
                output_lines.append(f"| **Titolario** | {doc.titolario_voce.codice} - {doc.titolario_voce.titolo} |\n")
            
            # Estrai testo
            if not doc.file:
                output_lines.append("\n⚠️ **Nessun file allegato**\n")
                continue
            
            file_path = doc.file.path
            if not os.path.exists(file_path):
                output_lines.append(f"\n⚠️ **File non trovato**: `{file_path}`\n")
                continue
            
            try:
                # OCR
                ocr_result = ocr_service.extract_text_from_file(file_path)
                text = ocr_result['text']
                method = ocr_result.get('method', 'unknown')
                confidence = ocr_result.get('confidence', 'N/A')
                
                char_count = len(text)
                word_count = len(text.split())
                line_count = len(text.splitlines())
                
                # Aggiorna stats
                stats['totale_caratteri'] += char_count
                stats['totale_parole'] += word_count
                stats['documenti_per_tipo'][tipo_code]['caratteri'] += char_count
                stats['documenti_per_tipo'][tipo_code]['parole'] += word_count
                stats['metodi_ocr'][method] = stats['metodi_ocr'].get(method, 0) + 1
                
                # Metadati OCR
                output_lines.append(f"| **Metodo OCR** | {method} |\n")
                output_lines.append(f"| **Confidence** | {confidence} |\n")
                output_lines.append(f"| **Caratteri** | {char_count:,} |\n")
                output_lines.append(f"| **Parole** | {word_count:,} |\n")
                output_lines.append(f"| **Righe** | {line_count:,} |\n")
                
                print(f"      ✅ OCR: {char_count} caratteri, {word_count} parole (metodo: {method})")
                
                # Feature Extraction
                try:
                    features = feature_extractor.extract_features(text, doc.file.name)
                    
                    output_lines.append("\n#### 🔬 Feature Extraction Summary\n")
                    
                    # NER
                    if 'ner_features' in features:
                        ner = features['ner_features']
                        output_lines.append("\n**Named Entities (NER)**:\n")
                        output_lines.append(f"- 👤 Persone: {ner.get('persons_count', 0)}\n")
                        output_lines.append(f"- 🏢 Organizzazioni: {ner.get('organizations_count', 0)}\n")
                        output_lines.append(f"- 📍 Luoghi: {ner.get('locations_count', 0)}\n")
                        output_lines.append(f"- 📅 Date: {ner.get('dates_count', 0)}\n")
                        output_lines.append(f"- 💰 Valori: {ner.get('money_count', 0)}\n")
                    
                    # Pattern
                    if 'pattern_features' in features:
                        patt = features['pattern_features']
                        output_lines.append("\n**Pattern Regex**:\n")
                        output_lines.append(f"- 🆔 Codici Fiscali: {patt.get('codici_fiscali_count', 0)}\n")
                        output_lines.append(f"- 🏛️ Partite IVA: {patt.get('partite_iva_count', 0)}\n")
                        output_lines.append(f"- 📅 Date: {patt.get('date_count', 0)}\n")
                        output_lines.append(f"- 💶 Importi: {patt.get('importi_count', 0)}\n")
                        
                        # Mostra esempi CF
                        if patt.get('codici_fiscali'):
                            output_lines.append(f"\n**Codici Fiscali trovati**: {', '.join(patt['codici_fiscali'])}\n")
                    
                    # Statistical
                    if 'statistical_features' in features:
                        stats_feat = features['statistical_features']
                        output_lines.append("\n**Statistiche Testuali**:\n")
                        output_lines.append(f"- Parole unique: {stats_feat.get('unique_words', 0)}\n")
                        output_lines.append(f"- Lunghezza media parola: {stats_feat.get('avg_word_length', 0):.2f}\n")
                        output_lines.append(f"- Densità cifre: {stats_feat.get('digit_density', 0):.2%}\n")
                        output_lines.append(f"- Densità maiuscole: {stats_feat.get('upper_density', 0):.2%}\n")
                    
                except Exception as e:
                    print(f"      ⚠️  Feature extraction error: {e}")
                    output_lines.append(f"\n⚠️ **Feature extraction error**: {str(e)}\n")
                
                # Testo completo
                output_lines.append("\n#### 📝 Testo Completo Estratto\n")
                output_lines.append("\n```\n")
                output_lines.append(text)
                output_lines.append("\n```\n")
                output_lines.append("\n---\n")
                
            except Exception as e:
                print(f"      ❌ Errore OCR: {e}")
                output_lines.append(f"\n❌ **Errore OCR**: {str(e)}\n")
                stats['errori_ocr'] += 1
    
    # Aggiungi statistiche finali
    output_lines.insert(4, "\n## 📊 Statistiche Globali\n")
    output_lines.insert(5, f"- **Totale documenti**: {stats['totale_documenti']}\n")
    output_lines.insert(6, f"- **Totale caratteri estratti**: {stats['totale_caratteri']:,}\n")
    output_lines.insert(7, f"- **Totale parole estratte**: {stats['totale_parole']:,}\n")
    output_lines.insert(8, f"- **Errori OCR**: {stats['errori_ocr']}\n")
    output_lines.insert(9, f"- **Metodi OCR usati**: {dict(stats['metodi_ocr'])}\n")
    output_lines.insert(10, "\n### 📈 Breakdown per Tipo Documento\n")
    
    for tipo, tipo_stats in sorted(stats['documenti_per_tipo'].items()):
        output_lines.insert(11, f"- **{tipo}**: {tipo_stats['totale']} docs, ")
        output_lines.insert(12, f"{tipo_stats['caratteri']:,} caratteri, ")
        output_lines.insert(13, f"{tipo_stats['parole']:,} parole\n")
    
    output_lines.insert(14, "\n---\n")
    
    # Salva file
    output_file = Path(__file__).parent / 'TESTI_ESTRATTI_OCR_COMPLETI.md'
    
    print(f"\n{'='*80}")
    print(f"💾 Salvataggio output...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    print(f"✅ File salvato: {output_file}")
    print(f"   Dimensione: {os.path.getsize(output_file) / 1024:.2f} KB")
    
    print(f"\n{'='*80}")
    print("📊 RIEPILOGO FINALE")
    print(f"{'='*80}")
    print(f"Documenti processati: {stats['totale_documenti']}")
    print(f"Caratteri totali: {stats['totale_caratteri']:,}")
    print(f"Parole totali: {stats['totale_parole']:,}")
    print(f"Errori OCR: {stats['errori_ocr']}")
    print(f"\nMetodi OCR:")
    for method, count in stats['metodi_ocr'].items():
        print(f"  - {method}: {count} documenti")
    print(f"\nDocumenti per tipo:")
    for tipo, tipo_stats in sorted(stats['documenti_per_tipo'].items()):
        print(f"  - {tipo}: {tipo_stats['totale']} docs")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    extract_all_training_documents()
