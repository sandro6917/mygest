"""
Comando Django per aggiornare automaticamente lo stato delle scadenze.

Esegui manualmente:
    python manage.py aggiorna_stati_scadenze

Oppure aggiungi a crontab per esecuzione giornaliera:
    0 1 * * * cd /path/to/mygest && /path/to/venv/bin/python manage.py aggiorna_stati_scadenze
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from scadenze.models import Scadenza, ScadenzaOccorrenza


class Command(BaseCommand):
    help = "Aggiorna automaticamente lo stato delle scadenze in base alle occorrenze attive"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula le modifiche senza salvarle nel database',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra output dettagliato',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        oggi = timezone.now().date()
        tre_giorni_dopo = oggi + timedelta(days=3)
        
        # Contatori
        scadute_count = 0
        in_scadenza_count = 0
        attive_count = 0
        ignorate_count = 0
        
        self.stdout.write(self.style.SUCCESS(f"=== Aggiornamento Stati Scadenze - {oggi} ==="))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODALITÀ DRY-RUN: Nessuna modifica verrà salvata"))
        
        # 1) Recuperare scadenze con stato bozza, attiva o in_scadenza
        scadenze_da_processare = Scadenza.objects.filter(
            stato__in=[Scadenza.Stato.BOZZA, Scadenza.Stato.ATTIVA, Scadenza.Stato.IN_SCADENZA]
        )
        
        if verbose:
            self.stdout.write(f"\nScadenze da processare: {scadenze_da_processare.count()}")
        
        for scadenza in scadenze_da_processare:
            # 2) Recuperare occorrenze attive (non completate né annullate)
            occorrenze_attive = ScadenzaOccorrenza.objects.filter(
                scadenza=scadenza
            ).exclude(
                stato__in=[ScadenzaOccorrenza.Stato.COMPLETATA, ScadenzaOccorrenza.Stato.ANNULLATA]
            ).order_by('inizio')
            
            # Se non ci sono occorrenze attive, ignora questa scadenza
            if not occorrenze_attive.exists():
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⊘ [{scadenza.id}] {scadenza.titolo} - "
                            f"Nessuna occorrenza attiva, IGNORATA"
                        )
                    )
                ignorate_count += 1
                continue
            
            # 3) Prendere la prima occorrenza (quella con data inizio minore/più recente)
            prima_occorrenza = occorrenze_attive.first()
            data_inizio = prima_occorrenza.inizio.date()
            
            # 4) Determinare nuovo stato e priorità
            nuovo_stato = None
            nuova_priorita = None
            motivo = ""
            
            if data_inizio < oggi:
                # a) SCADUTA + CRITICA
                nuovo_stato = Scadenza.Stato.SCADUTA
                nuova_priorita = Scadenza.Priorita.CRITICA
                giorni_passati = (oggi - data_inizio).days
                motivo = f"SCADUTA (occorrenza del {data_inizio}, {giorni_passati} giorni fa)"
                scadute_count += 1
                
            elif oggi <= data_inizio <= tre_giorni_dopo:
                # b) IN_SCADENZA + CRITICA
                nuovo_stato = Scadenza.Stato.IN_SCADENZA
                nuova_priorita = Scadenza.Priorita.CRITICA
                giorni_rimanenti = (data_inizio - oggi).days
                motivo = f"IN_SCADENZA (occorrenza il {data_inizio}, tra {giorni_rimanenti} giorni)"
                in_scadenza_count += 1
                
            else:  # data_inizio > tre_giorni_dopo
                # c) ATTIVA + MEDIA
                nuovo_stato = Scadenza.Stato.ATTIVA
                nuova_priorita = Scadenza.Priorita.MEDIA
                giorni_rimanenti = (data_inizio - oggi).days
                motivo = f"ATTIVA (occorrenza il {data_inizio}, tra {giorni_rimanenti} giorni)"
                attive_count += 1
            
            # Applica modifiche solo se cambiato qualcosa
            if scadenza.stato != nuovo_stato or scadenza.priorita != nuova_priorita:
                if verbose:
                    self.stdout.write(
                        f"  → [{scadenza.id}] {scadenza.titolo} "
                        f"({scadenza.get_stato_display()} → {nuovo_stato.label}, "
                        f"{scadenza.get_priorita_display()} → {nuova_priorita.label}) - {motivo}"
                    )
                
                if not dry_run:
                    scadenza.stato = nuovo_stato
                    scadenza.priorita = nuova_priorita
                    scadenza.save(update_fields=['stato', 'priorita', 'aggiornato_il'])
            else:
                if verbose:
                    self.stdout.write(
                        f"  ✓ [{scadenza.id}] {scadenza.titolo} - "
                        f"Già nello stato corretto ({nuovo_stato.label})"
                    )
        
        # Riepilogo
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✓ Scadenze marcate come SCADUTE: {scadute_count}"))
        self.stdout.write(self.style.SUCCESS(f"✓ Scadenze marcate come IN_SCADENZA: {in_scadenza_count}"))
        self.stdout.write(self.style.SUCCESS(f"✓ Scadenze marcate come ATTIVE: {attive_count}"))
        self.stdout.write(self.style.WARNING(f"⊘ Scadenze ignorate (senza occorrenze): {ignorate_count}"))
        self.stdout.write(self.style.SUCCESS(
            f"✓ Totale elaborate: {scadute_count + in_scadenza_count + attive_count}"
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠ Nessuna modifica salvata (dry-run mode)"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Aggiornamenti completati con successo!"))
