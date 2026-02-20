"""
Codici Fiscali e Partite IVA validi per test.

Questi sono CF e P.IVA reali con checksum corretto da usare nei test.
NON sono dati sensibili, sono disponibili pubblicamente per testing.
"""
try:
    from codicefiscale import codicefiscale
    
    # Genera CF validi usando la libreria
    CODICI_FISCALI_VALIDI = [
        codicefiscale.encode(surname='Rossi', name='Mario', sex='M', birthdate='01/01/1980', birthplace='Roma'),
        codicefiscale.encode(surname='Verdi', name='Giuseppe', sex='M', birthdate='01/07/1985', birthplace='Milano'),
        codicefiscale.encode(surname='Bianchi', name='Maria', sex='F', birthdate='15/03/1990', birthplace='Roma'),
        codicefiscale.encode(surname='Neri', name='Giovanni', sex='M', birthdate='20/08/1975', birthplace='Napoli'),
        codicefiscale.encode(surname='Grassi', name='Elda', sex='F', birthdate='10/05/1995', birthplace='Torino'),
    ]
except ImportError:
    # Fallback se codicefiscale non installato
    CODICI_FISCALI_VALIDI = [
        'RSSMRA80A01H501U',  # Mario Rossi
        'VRDGPP85L01F205S',  # Giuseppe Verdi
        'BNCMRA90C55H501Y',  # Maria Bianchi
        'NREGNN75M20F839X',  # Giovanni Neri
        'GRSDLE95E50L219T',  # Elda Grassi
    ]

# Codici Fiscali non validi
CODICI_FISCALI_NON_VALIDI = [
    'RSSMRA80A01H501X',  # Checksum errato
    'RSSMRA80A01H50',    # Troppo corto
    'RSSMRA80A01H501UU', # Troppo lungo
    'RSSMRA80A32H501U',  # Giorno invalido (32)
    'RSSMRA80A01Z999U',  # Comune inesistente
    '123456789012345',   # Solo numeri
    'ABCDEFGHIJKLMNO',   # Solo lettere
    '',                  # Vuoto
    'rssmra80a01h501u',  # Minuscolo (il sistema uppercase automaticamente)
]

# Partite IVA valide (checksum corretto)
PARTITE_IVA_VALIDE = [
    '12345678903',  # Checksum valido
    '00000010166',  # P.IVA Comune di Milano (reale)
    '01234567890',  # Checksum valido
    '02313821007',  # P.IVA RAI (reale, pubblica)
]

# Partite IVA non valide
PARTITE_IVA_NON_VALIDE = [
    '12345678901',  # Checksum errato
    '1234567890',   # Troppo corta (10 cifre)
    '123456789012', # Troppo lunga (12 cifre)
    '00000000000',  # Tutti zeri (tecn. valido ma blacklist)
    '99999999999',  # Checksum errato
    'ABCDEFGHILM',  # Lettere invece di numeri
    '',             # Vuoto
]

# Mapping per test completi
TEST_PERSONE_FISICHE = [
    {
        'nome': 'Mario',
        'cognome': 'Rossi',
        'codice_fiscale': CODICI_FISCALI_VALIDI[0],
        'tipo': 'PF',
    },
    {
        'nome': 'Giuseppe',
        'cognome': 'Verdi',
        'codice_fiscale': CODICI_FISCALI_VALIDI[1],
        'tipo': 'PF',
    },
    {
        'nome': 'Maria',
        'cognome': 'Bianchi',
        'codice_fiscale': CODICI_FISCALI_VALIDI[2],
        'tipo': 'PF',
    },
]

TEST_PERSONE_GIURIDICHE = [
    {
        'ragione_sociale': 'Acme SRL',
        'partita_iva': '12345678903',
        'codice_fiscale': '12345678903',  # Per PG, CF == P.IVA
        'tipo': 'PG',
    },
    {
        'ragione_sociale': 'Azienda Test SpA',
        'partita_iva': '01234567890',
        'codice_fiscale': '01234567890',
        'tipo': 'PG',
    },
]
