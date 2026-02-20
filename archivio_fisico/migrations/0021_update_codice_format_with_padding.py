# Generated manually to update codice format with 3-digit padding
from django.db import migrations


def update_codice_format(apps, schema_editor):
    """Aggiorna tutti i codici esistenti al nuovo formato con padding a 3 cifre"""
    UnitaFisica = apps.get_model("archivio_fisico", "UnitaFisica")
    
    updated_count = 0
    for unita in UnitaFisica.objects.all().iterator():
        # Rigenera il codice con il nuovo formato: prefisso + progressivo a 3 cifre
        new_codice = f"{unita.prefisso_codice}{unita.progressivo_codice:03d}"
        
        if new_codice != unita.codice:
            # Aggiorna anche full_path che contiene il codice
            old_code = unita.codice
            
            # Ricostruisci full_path sostituendo il vecchio codice con il nuovo
            if unita.full_path:
                parts = unita.full_path.split('/')
                if parts and parts[-1] == old_code:
                    parts[-1] = new_codice
                    new_full_path = '/'.join(parts)
                else:
                    new_full_path = unita.full_path
            else:
                new_full_path = new_codice
            
            # Ricostruisci progressivo (formato: codice-nome-tipo)
            progressivo_parts = []
            if new_codice:
                progressivo_parts.append(new_codice.strip())
            if unita.nome:
                progressivo_parts.append(unita.nome.strip())
            tipo_display = dict(UnitaFisica._meta.get_field('tipo').choices).get(unita.tipo, '')
            if tipo_display:
                progressivo_parts.append(tipo_display)
            new_progressivo = "-".join(progressivo_parts)
            
            # Aggiorna i campi
            UnitaFisica.objects.filter(pk=unita.pk).update(
                codice=new_codice,
                full_path=new_full_path,
                progressivo=new_progressivo
            )
            updated_count += 1
    
    # Aggiorna ricorsivamente i full_path dei figli
    for unita in UnitaFisica.objects.all().order_by('id'):
        if unita.parent_id:
            # Ricostruisci full_path basandosi sui codici aggiornati dei genitori
            parent = UnitaFisica.objects.get(pk=unita.parent_id)
            ancestors = []
            current = parent
            while current:
                ancestors.append(current.codice)
                current = UnitaFisica.objects.filter(pk=current.parent_id).first() if current.parent_id else None
            ancestors.reverse()
            ancestors.append(unita.codice)
            new_full_path = '/'.join(ancestors)
            
            if new_full_path != unita.full_path:
                UnitaFisica.objects.filter(pk=unita.pk).update(full_path=new_full_path)
    
    print(f"Aggiornati {updated_count} codici al nuovo formato con padding a 3 cifre")


def reverse_update_codice_format(apps, schema_editor):
    """Reverte i codici al formato senza padding"""
    UnitaFisica = apps.get_model("archivio_fisico", "UnitaFisica")
    
    for unita in UnitaFisica.objects.all().iterator():
        # Formato senza padding
        old_codice = f"{unita.prefisso_codice}{unita.progressivo_codice}"
        
        if old_codice != unita.codice:
            # Aggiorna full_path
            if unita.full_path:
                parts = unita.full_path.split('/')
                if parts and parts[-1] == unita.codice:
                    parts[-1] = old_codice
                    new_full_path = '/'.join(parts)
                else:
                    new_full_path = unita.full_path
            else:
                new_full_path = old_codice
            
            # Ricostruisci progressivo
            progressivo_parts = []
            if old_codice:
                progressivo_parts.append(old_codice.strip())
            if unita.nome:
                progressivo_parts.append(unita.nome.strip())
            tipo_display = dict(UnitaFisica._meta.get_field('tipo').choices).get(unita.tipo, '')
            if tipo_display:
                progressivo_parts.append(tipo_display)
            new_progressivo = "-".join(progressivo_parts)
            
            UnitaFisica.objects.filter(pk=unita.pk).update(
                codice=old_codice,
                full_path=new_full_path,
                progressivo=new_progressivo
            )


class Migration(migrations.Migration):

    dependencies = [
        ("archivio_fisico", "0020_add_cliente_to_unitafisica"),
    ]

    operations = [
        migrations.RunPython(update_codice_format, reverse_update_codice_format),
    ]
