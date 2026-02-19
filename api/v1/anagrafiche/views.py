"""
ViewSets per API Anagrafiche
"""
import csv
from io import BytesIO, StringIO
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from django.core.exceptions import ValidationError

from anagrafiche.models import Anagrafica, Cliente, ClientiTipo, Indirizzo, EmailContatto
from anagrafiche.models_comuni import ComuneItaliano
from .serializers import (
    AnagraficaListSerializer,
    AnagraficaDetailSerializer,
    AnagraficaCreateUpdateSerializer,
    ClienteSerializer,
    ClientiTipoSerializer,
    IndirizzoSerializer,
    EmailContattoSerializer,
    ComuneItalianoSerializer,
)


class AnagraficaViewSet(viewsets.ModelViewSet):
    """
    ViewSet per CRUD Anagrafiche
    
    list: GET /api/v1/anagrafiche/
    retrieve: GET /api/v1/anagrafiche/{id}/
    create: POST /api/v1/anagrafiche/
    update: PUT /api/v1/anagrafiche/{id}/
    partial_update: PATCH /api/v1/anagrafiche/{id}/
    destroy: DELETE /api/v1/anagrafiche/{id}/
    """
    permission_classes = [IsAuthenticated]
    queryset = Anagrafica.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ragione_sociale', 'nome', 'cognome', 'codice_fiscale', 'partita_iva', 'email', 'pec']
    filterset_fields = ['tipo']
    ordering_fields = ['created_at', 'updated_at', 'ragione_sociale', 'cognome', 'tipo', 'codice_fiscale', 'partita_iva']
    ordering = []  # Nessun default, verrà gestito in get_queryset
    
    def get_serializer_class(self):
        """Usa serializer diversi per azioni diverse"""
        if self.action == 'list':
            return AnagraficaListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AnagraficaCreateUpdateSerializer
        return AnagraficaDetailSerializer
    
    def get_queryset(self):
        """Filtra queryset in base ai parametri"""
        from django.db.models import Case, When, Value, CharField
        from django.db.models.functions import Concat
        
        queryset = super().get_queryset()
        
        # Filtro per clienti
        is_cliente = self.request.query_params.get('is_cliente')
        if is_cliente == 'true':
            queryset = queryset.filter(cliente__isnull=False)
        elif is_cliente == 'false':
            queryset = queryset.filter(cliente__isnull=True)
        
        # Filtro per tipo_cliente
        tipo_cliente = self.request.query_params.get('tipo_cliente')
        if tipo_cliente:
            queryset = queryset.filter(cliente__tipo_cliente_id=tipo_cliente)
        
        # Ordinamento custom per "nominativo"
        ordering = self.request.query_params.get('ordering', 'nominativo')  # Default: nominativo
        
        if 'nominativo' in ordering:
            # Crea campo virtuale per ordinamento: PG usa ragione_sociale, PF usa cognome+nome
            queryset = queryset.annotate(
                nominativo_sort=Case(
                    When(tipo='PG', then='ragione_sociale'),
                    When(tipo='PF', then=Concat('cognome', Value(' '), 'nome')),
                    output_field=CharField()
                )
            )
            # Applica ordinamento
            if ordering.startswith('-'):
                queryset = queryset.order_by('-nominativo_sort')
            else:
                queryset = queryset.order_by('nominativo_sort')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def clienti(self, request):
        """Lista solo clienti"""
        clienti = self.get_queryset().filter(cliente__isnull=False)
        page = self.paginate_queryset(clienti)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def make_cliente(self, request, pk=None):
        """Trasforma anagrafica in cliente"""
        anagrafica = self.get_object()
        
        if hasattr(anagrafica, 'cliente'):
            return Response(
                {'detail': 'Già cliente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        Cliente.objects.create(anagrafica=anagrafica)
        serializer = self.get_serializer(anagrafica)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ricalcola_codice(self, request, pk=None):
        """
        Ricalcola il codice anagrafica.
        IMPORTANTE: Il codice è un identificatore univoco che NON deve cambiare
        se è già ben formato, anche se la ragione sociale o il nome cambiano.
        
        Rigenera SOLO se:
        - Il codice non esiste (NULL)
        - È in vecchio formato (es. CLI00073 con cifre nei primi 6 caratteri)
        - È malformato (lunghezza != 8 o formato invalido)
        
        Formato corretto: 6 LETTERE + 2 CIFRE (es. ABCNUO01, BOCMAR01)
        """
        from anagrafiche.utils import get_or_generate_cli
        
        anagrafica = self.get_object()
        old_code = anagrafica.codice
        
        # Verifica se il codice esistente è ben formato
        if old_code:
            # Formato corretto: 8 caratteri (6 LETTERE + 2 cifre)
            is_well_formed = (
                len(old_code) == 8 and
                old_code[:6].isalpha() and  # Prime 6: solo LETTERE (no cifre)
                old_code[6:].isdigit()      # Ultime 2: solo CIFRE
            )
            
            if is_well_formed:
                # Codice ben formato: NON modificare, è l'indice stabile dell'anagrafica
                serializer = self.get_serializer(anagrafica)
                return Response({
                    'old_code': old_code,
                    'new_code': old_code,
                    'unchanged': True,
                    'message': 'Codice ben formato mantenuto (indice stabile)',
                    'anagrafica': serializer.data
                })
        
        # Se arriviamo qui: codice assente, vecchio formato o malformato
        # Forziamo la rigenerazione
        anagrafica.codice = None
        new_code = get_or_generate_cli(anagrafica)
        
        serializer = self.get_serializer(anagrafica)
        return Response({
            'old_code': old_code,
            'new_code': new_code,
            'unchanged': False,
            'anagrafica': serializer.data
        })
    
    # ===== INDIRIZZI =====
    @action(detail=True, methods=['get', 'post'], url_path='indirizzi')
    def manage_indirizzi(self, request, pk=None):
        """Lista (GET) o crea (POST) indirizzi dell'anagrafica"""
        anagrafica = self.get_object()
        
        if request.method == 'GET':
            indirizzi = anagrafica.indirizzi.all()
            serializer = IndirizzoSerializer(indirizzi, many=True)
            return Response(serializer.data)
        
        else:  # POST
            serializer = IndirizzoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(anagrafica=anagrafica)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'put', 'patch', 'delete'], url_path='indirizzi/(?P<indirizzo_id>[^/.]+)')
    def manage_indirizzo_detail(self, request, pk=None, indirizzo_id=None):
        """Ottieni (GET), aggiorna (PUT/PATCH) o elimina (DELETE) un indirizzo specifico"""
        anagrafica = self.get_object()
        
        try:
            indirizzo = anagrafica.indirizzi.get(pk=indirizzo_id)
        except Indirizzo.DoesNotExist:
            return Response({'detail': 'Indirizzo non trovato'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = IndirizzoSerializer(indirizzo)
            return Response(serializer.data)
        
        elif request.method == 'DELETE':
            indirizzo.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        else:  # PUT or PATCH
            partial = request.method == 'PATCH'
            serializer = IndirizzoSerializer(indirizzo, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # ===== CONTATTI EMAIL =====
    @action(detail=True, methods=['get', 'post'], url_path='contatti-email')
    def manage_contatti_email(self, request, pk=None):
        """Lista (GET) o crea (POST) contatti email dell'anagrafica"""
        anagrafica = self.get_object()
        
        if request.method == 'GET':
            contatti = anagrafica.contatti_email.all()
            serializer = EmailContattoSerializer(contatti, many=True)
            return Response(serializer.data)
        
        else:  # POST
            serializer = EmailContattoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(anagrafica=anagrafica)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'put', 'patch', 'delete'], url_path='contatti-email/(?P<contatto_id>[^/.]+)')
    def manage_contatto_email_detail(self, request, pk=None, contatto_id=None):
        """Ottieni (GET), aggiorna (PUT/PATCH) o elimina (DELETE) un contatto email specifico"""
        anagrafica = self.get_object()
        
        try:
            contatto = anagrafica.contatti_email.get(pk=contatto_id)
        except EmailContatto.DoesNotExist:
            return Response({'detail': 'Contatto non trovato'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = EmailContattoSerializer(contatto)
            return Response(serializer.data)
        
        elif request.method == 'DELETE':
            contatto.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        else:  # PUT or PATCH
            partial = request.method == 'PATCH'
            serializer = EmailContattoSerializer(contatto, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Esporta anagrafiche filtrate in CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Crea CSV in memoria
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Tipo',
            'Ragione Sociale / Nome Cognome',
            'Codice Fiscale',
            'Partita IVA',
            'Codice',
            'Email',
            'PEC',
            'Telefono',
            'Indirizzo',
            'Cliente',
            'Tipo Cliente',
            'Data Creazione'
        ])
        
        # Dati
        for ana in queryset:
            display_name = ana.ragione_sociale if ana.tipo == 'PG' else f"{ana.cognome} {ana.nome}"
            is_cliente = 'Sì' if hasattr(ana, 'cliente') else 'No'
            tipo_cliente = ''
            if hasattr(ana, 'cliente') and ana.cliente.tipo_cliente:
                tipo_cliente = ana.cliente.tipo_cliente.descrizione
            
            writer.writerow([
                ana.get_tipo_display(),
                display_name,
                ana.codice_fiscale,
                ana.partita_iva or '',
                ana.codice or '',
                ana.email or '',
                ana.pec or '',
                ana.telefono or '',
                ana.indirizzo or '',
                is_cliente,
                tipo_cliente,
                ana.created_at.strftime('%d/%m/%Y %H:%M')
            ])
        
        # Prepara response
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="anagrafiche_export.csv"'
        response.write('\ufeff')  # BOM per Excel
        return response
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Stampa PDF anagrafiche filtrate (LS_ANAG)"""
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from datetime import datetime
        
        # Ottieni queryset filtrato
        queryset = self.filter_queryset(self.get_queryset())
        
        # Genera PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                               topMargin=1.5*cm, bottomMargin=1.5*cm,
                               leftMargin=1.5*cm, rightMargin=1.5*cm)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titolo
        title_text = f"Elenco Anagrafiche - {datetime.now().strftime('%d/%m/%Y')}"
        elements.append(Paragraph(title_text, styles['Title']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Info filtri applicati
        filter_info = []
        if request.GET.get('search'):
            filter_info.append(f"Ricerca: {request.GET.get('search')}")
        if request.GET.get('tipo'):
            tipo_display = 'Persona Fisica' if request.GET.get('tipo') == 'PF' else 'Persona Giuridica'
            filter_info.append(f"Tipo: {tipo_display}")
        if request.GET.get('is_cliente'):
            filter_info.append(f"Solo Clienti: {'Sì' if request.GET.get('is_cliente') == 'true' else 'No'}")
        
        if filter_info:
            filter_text = "Filtri: " + " | ".join(filter_info)
            elements.append(Paragraph(filter_text, styles['Normal']))
            elements.append(Spacer(1, 0.3*cm))
        
        elements.append(Paragraph(f"Totale record: {queryset.count()}", styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabella dati
        data = [['Tipo', 'Denominazione', 'Codice Fiscale', 'P.IVA', 'Email/PEC', 'Tel.', 'Cliente']]
        
        for ana in queryset[:200]:  # Limita a 200 per performance
            display_name = ana.ragione_sociale if ana.tipo == 'PG' else f"{ana.cognome} {ana.nome}"
            is_cliente = '✓' if hasattr(ana, 'cliente') else '-'
            email_pec = ana.pec or ana.email or '-'
            
            data.append([
                ana.get_tipo_display()[:2],  # PF/PG
                display_name[:35],
                ana.codice_fiscale[:16],
                (ana.partita_iva or '-')[:11],
                email_pec[:25],
                (ana.telefono or '-')[:15],
                is_cliente
            ])
        
        # Crea tabella con stile
        table = Table(data, colWidths=[1.5*cm, 6*cm, 4*cm, 3*cm, 5.5*cm, 3*cm, 1.5*cm])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00008B')),  # DarkBlue
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Tipo centrato
            ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),  # Cliente centrato
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Footer
        if queryset.count() > 200:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(
                f"<i>Nota: Visualizzati primi 200 record di {queryset.count()} totali</i>",
                styles['Normal']
            ))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(
            buffer,
            filename=f'elenco_anagrafiche_{datetime.now().strftime("%Y%m%d")}.pdf',
            content_type='application/pdf'
        )
    
    @action(detail=False, methods=['get'])
    def facsimile_csv(self, request):
        """
        Genera e scarica un file CSV di esempio per l'importazione anagrafiche.
        Include tutti i campi disponibili con esempi per PF e PG.
        """
        header = [
            "tipo", 
            "ragione_sociale", 
            "nome", 
            "cognome", 
            "codice_fiscale",
            "partita_iva", 
            "codice", 
            "denominazione_abbreviata",
            "pec", 
            "email", 
            "telefono", 
            "indirizzo", 
            "note"
        ]
        
        examples = [
            # Persona Fisica - esempio 1
            [
                "PF", "", "Mario", "Rossi", "RSSMRA80A01H501U", "", "CLI0001", "ROSSI MARIO",
                "mario.rossi@pec.it", "mario.rossi@email.it", "3331234567", 
                "Via Roma 1, 20121 Milano", "Cliente preferenziale"
            ],
            # Persona Fisica - esempio 2
            [
                "PF", "", "Anna", "Verdi", "VRDNNA85M45F205X", "", "", "",
                "anna.verdi@pec.example.it", "anna@example.com", "+39 02 12345678",
                "Corso Italia 45, 00100 Roma", ""
            ],
            # Persona Giuridica - esempio 1
            [
                "PG", "Acme S.r.l.", "", "", "12345678901", "12345678901", "CLI0002", "ACME SRL",
                "acme@pec.it", "info@acme.it", "024567890", 
                "Via Milano 10, 20100 Milano", "Cliente importante - fatturazione elettronica"
            ],
            # Persona Giuridica - esempio 2
            [
                "PG", "Beta Solutions S.p.A.", "", "", "98765432109", "98765432109", "", "BETA SPA",
                "beta@pec.example.com", "contatti@beta.com", "+39 06 9876543",
                "Piazza Duomo 1, 50100 Firenze", "Partner tecnologico"
            ],
        ]
        
        output = StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(header)
        for row in examples:
            writer.writerow(row)
        
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="facsimile_anagrafiche.csv"'
        response.write('\ufeff')  # BOM per UTF-8
        return response
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_csv(self, request):
        """
        Importa anagrafiche da file CSV.
        
        POST /api/v1/anagrafiche/import_csv/
        Content-Type: multipart/form-data
        Body: file (CSV file)
        
        Returns: {
            "totale": int,
            "importate": [{ "riga": int, "nome": str, "codice_fiscale": str, "id": int }],
            "scartate": [{ "riga": int, "dati": str, "motivi": [str] }],
            "num_importate": int,
            "num_scartate": int
        }
        """
        csv_file = request.FILES.get('file')
        
        if not csv_file:
            return Response(
                {'error': 'Nessun file fornito'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Decodifica del file CSV
        try:
            decoded_file = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            csv_file.seek(0)
            try:
                decoded_file = csv_file.read().decode('latin-1')
            except:
                return Response(
                    {'error': 'Encoding file non supportato. Usa UTF-8 o Latin-1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Gestione BOM e preparazione reader
        decoded_file = decoded_file.lstrip('\ufeff')
        reader = csv.DictReader(StringIO(decoded_file), delimiter=';')
        
        # Contatori e report
        importate = []
        scartate = []
        riga_numero = 1  # Inizia da 1 per l'header
        
        for row in reader:
            riga_numero += 1
            errori_riga = []
            
            try:
                # Validazione campi obbligatori
                tipo = row.get("tipo", "").strip().upper()
                codice_fiscale = row.get("codice_fiscale", "").strip().upper()
                
                if not tipo:
                    errori_riga.append("Campo 'tipo' mancante")
                elif tipo not in ["PF", "PG"]:
                    errori_riga.append(f"Tipo '{tipo}' non valido (deve essere PF o PG)")
                
                if not codice_fiscale:
                    errori_riga.append("Campo 'codice_fiscale' mancante")
                
                # Validazione specifica per tipo
                nome = row.get("nome", "").strip()
                cognome = row.get("cognome", "").strip()
                ragione_sociale = row.get("ragione_sociale", "").strip()
                
                if tipo == "PF":
                    if not nome:
                        errori_riga.append("Campo 'nome' obbligatorio per Persona Fisica")
                    if not cognome:
                        errori_riga.append("Campo 'cognome' obbligatorio per Persona Fisica")
                elif tipo == "PG":
                    if not ragione_sociale:
                        errori_riga.append("Campo 'ragione_sociale' obbligatorio per Persona Giuridica")
                
                # Se ci sono errori di validazione base, scarta la riga
                if errori_riga:
                    scartate.append({
                        "riga": riga_numero,
                        "dati": f"{cognome} {nome}".strip() or ragione_sociale or codice_fiscale,
                        "motivi": errori_riga
                    })
                    continue
                
                # Verifica duplicati per codice fiscale
                if Anagrafica.objects.filter(codice_fiscale=codice_fiscale).exists():
                    scartate.append({
                        "riga": riga_numero,
                        "dati": f"{cognome} {nome}".strip() or ragione_sociale,
                        "motivi": [f"Codice fiscale '{codice_fiscale}' già presente nel database"]
                    })
                    continue
                
                # Preparazione campi opzionali
                partita_iva = row.get("partita_iva", "").strip()
                codice = row.get("codice", "").strip() or None
                pec = row.get("pec", "").strip()
                email = row.get("email", "").strip()
                telefono = row.get("telefono", "").strip()
                indirizzo = row.get("indirizzo", "").strip()
                note = row.get("note", "").strip()
                denominazione_abbreviata = row.get("denominazione_abbreviata", "").strip()
                
                # Verifica duplicati per P.IVA se presente
                if partita_iva and Anagrafica.objects.filter(partita_iva=partita_iva).exists():
                    scartate.append({
                        "riga": riga_numero,
                        "dati": f"{cognome} {nome}".strip() or ragione_sociale,
                        "motivi": [f"Partita IVA '{partita_iva}' già presente nel database"]
                    })
                    continue
                
                # Verifica duplicati per PEC se presente
                if pec and Anagrafica.objects.filter(pec=pec).exists():
                    scartate.append({
                        "riga": riga_numero,
                        "dati": f"{cognome} {nome}".strip() or ragione_sociale,
                        "motivi": [f"PEC '{pec}' già presente nel database"]
                    })
                    continue
                
                # Creazione anagrafica con validazione
                anagrafica = Anagrafica(
                    tipo=tipo,
                    ragione_sociale=ragione_sociale if tipo == "PG" else "",
                    nome=nome if tipo == "PF" else "",
                    cognome=cognome if tipo == "PF" else "",
                    codice_fiscale=codice_fiscale,
                    partita_iva=partita_iva,
                    codice=codice,
                    pec=pec,
                    email=email,
                    telefono=telefono,
                    indirizzo=indirizzo,
                    note=note,
                    denominazione_abbreviata=denominazione_abbreviata,
                )
                
                # Validazione model (clean())
                try:
                    anagrafica.full_clean()
                    anagrafica.save()
                    
                    # Aggiunta alla lista delle importate
                    importate.append({
                        "riga": riga_numero,
                        "nome": anagrafica.display_name(),
                        "codice_fiscale": codice_fiscale,
                        "id": anagrafica.id
                    })
                    
                except ValidationError as ve:
                    # Errori di validazione Django
                    errori_validazione = []
                    if hasattr(ve, 'message_dict'):
                        for field, errors in ve.message_dict.items():
                            errori_validazione.extend([f"{field}: {e}" for e in errors])
                    else:
                        errori_validazione.append(str(ve))
                    
                    scartate.append({
                        "riga": riga_numero,
                        "dati": f"{cognome} {nome}".strip() or ragione_sociale,
                        "motivi": errori_validazione
                    })
            
            except Exception as e:
                # Errore generico
                scartate.append({
                    "riga": riga_numero,
                    "dati": str(row),
                    "motivi": [f"Errore imprevisto: {str(e)}"]
                })
        
        # Preparazione risposta
        return Response({
            "totale": riga_numero - 1,  # -1 per l'header
            "importate": importate,
            "scartate": scartate,
            "num_importate": len(importate),
            "num_scartate": len(scartate),
        }, status=status.HTTP_200_OK)


class ClienteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet read-only per Clienti
    """
    permission_classes = [IsAuthenticated]
    queryset = Cliente.objects.select_related('anagrafica').all()
    serializer_class = ClienteSerializer
    pagination_class = None  # Disabilita paginazione per avere tutti i clienti nelle select


class ClientiTipoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet read-only per Tipi Cliente
    
    list: GET /api/v1/anagrafiche/tipi-cliente/
    retrieve: GET /api/v1/anagrafiche/tipi-cliente/{id}/
    """
    permission_classes = [IsAuthenticated]
    queryset = ClientiTipo.objects.all()
    serializer_class = ClientiTipoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codice', 'descrizione']
    ordering_fields = ['codice', 'descrizione']
    ordering = ['descrizione']


class ComuneItalianoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet read-only per Comuni Italiani
    
    list: GET /api/v1/anagrafiche/comuni/
          Supporta ricerca per nome, provincia, CAP
          Query params: search, provincia
    retrieve: GET /api/v1/anagrafiche/comuni/{id}/
    """
    permission_classes = [AllowAny]  # Dati pubblici ISTAT - nessuna autenticazione richiesta
    queryset = ComuneItaliano.objects.filter(attivo=True)
    serializer_class = ComuneItalianoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'nome_alternativo', 'cap', 'codice_istat', 'codice_belfiore']
    filterset_fields = ['provincia', 'regione', 'flag_capoluogo']
    ordering_fields = ['nome', 'provincia', 'cap']
    ordering = ['nome']
    
    
    def get_queryset(self):
        """
        Ottimizza query e permette ricerca avanzata
        """
        queryset = super().get_queryset()
        
        # Ricerca per provincia (filtro veloce)
        provincia = self.request.query_params.get('provincia', None)
        if provincia:
            queryset = queryset.filter(provincia__iexact=provincia)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Lista comuni con limite per performance autocomplete
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Limita a 50 risultati per autocomplete
        if request.query_params.get('search'):
            queryset = queryset[:50]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


