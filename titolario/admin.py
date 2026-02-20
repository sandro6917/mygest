from __future__ import annotations
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
from django import forms
from django.shortcuts import render
from .models import TitolarioVoce
from anagrafiche.models import Anagrafica


class AnagraficheBulkSelectionForm(forms.Form):
    """Form per selezione anagrafiche nella bulk creation"""
    
    anagrafiche = forms.ModelMultipleChoiceField(
        queryset=Anagrafica.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label=_("Seleziona anagrafiche"),
        help_text=_("Seleziona una o più anagrafiche per cui creare voci titolario"),
        required=True
    )
    
    crea_sottovoci = forms.BooleanField(
        label=_("Crea sotto-voci standard"),
        help_text=_("Crea automaticamente sotto-voci: Buste Paga, Contratti, CU, Documenti Vari"),
        required=False,
        initial=False
    )
    
    def __init__(self, *args, **kwargs):
        anagrafiche_disponibili = kwargs.pop('anagrafiche_disponibili', None)
        super().__init__(*args, **kwargs)
        
        if anagrafiche_disponibili is not None:
            self.fields['anagrafiche'].queryset = anagrafiche_disponibili


@admin.register(TitolarioVoce)
class TitolarioVoceAdmin(admin.ModelAdmin):
    list_display = ("id", "codice", "titolo", "parent", "consente_intestazione_badge", "anagrafica_display")
    list_filter = ("consente_intestazione", "parent")
    search_fields = ("codice", "titolo", "anagrafica__nome", "anagrafica__cognome", "anagrafica__ragione_sociale")
    autocomplete_fields = ["anagrafica", "parent"]
    actions = ["crea_voci_intestate_bulk"]
    fieldsets = (
        (_("Informazioni Base"), {
            'fields': ('codice', 'titolo', 'parent', 'pattern_codice')
        }),
        (_("Intestazione Anagrafica"), {
            'fields': ('consente_intestazione', 'anagrafica'),
            'description': _(
                "Se 'Consente intestazione' è attivo, questa voce può avere sotto-voci "
                "intestate ad anagrafiche. Se 'Anagrafica' è impostata, questa voce è "
                "intestata a quell'anagrafica specifica."
            )
        }),
    )
    
    class Media:
        js = ('admin/js/titolario_auto_fill.js',)
    
    def consente_intestazione_badge(self, obj):
        """Badge colorato per flag consente_intestazione"""
        if obj.consente_intestazione:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Sì</span>'
            )
        return format_html('<span style="color: gray;">✗ No</span>')
    consente_intestazione_badge.short_description = _("Consente intestazione")
    
    def anagrafica_display(self, obj):
        """Mostra anagrafica con badge se presente"""
        if obj.anagrafica:
            return format_html(
                '<span style="background-color: #e3f2fd; padding: 2px 8px; border-radius: 3px;">'
                '👤 {}</span>',
                obj.anagrafica.display_name()
            )
        return format_html('<span style="color: gray;">-</span>')
    anagrafica_display.short_description = _("Intestataria")
    
    def crea_voci_intestate_bulk(self, request, queryset):
        """
        Admin action: Mostra form per selezionare anagrafiche,
        poi crea voci intestate per le anagrafiche selezionate.
        """
        # Filtra solo voci che consentono intestazione
        voci_valide = queryset.filter(consente_intestazione=True)
        
        if not voci_valide.exists():
            self.message_user(
                request,
                _("Nessuna delle voci selezionate consente intestazione ad anagrafiche."),
                level=messages.ERROR
            )
            return
        
        # Per semplicità, supportiamo solo 1 voce parent alla volta
        if voci_valide.count() > 1:
            self.message_user(
                request,
                _("Seleziona una sola voce parent per volta per la bulk creation."),
                level=messages.WARNING
            )
            return
        
        voce_parent = voci_valide.first()
        
        # Ottieni anagrafiche disponibili
        anagrafiche_disponibili = voce_parent.get_anagrafiche_disponibili()
        
        if not anagrafiche_disponibili or not anagrafiche_disponibili.exists():
            self.message_user(
                request,
                _(f"Nessuna anagrafica disponibile per la voce '{voce_parent}'."),
                level=messages.INFO
            )
            return
        
        # Filtra solo anagrafiche con codice valido
        anagrafiche_con_codice = anagrafiche_disponibili.exclude(
            codice__isnull=True
        ).exclude(codice='')
        
        if not anagrafiche_con_codice.exists():
            self.message_user(
                request,
                _("Nessuna anagrafica con codice valido disponibile."),
                level=messages.INFO
            )
            return
        
        # Se il form è stato inviato (POST)
        if 'apply' in request.POST:
            form = AnagraficheBulkSelectionForm(
                request.POST,
                anagrafiche_disponibili=anagrafiche_con_codice
            )
            
            if form.is_valid():
                anagrafiche_selezionate = form.cleaned_data['anagrafiche']
                crea_sottovoci = form.cleaned_data.get('crea_sottovoci', False)
                
                # Template sotto-voci
                SOTTO_VOCI_TEMPLATE = [
                    ('BP', 'Buste Paga', '{CLI}-{ANA}-BP-{ANNO}-{SEQ:03d}'),
                    ('CONTR', 'Contratti', '{CLI}-{ANA}-CONTR-{ANNO}-{SEQ:03d}'),
                    ('CU', 'Certificazione Unica', '{CLI}-{ANA}-CU-{ANNO}-{SEQ:03d}'),
                    ('DOC', 'Documenti Vari', '{CLI}-{ANA}-DOC-{ANNO}-{SEQ:03d}'),
                ]
                
                # Esegui creazione
                totale_create = 0
                totale_gia_esistenti = 0
                totale_sottovoci = 0
                errori = []
                
                for anagrafica in anagrafiche_selezionate:
                    # Verifica se esiste già (FUORI dalla transazione)
                    if TitolarioVoce.objects.filter(parent=voce_parent, anagrafica=anagrafica).exists():
                        totale_gia_esistenti += 1
                        continue
                    
                    try:
                        # Transazione atomica INDIVIDUALE per ogni voce
                        with transaction.atomic():
                            # Crea voce intestata
                            nuova_voce = TitolarioVoce.objects.create(
                                codice=anagrafica.codice,
                                titolo=f"Dossier {anagrafica.display_name()}",
                                parent=voce_parent,
                                anagrafica=anagrafica,
                                pattern_codice='{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}',
                                consente_intestazione=False
                            )
                            totale_create += 1
                            
                            # Crea sotto-voci se richiesto
                            if crea_sottovoci:
                                for sv_codice, sv_titolo, sv_pattern in SOTTO_VOCI_TEMPLATE:
                                    try:
                                        TitolarioVoce.objects.create(
                                            codice=sv_codice,
                                            titolo=sv_titolo,
                                            parent=nuova_voce,
                                            pattern_codice=sv_pattern,
                                            consente_intestazione=False
                                        )
                                        totale_sottovoci += 1
                                    except Exception as e:
                                        errori.append(f"{anagrafica.display_name()} → {sv_titolo}: {str(e)}")
                    
                    except Exception as e:
                        errori.append(f"{anagrafica.display_name()}: {str(e)}")
                
                # Messaggi di feedback
                if totale_create > 0:
                    msg = f"✓ Create {totale_create} voci intestate con successo!"
                    if crea_sottovoci and totale_sottovoci > 0:
                        msg += f" (+ {totale_sottovoci} sotto-voci)"
                    self.message_user(request, _(msg), level=messages.SUCCESS)
                
                if totale_gia_esistenti > 0:
                    self.message_user(
                        request,
                        _(f"ℹ️ {totale_gia_esistenti} voci già esistenti (saltate)."),
                        level=messages.INFO
                    )
                
                if errori:
                    self.message_user(
                        request,
                        _(f"✗ {len(errori)} errori durante la creazione: {'; '.join(errori[:5])}"),
                        level=messages.WARNING
                    )
                
                if totale_create == 0 and totale_gia_esistenti == 0:
                    self.message_user(
                        request,
                        _("Nessuna voce creata."),
                        level=messages.INFO
                    )
                
                return None  # Ritorna alla lista
        
        # Mostra form per selezione anagrafiche (GET)
        else:
            form = AnagraficheBulkSelectionForm(
                anagrafiche_disponibili=anagrafiche_con_codice
            )
        
        # Rendering template form
        context = {
            'title': _('Seleziona anagrafiche per bulk creation'),
            'form': form,
            'voce_parent': voce_parent,
            'anagrafiche_count': anagrafiche_con_codice.count(),
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'site_title': admin.site.site_title,
            'site_header': admin.site.site_header,
            'queryset': queryset,  # Aggiungi queryset per i campi hidden
            'action_name': 'crea_voci_intestate_bulk',  # Nome dell'action
        }
        
        return render(
            request,
            'admin/titolario/bulk_creation_form.html',
            context
        )
    
    crea_voci_intestate_bulk.short_description = _("Crea voci intestate per anagrafiche selezionate")

