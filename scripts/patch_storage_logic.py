#!/usr/bin/env python3
"""
Script per modificare documenti/models.py con la nuova logica storage
"""

import re

# Leggi il file
with open('documenti/models.py', 'r') as f:
    content = f.read()

# 1. Aggiungi la funzione helper dopo la definizione di User
helper_function = """

# ============================================
# Utility: voce di titolario default
# ============================================
def get_or_create_default_titolario() -> TitolarioVoce:
    \"\"\"
    Ottiene o crea la voce di titolario di default '99 - Varie'
    per documenti senza classificazione specifica.
    \"\"\"
    default_voce, created = TitolarioVoce.objects.get_or_create(
        codice="99",
        parent=None,
        defaults={
            "titolo": "Varie",
            "pattern_codice": "{CLI}-{TIT}-{ANNO}-{SEQ:03d}"
        }
    )
    if created:
        logger.info("Creata voce di titolario default: 99 - Varie")
    return default_voce
"""

# Trova dove inserire la funzione helper (dopo User = get_user_model())
user_line = "User = get_user_model()"
if user_line in content and helper_function.strip() not in content:
    content = content.replace(user_line, user_line + helper_function)
    print("✓ Aggiunta funzione get_or_create_default_titolario()")

# 2. Sostituisci la funzione _build_path
old_build_path = r'''    def _build_path\(self\) -> str:
        """Percorso ASSOLUTO del contenitore del documento nel NAS, coerente con Fascicolo\."""
        # 1\) Path "del documento" \(in base al suo titolario, se presente\)
        cli_code = self\._cliente_code\(self\.cliente\)
        doc_parts = build_titolario_parts\(self\.titolario_voce\) if self\.titolario_voce_id else \[\]
        doc_abs = ensure_archivio_path\(cli_code, doc_parts, self\.data_documento\.year\)

        # 2\) Se legato a un fascicolo, confronta con il path del fascicolo
        if self\.fascicolo_id:
            fasc_abs = \(self\.fascicolo\.path_archivio or ""\)\.strip\(\)
            # Usa il path fascicolo solo se esiste e coincide col path del documento
            try:
                same = bool\(fasc_abs\) and os\.path\.normpath\(fasc_abs\) == os\.path\.normpath\(doc_abs\)
                exists = bool\(fasc_abs\) and os\.path\.isdir\(fasc_abs\)
            except Exception:
                same, exists = False, False
            if same and exists:
                return fasc_abs
        # 3\) Default: usa il path calcolato per il documento \(case 1: diverso o inesistente; case 2: sempre consentito\)
        return doc_abs'''

new_build_path = '''    def _build_path(self) -> str:
        """
        Percorso ASSOLUTO del contenitore del documento nel NAS.
        
        Logica:
        1. Se il documento ha un titolario_voce, usa quello
        2. Se non ha titolario_voce, usa la voce default "99 - Varie"
        3. I documenti fascicolati possono avere un titolario diverso dal fascicolo
           (es. documento creato prima dell'associazione al fascicolo)
        """
        cli_code = self._cliente_code(self.cliente)
        
        # Usa il titolario del documento, oppure la voce default "99 - Varie"
        voce_da_usare = self.titolario_voce
        if not voce_da_usare:
            voce_da_usare = get_or_create_default_titolario()
        
        doc_parts = build_titolario_parts(voce_da_usare) if voce_da_usare else []
        doc_abs = ensure_archivio_path(cli_code, doc_parts, self.data_documento.year)
        
        return doc_abs'''

content = re.sub(old_build_path, new_build_path, content, flags=re.MULTILINE | re.DOTALL)
print("✓ Sostituita funzione _build_path()")

# Scrivi il file modificato
with open('documenti/models.py', 'w') as f:
    f.write(content)

print("\n✓✓✓ Modifiche completate con successo!")
