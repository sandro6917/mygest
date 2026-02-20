#!/usr/bin/env python3
"""
Script per aggiungere la logica di spostamento file quando cambia il titolario
"""

import re

# Leggi il file
with open('documenti/models.py', 'r') as f:
    content = f.read()

# Trova e sostituisci il metodo save()
old_save = r'''    @transaction\.atomic
    def save\(self, \*args, \*\*kwargs\):
        is_new = self\.pk is None
        original_name = None
        if self\.file and hasattr\(self\.file, "name"\):
            original_name = os\.path\.basename\(self\.file\.name\)

        if is_new and not self\.codice:
            seq = self\._next_seq\(\)
            self\.codice = self\._generate_codice\(seq\)

        # percorso assoluto su /mnt/archivio \(usato per calcolare la dir relativa nello storage\)
        self\.percorso_archivio = self\._build_path\(\)

        super\(\)\.save\(\*args, \*\*kwargs\)

        # rinomina/sposta il file dentro lo storage NAS
        if self\.file and original_name:
            self\._rename_file_if_needed\(
                original_name,
                only_new=getattr\(settings, "DOCUMENTI_RENAME_ONLY_NEW", True\),
            \)

        # Sposta sempre il file dentro percorso_archivio \(se presente\)
        if self\.file:
            self\._move_file_into_archivio\(\)'''

new_save = '''    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        original_name = None
        if self.file and hasattr(self.file, "name"):
            original_name = os.path.basename(self.file.name)

        # Verifica se il titolario è cambiato (per spostare il file)
        titolario_changed = False
        old_percorso = None
        if not is_new and self.pk:
            try:
                old_doc = type(self).objects.only("titolario_voce_id", "percorso_archivio").get(pk=self.pk)
                if old_doc.titolario_voce_id != self.titolario_voce_id:
                    titolario_changed = True
                    old_percorso = old_doc.percorso_archivio
                    logger.info(
                        "Documento id=%s: titolario_voce cambiato da %s a %s",
                        self.pk,
                        old_doc.titolario_voce_id,
                        self.titolario_voce_id
                    )
            except type(self).DoesNotExist:
                pass

        if is_new and not self.codice:
            seq = self._next_seq()
            self.codice = self._generate_codice(seq)

        # percorso assoluto su /mnt/archivio (usato per calcolare la dir relativa nello storage)
        self.percorso_archivio = self._build_path()

        super().save(*args, **kwargs)

        # rinomina/sposta il file dentro lo storage NAS
        if self.file and original_name:
            self._rename_file_if_needed(
                original_name,
                only_new=getattr(settings, "DOCUMENTI_RENAME_ONLY_NEW", True),
            )

        # Se il titolario è cambiato e c'è un file, spostalo nella nuova directory
        if titolario_changed and self.file and old_percorso and old_percorso != self.percorso_archivio:
            logger.info(
                "Documento id=%s: spostamento file da %s a %s",
                self.pk,
                old_percorso,
                self.percorso_archivio
            )
            self._move_file_into_archivio()
        # Altrimenti, sposta sempre il file dentro percorso_archivio (se presente)
        elif self.file:
            self._move_file_into_archivio()'''

content = re.sub(old_save, new_save, content, flags=re.MULTILINE | re.DOTALL)
print("✓ Modificato metodo save() con logica spostamento file")

# Scrivi il file modificato
with open('documenti/models.py', 'w') as f:
    f.write(content)

print("\n✓✓✓ Modifiche completate con successo!")
