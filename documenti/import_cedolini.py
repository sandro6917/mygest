"""
Logica business per l'importazione di cedolini paga.

Gestisce:
- Estrazione file ZIP
- Parsing cedolini (nome file + contenuto PDF)
- Creazione/ricerca anagrafica dipendente e cliente azienda
- Creazione fascicolo paghe
- Creazione documento con attributi dinamici
"""
from __future__ import annotations
import logging
import zipfile
from io import BytesIO
from typing import Dict, List, Any, Tuple, Optional
from datetime import date
from django.db import transaction
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from anagrafiche.models import Anagrafica, Cliente
from anagrafiche.utils import get_or_generate_cli  # Generazione codice anagrafica
from fascicoli.models import Fascicolo
from titolario.models import TitolarioVoce
from documenti.models import Documento, DocumentiTipo, AttributoValore, AttributoDefinizione
from documenti.utils_cedolini import (
    parse_filename_cedolino,
    extract_pdf_data,
    identifica_mensilita,
    calcola_ultimo_giorno_mese,
    genera_titolo_fascicolo,
    genera_descrizione_documento,
    parse_data_italiana,
    genera_note_documento,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class CedolinoImporter:
    """Classe per gestire l'importazione di cedolini paga"""
    
    def __init__(self, zip_file, user=None, duplicate_policy='skip'):
        """
        Inizializza l'importer.
        
        Args:
            zip_file: File ZIP caricato
            user: Utente che richiede l'import (opzionale)
            duplicate_policy: Gestione duplicati ('skip', 'replace', 'add')
                - 'skip': Non importare se documento già esiste
                - 'replace': Sostituire documento esistente
                - 'add': Aggiungere comunque il documento (crea duplicato)
        """
        self.zip_file = zip_file
        self.user = user
        self.duplicate_policy = duplicate_policy
        self.tipo_bpag = None
        self.voce_pag = None
        self.risultati = {
            'created': 0,
            'replaced': 0,
            'skipped': 0,
            'errors': [],
            'documenti': [],
            'warnings': [],
        }
    
    def importa(self) -> Dict[str, Any]:
        """
        Esegue l'importazione completa.
        
        Returns:
            Dict con risultati: created, errors, documenti, warnings
        """
        logger.info(f"Inizio importazione cedolini da {self.zip_file.name}")
        
        try:
            # Carica tipo documento BPAG
            self.tipo_bpag = DocumentiTipo.objects.get(codice='BPAG')
            
            # Carica voce titolario PAG con ID 107 (obbligatorio)
            self.voce_pag = TitolarioVoce.objects.get(id=107)
            
        except DocumentiTipo.DoesNotExist:
            error_msg = "Tipo documento BPAG mancante. Eseguire: python manage.py setup_cedolini"
            logger.error(error_msg)
            self.risultati['errors'].append(error_msg)
            return self.risultati
        except TitolarioVoce.DoesNotExist:
            error_msg = "Voce titolario PAG (ID 107) non trovata"
            logger.error(error_msg)
            self.risultati['errors'].append(error_msg)
            return self.risultati
        
        # Estrai e processa file dal ZIP
        try:
            with zipfile.ZipFile(BytesIO(self.zip_file.read()), 'r') as zip_ref:
                pdf_files = [f for f in zip_ref.namelist() if f.endswith('.pdf')]
                total_files = len(pdf_files)
                
                logger.info(f"Trovati {total_files} file PDF nel ZIP")
                self.risultati['total'] = total_files  # Aggiungi totale
                
                for pdf_filename in pdf_files:
                    try:
                        pdf_content = zip_ref.read(pdf_filename)
                        self._processa_cedolino(pdf_filename, pdf_content)
                    except Exception as e:
                        error_msg = f"Errore processando {pdf_filename}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        # Errore dettagliato con filename
                        self.risultati['errors'].append({
                            'filename': pdf_filename,
                            'error': str(e)
                        })
        
        except zipfile.BadZipFile:
            error_msg = "File ZIP non valido o corrotto"
            logger.error(error_msg)
            self.risultati['errors'].append({
                'filename': self.zip_file.name,
                'error': error_msg
            })
        except Exception as e:
            error_msg = f"Errore durante l'estrazione del ZIP: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.risultati['errors'].append({
                'filename': self.zip_file.name,
                'error': error_msg
            })
        
        # Log finale dettagliato
        logger.info(
            f"Importazione completata: {self.risultati['created']}/{self.risultati.get('total', 0)} "
            f"documenti creati, {len(self.risultati['errors'])} errori"
        )
        
        return self.risultati
    
    def _processa_cedolino(self, filename: str, pdf_content: bytes):
        """
        Processa un singolo cedolino.
        
        Args:
            filename: Nome file PDF
            pdf_content: Contenuto binario PDF
        """
        logger.info(f"Processando cedolino: {filename}")
        
        # 1. Parse nome file
        file_data = parse_filename_cedolino(filename)
        if not file_data:
            error_msg = f"Nome file non valido: {filename}"
            logger.warning(error_msg)
            self.risultati['errors'].append(error_msg)
            return
        
        # 2. Estrai dati dal PDF
        pdf_data = extract_pdf_data(pdf_content)
        
        # Verifica dati essenziali
        if not pdf_data.get('azienda_cf'):
            error_msg = f"CF azienda non trovato nel PDF: {filename}"
            logger.warning(error_msg)
            self.risultati['errors'].append({
                'filename': filename,
                'error': error_msg
            })
            return
        
        # 3. Identifica mensilità
        mensilita = identifica_mensilita(pdf_data.get('periodo'), pdf_data.get('raw_text', ''))
        
        # 4. Calcola data documento (ultimo giorno del mese)
        anno = pdf_data.get('anno') or int(file_data['anno'])
        mese = pdf_data.get('mese') or mensilita
        if mese > 12:  # Tredicesima/quattordicesima -> dicembre
            mese = 12
        data_doc = calcola_ultimo_giorno_mese(anno, mese)
        
        try:
            with transaction.atomic():
                # 5. Crea/trova anagrafica dipendente
                dipendente = self._crea_o_trova_anagrafica_dipendente(file_data, pdf_data)
                
                # 6. Crea/trova cliente azienda
                cliente = self._crea_o_trova_cliente_azienda(pdf_data)
                
                # 7. Crea/trova fascicolo paghe
                fascicolo = self._crea_o_trova_fascicolo_paghe(cliente, anno, mese)
                
                # 8. Genera descrizione
                descrizione = genera_descrizione_documento(
                    file_data['cognome'],
                    file_data['nome'],
                    pdf_data.get('periodo', f"{mese}/{anno}")
                )
                
                # 9. Genera note
                note = genera_note_documento(file_data, pdf_data)
                
                # 10. Controlla se esiste già un documento per questo dipendente/periodo
                existing_doc = self._trova_documento_esistente(cliente, dipendente, anno, mese, mensilita)
                
                if existing_doc:
                    if self.duplicate_policy == 'skip':
                        logger.info(f"Documento già esistente: {existing_doc.codice} - SALTATO")
                        self.risultati['skipped'] += 1
                        self.risultati['warnings'].append({
                            'filename': filename,
                            'message': f'Documento già esistente: {existing_doc.codice}',
                            'action': 'skipped'
                        })
                        return  # Salta questo documento
                    
                    elif self.duplicate_policy == 'replace':
                        logger.info(f"Documento già esistente: {existing_doc.codice} - SOSTITUZIONE")
                        # Elimina il vecchio file se presente
                        if existing_doc.file:
                            try:
                                existing_doc.file.delete(save=False)
                            except Exception as e:
                                logger.warning(f"Errore eliminando vecchio file: {e}")
                        
                        # Aggiorna il documento esistente
                        existing_doc.descrizione = descrizione
                        existing_doc.data_documento = data_doc
                        existing_doc.note = note
                        existing_doc.file.save(filename, ContentFile(pdf_content), save=False)
                        existing_doc.save()
                        
                        # Aggiorna attributi
                        self._salva_attributi(existing_doc, file_data, pdf_data, dipendente, anno, mese, mensilita)
                        
                        self.risultati['replaced'] += 1
                        self.risultati['documenti'].append({
                            'id': existing_doc.id,
                            'codice': existing_doc.codice,
                            'descrizione': existing_doc.descrizione,
                            'filename': filename,
                            'action': 'replaced'
                        })
                        
                        logger.info(f"Documento sostituito: {existing_doc.codice} (ID: {existing_doc.id})")
                        return  # Documento sostituito, non crearne uno nuovo
                    
                    # else: duplicate_policy == 'add' → procedi con creazione normale
                
                # 11. Crea documento
                documento = Documento(
                    tipo=self.tipo_bpag,
                    cliente=cliente,
                    fascicolo=fascicolo,
                    titolario_voce=self.voce_pag,
                    descrizione=descrizione,
                    data_documento=data_doc,
                    stato=Documento.Stato.DEFINITIVO,
                    digitale=True,
                    tracciabile=True,
                    note=note,
                )
                
                # Salva file PDF
                documento.file.save(filename, ContentFile(pdf_content), save=False)
                documento.save()
                
                # 12. Salva attributi dinamici
                self._salva_attributi(documento, file_data, pdf_data, dipendente, anno, mese, mensilita)
                
                # 13. Rigenera codice se il pattern usa attributi dinamici
                # Controlla se il pattern_codice contiene {ATTR:...}
                pattern = self.voce_pag.pattern_codice if self.voce_pag else ""
                if '{ATTR:' in pattern:
                    logger.info(f"Pattern codice usa attributi dinamici: rigenerazione codice per {documento.id}")
                    documento.rigenera_codice_con_attributi()
                
                # Aggiungi ai risultati
                self.risultati['created'] += 1
                self.risultati['documenti'].append({
                    'id': documento.id,
                    'codice': documento.codice,
                    'descrizione': documento.descrizione,
                    'filename': filename,
                })
                
                logger.info(f"Documento creato: {documento.codice} (ID: {documento.id})")
        
        except Exception as e:
            error_msg = f"{str(e)}"
            logger.error(f"Errore creando documento per {filename}: {error_msg}", exc_info=True)
            self.risultati['errors'].append({
                'filename': filename,
                'error': error_msg
            })
    
    def _trova_documento_esistente(
        self,
        cliente: Cliente,
        dipendente: Anagrafica,
        anno: int,
        mese: int,
        mensilita: str
    ) -> Optional[Documento]:
        """
        Cerca un documento esistente per lo stesso dipendente/periodo.
        
        Criteri di ricerca:
        - Stesso tipo (BPAG)
        - Stesso cliente
        - Stesso anno
        - Attributo 'dipendente' uguale
        - Attributo 'mese_riferimento' uguale
        - Attributo 'mensilita' uguale
        
        Returns:
            Documento esistente o None
        """
        from django.db.models import Q
        
        # Trova attributi definizione
        try:
            attr_def_dipendente = AttributoDefinizione.objects.get(
                tipo_documento=self.tipo_bpag,
                codice='dipendente'
            )
            attr_def_mese = AttributoDefinizione.objects.get(
                tipo_documento=self.tipo_bpag,
                codice='mese_riferimento'
            )
            attr_def_mensilita = AttributoDefinizione.objects.get(
                tipo_documento=self.tipo_bpag,
                codice='mensilita'
            )
        except AttributoDefinizione.DoesNotExist as e:
            logger.warning(f"Attributo definizione mancante: {e}")
            return None
        
        # Cerca documenti dello stesso anno e cliente
        documenti_candidati = Documento.objects.filter(
            tipo=self.tipo_bpag,
            cliente=cliente,
            data_documento__year=anno
        ).prefetch_related('attributi')
        
        # Filtra per attributi specifici
        for doc in documenti_candidati:
            attributi = {av.definizione_id: av.valore for av in doc.attributi.all()}
            
            # Verifica dipendente (ID anagrafica)
            if attributi.get(attr_def_dipendente.id) != str(dipendente.id):
                continue
            
            # Verifica mese
            if attributi.get(attr_def_mese.id) != str(mese):
                continue
            
            # Verifica mensilita
            if attributi.get(attr_def_mensilita.id) != mensilita:
                continue
            
            # Trovato match!
            logger.info(
                f"Trovato documento esistente: {doc.codice} "
                f"(dipendente={dipendente.codice}, anno={anno}, mese={mese}, mensilità={mensilita})"
            )
            return doc
        
        return None
    
    def _crea_o_trova_anagrafica_dipendente(
        self, 
        file_data: Dict[str, str], 
        pdf_data: Dict[str, Any]
    ) -> Anagrafica:
        """Crea o trova l'anagrafica del dipendente"""
        cf = file_data['codice_fiscale']
        
        # Cerca anagrafica esistente
        anagrafica = Anagrafica.objects.filter(codice_fiscale=cf).first()
        
        if anagrafica:
            # Se esiste ma non ha codice, generalo
            if not anagrafica.codice:
                logger.info(
                    f"📌 TROVATA anagrafica esistente SENZA codice: {anagrafica.nome} {anagrafica.cognome} "
                    f"(CF: {cf}) - Genero codice..."
                )
                codice_generato = get_or_generate_cli(anagrafica)
                anagrafica.refresh_from_db()
                logger.info(f"   ✅ Codice generato: {anagrafica.codice} (risultato funzione: {codice_generato})")
            else:
                logger.info(
                    f"📌 TROVATA anagrafica esistente: {anagrafica.nome} {anagrafica.cognome} "
                    f"(CF: {cf}, Codice: {anagrafica.codice})"
                )
        
        if not anagrafica:
            # Crea nuova anagrafica
            tipo = 'PF'  # Dipendente è sempre persona fisica
            
            anagrafica = Anagrafica(
                tipo=tipo,
                codice_fiscale=cf,
                nome=file_data['nome'],
                cognome=file_data['cognome'],
            )
            
            # Aggiungi dati extra se disponibili
            if pdf_data.get('data_nascita'):
                anagrafica.data_nascita = parse_data_italiana(pdf_data['data_nascita'])
            
            anagrafica.save()
            
            # Genera codice CLI (la funzione gestisce automaticamente save e retry)
            codice_generato = get_or_generate_cli(anagrafica)
            
            # FORZA refresh per essere sicuri che il codice sia aggiornato
            anagrafica.refresh_from_db()
            
            logger.info(
                f"Creata anagrafica dipendente: {anagrafica.nome} {anagrafica.cognome} "
                f"(CF: {cf}, Codice: {anagrafica.codice}, Generato: {codice_generato})"
            )
        
        return anagrafica
    
    def _crea_o_trova_cliente_azienda(self, pdf_data: Dict[str, Any]) -> Cliente:
        """Crea o trova il cliente azienda datore di lavoro"""
        cf_azienda = pdf_data.get('azienda_cf')
        
        if not cf_azienda:
            # Fallback: usa cliente di default o solleva errore
            logger.warning("Codice fiscale azienda non trovato nel PDF")
            # Qui potresti creare un cliente "VARIE" oppure sollevare un'eccezione
            raise ValueError("Impossibile identificare l'azienda dal cedolino")
        
        # Cerca cliente esistente tramite anagrafica
        anagrafica_azienda = Anagrafica.objects.filter(codice_fiscale=cf_azienda).first()
        
        if anagrafica_azienda:
            # Trova il cliente associato
            cliente = Cliente.objects.filter(anagrafica=anagrafica_azienda).first()
            if cliente:
                return cliente
        
        # Crea nuova anagrafica + cliente
        tipo = 'PG' if len(cf_azienda) == 11 else 'PF'
        
        if not anagrafica_azienda:
            anagrafica_azienda = Anagrafica(
                tipo=tipo,
                codice_fiscale=cf_azienda,
            )
            
            if tipo == 'PG':
                # Persona Giuridica
                anagrafica_azienda.denominazione = pdf_data.get('azienda_ragione_sociale', 'Azienda')
            else:
                # Persona Fisica (caso raro per azienda)
                # Parsing nome/cognome dalla ragione sociale (fallback)
                rag_soc = pdf_data.get('azienda_ragione_sociale', '')
                parts = rag_soc.split()
                if len(parts) >= 2:
                    anagrafica_azienda.nome = parts[0]
                    anagrafica_azienda.cognome = ' '.join(parts[1:])
                else:
                    anagrafica_azienda.cognome = rag_soc or 'Azienda'
            
            anagrafica_azienda.save()
            logger.info(f"Creata anagrafica azienda: {anagrafica_azienda} (CF: {cf_azienda})")
        
        # Crea cliente
        cliente = Cliente.objects.create(anagrafica=anagrafica_azienda)
        logger.info(f"Creato cliente azienda: {cliente}")
        
        return cliente
    
    def _crea_o_trova_fascicolo_paghe(
        self, 
        cliente: Cliente, 
        anno: int, 
        mese: int
    ) -> Fascicolo:
        """Crea o trova il fascicolo paghe per il cliente, anno e mese"""
        titolo = genera_titolo_fascicolo(mese, anno)
        
        # Cerca fascicolo esistente per cliente, anno, mese e titolario PAG
        # Usa icontains per gestire variazioni nel titolo ("Paghe Dicembre" vs "Buste paga dicembre")
        fascicolo = Fascicolo.objects.filter(
            cliente=cliente,
            anno=anno,
            titolario_voce=self.voce_pag,
            titolo__icontains=f"dicembre {anno}" if mese == 12 else 
                             f"gennaio {anno}" if mese == 1 else
                             f"febbraio {anno}" if mese == 2 else
                             f"marzo {anno}" if mese == 3 else
                             f"aprile {anno}" if mese == 4 else
                             f"maggio {anno}" if mese == 5 else
                             f"giugno {anno}" if mese == 6 else
                             f"luglio {anno}" if mese == 7 else
                             f"agosto {anno}" if mese == 8 else
                             f"settembre {anno}" if mese == 9 else
                             f"ottobre {anno}" if mese == 10 else
                             f"novembre {anno}" if mese == 11 else
                             f"{mese} {anno}"
        ).first()
        
        if not fascicolo:
            # Crea nuovo fascicolo solo se non esiste
            fascicolo = Fascicolo(
                cliente=cliente,
                titolario_voce=self.voce_pag,
                titolo=titolo,
                anno=anno,
                ubicazione=None,  # Fascicolo digitale (nessuna ubicazione fisica)
            )
            fascicolo.save()
            logger.info(f"Creato fascicolo: {fascicolo.titolo} (ID: {fascicolo.id}, Codice: {fascicolo.codice})")
        else:
            logger.info(f"Trovato fascicolo esistente: {fascicolo.titolo} (ID: {fascicolo.id}, Codice: {fascicolo.codice})")
        
        return fascicolo
    
    def _salva_attributi(
        self,
        documento: Documento,
        file_data: Dict[str, str],
        pdf_data: Dict[str, Any],
        dipendente: Anagrafica,
        anno: int,
        mese: int,
        mensilita: int
    ):
        """Salva gli attributi dinamici del documento BPAG"""
        # Carica definizioni attributi
        attributi_def = {
            attr.codice: attr
            for attr in AttributoDefinizione.objects.filter(tipo_documento=self.tipo_bpag)
        }
        
        # Valori attributi
        valori = {
            'tipo': 'Libro Unico',
            'anno_riferimento': anno,
            'mese_riferimento': mese,
            'mensilita': mensilita,
            'dipendente': dipendente.id,  # ID anagrafica
        }
        
        # Salva ogni attributo
        for codice, valore in valori.items():
            if codice in attributi_def:
                AttributoValore.objects.create(
                    documento=documento,
                    definizione=attributi_def[codice],
                    valore=valore
                )
        
        logger.debug(f"Salvati {len(valori)} attributi per documento {documento.codice}")
