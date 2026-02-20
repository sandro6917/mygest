# Esempi Pratici - Archivio Fisico

## Scenari d'Uso Reali

### Scenario 1: Archiviazione Documento in Entrata

**Contesto:** Un documento protocollato deve essere archiviato fisicamente.

#### Step 1: Identifica il documento
```bash
# Cerca documenti tracciabili
GET /api/v1/archivio-fisico/documenti-tracciabili/?search=PROT-2024-001
```

#### Step 2: Identifica unità di destinazione
```bash
# Visualizza albero archivio
GET /api/v1/archivio-fisico/unita/tree/
```

#### Step 3: Crea operazione di entrata
```typescript
const operazione = {
  tipo_operazione: 'entrata',
  referente_interno: currentUserId,
  referente_esterno: fornitorId,
  note: 'Archiviazione fatture gennaio 2024',
  righe: [
    {
      documento: 123,
      unita_fisica_destinazione: 45,  // Scaffale A - Ripiano 2
      stato_successivo: 'archiviato',
      note: 'Collocazione definitiva'
    }
  ]
};

await createOperazioneArchivio(operazione);
```

#### Step 4: Processa operazione
```typescript
await processOperazioneArchivio(operazione.id);
// Il documento passa da 'protocollato' a 'archiviato'
// Viene creata la collocazione fisica
```

#### Step 5: Genera verbale
```typescript
await downloadVerbaleConsegna(operazione.id, 'template-standard');
// Download automatico del DOCX con tutti i dettagli
```

---

### Scenario 2: Prelievo Documento per Consultazione

**Contesto:** Un documento archiviato deve essere prelevato temporaneamente.

```typescript
const operazione = {
  tipo_operazione: 'uscita',
  referente_interno: currentUserId,
  referente_esterno: clienteId,
  note: 'Prelievo per consultazione causa contenzioso',
  righe: [
    {
      documento: 123,
      unita_fisica_sorgente: 45,  // Da: Scaffale A - Ripiano 2
      stato_successivo: 'in_consultazione'
    }
  ]
};

await createOperazioneArchivio(operazione);
await processOperazioneArchivio(operazione.id);
// Il documento viene spostato all'unità di scarico
```

---

### Scenario 3: Spostamento Interno

**Contesto:** Riorganizzazione archivio, spostamento tra scaffali.

```typescript
const operazione = {
  tipo_operazione: 'interna',
  referente_interno: currentUserId,
  note: 'Riorganizzazione archivio - consolidamento pratiche 2023',
  righe: [
    {
      documento: 123,
      unita_fisica_sorgente: 45,      // Da: Scaffale A - Ripiano 2
      unita_fisica_destinazione: 67,  // A: Scaffale B - Ripiano 3
      stato_successivo: 'archiviato'
    },
    {
      documento: 124,
      unita_fisica_sorgente: 45,
      unita_fisica_destinazione: 67,
      stato_successivo: 'archiviato'
    }
  ]
};

await createOperazioneArchivio(operazione);
await processOperazioneArchivio(operazione.id);
```

---

### Scenario 4: Archiviazione Fascicolo Completo

**Contesto:** Un fascicolo con più documenti deve essere archiviato.

```typescript
// Prima cerca il fascicolo
const fascicoli = await getFascicoliTracciabili('FASC-2024-042');
const fascicolo = fascicoli[0];

// Poi cerca tutti i documenti del fascicolo
const documenti = await getDocumentiTracciabili(`fascicolo:${fascicolo.id}`);

// Crea operazione con più righe
const operazione = {
  tipo_operazione: 'entrata',
  referente_interno: currentUserId,
  note: `Archiviazione completa fascicolo ${fascicolo.codice}`,
  righe: [
    // Riga per il fascicolo
    {
      fascicolo: fascicolo.id,
      unita_fisica_destinazione: 89,  // Contenitore fascicoli 2024
      stato_successivo: 'archiviato'
    },
    // Righe per ogni documento
    ...documenti.map(doc => ({
      documento: doc.id,
      unita_fisica_destinazione: 89,
      stato_successivo: 'archiviato',
      note: `Parte del fascicolo ${fascicolo.codice}`
    }))
  ]
};

await createOperazioneArchivio(operazione);
await processOperazioneArchivio(operazione.id);
```

---

## Integrazione nei Workflow

### Workflow: Dal Protocollo all'Archivio

```typescript
// 1. Utente protocolla documento
const movimento = await createMovimentoProtocollo({
  tipo: 'entrata',
  oggetto: 'Fattura fornitore XYZ',
  documento_id: newDocumento.id
});

// 2. Documento diventa tracciabile
await updateDocumento(newDocumento.id, {
  tracciabile: true,
  stato: 'protocollato'
});

// 3. Schedulazione archiviazione automatica dopo 7 giorni
setTimeout(async () => {
  const operazione = await createOperazioneArchivio({
    tipo_operazione: 'entrata',
    referente_interno: SYSTEM_USER_ID,
    note: 'Archiviazione automatica post-protocollo',
    righe: [{
      documento: newDocumento.id,
      movimento_protocollo: movimento.id,
      unita_fisica_destinazione: DEFAULT_ARCHIVE_UNIT,
      stato_successivo: 'archiviato'
    }]
  });
  
  await processOperazioneArchivio(operazione.id);
}, 7 * 24 * 60 * 60 * 1000);
```

### Workflow: Restituzione con Verifica

```typescript
// 1. Crea operazione di uscita
const uscita = await createOperazioneArchivio({
  tipo_operazione: 'uscita',
  referente_interno: currentUserId,
  referente_esterno: clienteId,
  righe: [{
    documento: documentoId,
    stato_successivo: 'in_prestito'
  }]
});

// 2. Processa uscita
await processOperazioneArchivio(uscita.id);

// 3. Dopo consultazione, crea operazione di rientro
const rientro = await createOperazioneArchivio({
  tipo_operazione: 'entrata',
  referente_interno: currentUserId,
  note: 'Rientro dopo consultazione',
  righe: [{
    documento: documentoId,
    unita_fisica_destinazione: originalUnitaId,
    stato_successivo: 'archiviato'
  }]
});

// 4. Processa rientro
await processOperazioneArchivio(rientro.id);
```

---

## Uso dei Componenti React

### Esempio 1: Form Custom con Selettori

```typescript
import React, { useState } from 'react';
import { DocumentoSelector, FascicoloSelector } from '../components/ArchivioFisico';

const MyCustomForm = () => {
  const [selectedDocumento, setSelectedDocumento] = useState(null);
  const [selectedFascicolo, setSelectedFascicolo] = useState(null);
  
  const handleSubmit = async () => {
    const operazione = {
      tipo_operazione: 'entrata',
      referente_interno: currentUser.id,
      righe: []
    };
    
    if (selectedDocumento) {
      operazione.righe.push({
        documento: selectedDocumento.id,
        unita_fisica_destinazione: destinationUnitId,
        stato_successivo: 'archiviato'
      });
    }
    
    if (selectedFascicolo) {
      operazione.righe.push({
        fascicolo: selectedFascicolo.id,
        unita_fisica_destinazione: destinationUnitId,
        stato_successivo: 'archiviato'
      });
    }
    
    await createOperazioneArchivio(operazione);
  };
  
  return (
    <Box>
      <DocumentoSelector
        value={selectedDocumento}
        onChange={setSelectedDocumento}
        label="Seleziona Documento"
      />
      
      <FascicoloSelector
        value={selectedFascicolo}
        onChange={setSelectedFascicolo}
        label="Seleziona Fascicolo"
      />
      
      <Button onClick={handleSubmit}>Archivia</Button>
    </Box>
  );
};
```

### Esempio 2: TreeView per Navigazione

```typescript
import React, { useState } from 'react';
import { UnitaFisicaTreeView } from '../components/ArchivioFisico';

const ArchiveNavigator = () => {
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [documents, setDocuments] = useState([]);
  
  const handleSelectUnit = async (node) => {
    setSelectedUnit(node);
    
    // Carica documenti nella unità selezionata
    const collocazioni = await getCollocazioniFisiche({
      unita: node.id,
      solo_attive: true
    });
    
    setDocuments(collocazioni);
  };
  
  return (
    <Grid container spacing={2}>
      <Grid item xs={4}>
        <UnitaFisicaTreeView
          onSelectNode={handleSelectUnit}
          selectedNodeId={selectedUnit?.id}
        />
      </Grid>
      
      <Grid item xs={8}>
        <Typography variant="h6">
          Documenti in {selectedUnit?.nome}
        </Typography>
        <List>
          {documents.map(doc => (
            <ListItem key={doc.id}>
              <ListItemText
                primary={doc.documento_detail?.codice}
                secondary={doc.documento_detail?.descrizione}
              />
            </ListItem>
          ))}
        </List>
      </Grid>
    </Grid>
  );
};
```

### Esempio 3: Dashboard Statistiche

```typescript
import React, { useEffect, useState } from 'react';
import { getOperazioniArchivio, getCollocazioniFisiche } from '../api/archivioFisico';

const ArchiveDashboard = () => {
  const [stats, setStats] = useState({
    totaleOperazioni: 0,
    operazioniMeseCorrente: 0,
    documentiArchiviati: 0,
    percentualeOccupazione: 0
  });
  
  useEffect(() => {
    loadStats();
  }, []);
  
  const loadStats = async () => {
    const oggi = new Date();
    const inizioMese = new Date(oggi.getFullYear(), oggi.getMonth(), 1);
    
    // Operazioni totali
    const allOperations = await getOperazioniArchivio({}, 1, 9999);
    
    // Operazioni mese corrente
    const monthOperations = await getOperazioniArchivio({
      data_dal: inizioMese.toISOString().split('T')[0]
    }, 1, 9999);
    
    // Collocazioni attive
    const collocazioni = await getCollocazioniFisiche({
      solo_attive: true
    });
    
    setStats({
      totaleOperazioni: allOperations.count,
      operazioniMeseCorrente: monthOperations.count,
      documentiArchiviati: collocazioni.length,
      percentualeOccupazione: calculateOccupancy(collocazioni)
    });
  };
  
  return (
    <Grid container spacing={3}>
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary">Operazioni Totali</Typography>
            <Typography variant="h4">{stats.totaleOperazioni}</Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary">Questo Mese</Typography>
            <Typography variant="h4">{stats.operazioniMeseCorrente}</Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary">Documenti Archiviati</Typography>
            <Typography variant="h4">{stats.documentiArchiviati}</Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary">Occupazione</Typography>
            <Typography variant="h4">{stats.percentualeOccupazione}%</Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};
```

---

## Batch Operations

### Esempio: Archiviazione Massiva

```typescript
const archiviazioneMultipla = async (documentiIds: number[], unitaId: number) => {
  const righe = documentiIds.map(docId => ({
    documento: docId,
    unita_fisica_destinazione: unitaId,
    stato_successivo: 'archiviato'
  }));
  
  const operazione = await createOperazioneArchivio({
    tipo_operazione: 'entrata',
    referente_interno: currentUserId,
    note: `Archiviazione massiva di ${documentiIds.length} documenti`,
    righe
  });
  
  await processOperazioneArchivio(operazione.id);
  
  return operazione;
};

// Uso
await archiviazioneMultipla([101, 102, 103, 104, 105], 45);
```

---

## Gestione Errori

### Esempio: Validazione Pre-Operazione

```typescript
const validateBeforeArchive = async (documentoId: number) => {
  const documento = await getDocumento(documentoId);
  
  const errors = [];
  
  if (!documento.tracciabile) {
    errors.push('Documento non tracciabile');
  }
  
  if (documento.digitale) {
    errors.push('I documenti digitali non possono essere archiviati fisicamente');
  }
  
  const movimenti = await getMovimentiProtocollo({
    documento_id: documentoId
  });
  
  if (movimenti.length === 0) {
    errors.push('Documento non protocollato');
  }
  
  if (errors.length > 0) {
    throw new Error(`Validazione fallita: ${errors.join(', ')}`);
  }
  
  return true;
};

// Uso
try {
  await validateBeforeArchive(123);
  // Procedi con archiviazione
} catch (error) {
  toast.error(error.message);
}
```

---

## Best Practices

### 1. Sempre Processare le Operazioni
```typescript
// ❌ NON FARE
const op = await createOperazioneArchivio(data);
// Gli stati non vengono aggiornati!

// ✅ FARE
const op = await createOperazioneArchivio(data);
await processOperazioneArchivio(op.id);
// Stati e collocazioni aggiornati correttamente
```

### 2. Gestire le Eccezioni
```typescript
try {
  await processOperazioneArchivio(id);
  toast.success('Operazione processata');
} catch (error) {
  toast.error(error.response?.data?.message || 'Errore');
  // Log per debugging
  console.error('Process error:', error);
}
```

### 3. Validare Input
```typescript
if (formData.righe.length === 0) {
  toast.error('Aggiungi almeno una riga');
  return;
}

if (!formData.referente_interno) {
  toast.error('Seleziona referente interno');
  return;
}
```

### 4. Feedback Visivo
```typescript
const [saving, setSaving] = useState(false);

const handleSave = async () => {
  setSaving(true);
  try {
    await saveData();
    toast.success('Salvato!');
  } finally {
    setSaving(false);
  }
};

// Nel JSX
<Button disabled={saving}>
  {saving ? 'Salvataggio...' : 'Salva'}
</Button>
```

---

Questi esempi coprono i casi d'uso più comuni e forniscono pattern riutilizzabili per l'implementazione. 🎯
