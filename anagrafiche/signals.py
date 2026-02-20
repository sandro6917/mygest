from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Anagrafica, AnagraficaDeletion, Indirizzo, EmailContatto
from .models_comuni import ComuneItaliano


@receiver(post_save, sender=Indirizzo)
def sync_comune_italiano_to_fields(sender, instance: Indirizzo, **kwargs):
    """
    Quando viene salvato un indirizzo con comune_italiano popolato,
    sincronizza automaticamente cap, comune e provincia dai dati del comune.
    Questo signal viene eseguito PRIMA del salvataggio, tramite pre_save,
    ma Django non supporta modifiche all'instance nel post_save che triggera un nuovo save.
    Quindi usiamo la logica nel model save() invece.
    """
    pass  # La logica è implementata in Indirizzo.save()


@receiver(post_delete, sender=Anagrafica)
def log_anagrafica_deletion(sender, instance: Anagrafica, **kwargs):
    try:
        display = instance.display_name()
    except Exception:
        display = getattr(instance, "ragione_sociale", "") or f"{getattr(instance,'cognome','')} {getattr(instance,'nome','')}".strip()
    AnagraficaDeletion.objects.create(
        original_id=instance.pk or 0,
        codice_fiscale=instance.codice_fiscale or "",
        display_name=display or "",
    )


@receiver(post_save, sender=Indirizzo)
def sync_indirizzo_principale(sender, instance: Indirizzo, created, **kwargs):
    """
    Quando viene salvato un indirizzo principale, aggiorna il campo 'indirizzo' dell'anagrafica.
    Se viene rimosso il flag principale da un indirizzo, pulisce il campo.
    """
    if instance.anagrafica_id:
        if instance.principale:
            # Costruisci stringa indirizzo completo
            parts = []
            if instance.toponimo:
                parts.append(instance.toponimo)
            if instance.indirizzo:
                parts.append(instance.indirizzo)
            if instance.numero_civico:
                parts.append(instance.numero_civico)
            
            riga1 = " ".join(parts).strip()
            
            parts2 = []
            if instance.cap:
                parts2.append(instance.cap)
            if instance.comune:
                parts2.append(instance.comune)
            if instance.provincia:
                parts2.append(f"({instance.provincia})")
            
            riga2 = " ".join(parts2).strip()
            
            indirizzo_completo = f"{riga1}, {riga2}" if riga1 and riga2 else (riga1 or riga2)
            
            # Aggiorna anagrafica senza triggare altri signal
            Anagrafica.objects.filter(pk=instance.anagrafica_id).update(indirizzo=indirizzo_completo)
        
        elif not created:
            # Se tolgo il flag principale da un indirizzo esistente, 
            # verifica se ci sono altri indirizzi principali, altrimenti pulisce
            altri_principali = Indirizzo.objects.filter(
                anagrafica_id=instance.anagrafica_id,
                principale=True
            ).exclude(pk=instance.pk).exists()
            
            if not altri_principali:
                # Nessun altro indirizzo principale: pulisci il campo
                Anagrafica.objects.filter(pk=instance.anagrafica_id).update(indirizzo='')


@receiver(post_delete, sender=Indirizzo)
def clear_indirizzo_principale(sender, instance: Indirizzo, **kwargs):
    """
    Quando viene eliminato un indirizzo principale, pulisce il campo 'indirizzo' dell'anagrafica.
    """
    if instance.principale and instance.anagrafica_id:
        Anagrafica.objects.filter(pk=instance.anagrafica_id).update(indirizzo='')


@receiver(post_save, sender=EmailContatto)
def sync_email_preferito(sender, instance: EmailContatto, created, **kwargs):
    """
    Quando viene salvato un contatto email preferito e attivo,
    aggiorna il campo 'email' o 'pec' dell'anagrafica.
    Se viene rimosso il flag preferito, pulisce il campo se non ci sono altri preferiti.
    """
    if instance.anagrafica_id:
        if instance.is_preferito and instance.attivo:
            # Aggiorna campo appropriato
            if instance.tipo == 'GEN':
                Anagrafica.objects.filter(pk=instance.anagrafica_id).update(email=instance.email)
            elif instance.tipo == 'PEC':
                Anagrafica.objects.filter(pk=instance.anagrafica_id).update(pec=instance.email)
        
        elif not created:
            # Se tolgo il flag preferito da un contatto esistente,
            # verifica se ci sono altri contatti preferiti dello stesso tipo
            altri_preferiti = EmailContatto.objects.filter(
                anagrafica_id=instance.anagrafica_id,
                tipo=instance.tipo,
                is_preferito=True,
                attivo=True
            ).exclude(pk=instance.pk).exists()
            
            if not altri_preferiti:
                # Nessun altro contatto preferito: pulisci il campo
                if instance.tipo == 'GEN':
                    Anagrafica.objects.filter(pk=instance.anagrafica_id).update(email='')
                elif instance.tipo == 'PEC':
                    Anagrafica.objects.filter(pk=instance.anagrafica_id).update(pec='')


@receiver(post_delete, sender=EmailContatto)
def clear_email_preferito(sender, instance: EmailContatto, **kwargs):
    """
    Quando viene eliminato un contatto email preferito, pulisce il campo corrispondente dell'anagrafica.
    """
    if instance.is_preferito and instance.anagrafica_id:
        if instance.tipo == 'GEN':
            Anagrafica.objects.filter(pk=instance.anagrafica_id).update(email='')
        elif instance.tipo == 'PEC':
            Anagrafica.objects.filter(pk=instance.anagrafica_id).update(pec='')