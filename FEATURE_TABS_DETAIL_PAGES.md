# Implementazione Tabs per Detail Pages

## 📋 Stato Implementazione

### ✅ Completato
- [x] Componente riutilizzabile `TabPanel` creato in `/frontend/src/components/common/TabPanel.tsx`

### ⏳ In Corso
- [ ] DocumentoDetailPage - Refactoring con tabs
- [ ] FascicoloDetailPage - Refactoring con tabs  
- [ ] PraticaDetailPage - Refactoring con tabs

## 🎨 Struttura Proposta

### DocumentoDetailPage (668 righe → ~3 tabs)

```tsx
// Header sempre visibile
<div className="page-header">
  <h1>{documento.codice}</h1>
  <div>
    <button>Indietro</button>
    <button>Modifica</button>
    <button>Download</button>
    <button>Elimina</button>
  </div>
</div>

// Tabs scrollabili con contatori
<Tabs value={activeTab} onChange={handleChange} variant="scrollable">
  <Tab label="Dettagli" />
  <Tab label={<Badge badgeContent={movimenti.length}>Protocollo</Badge>} />
  <Tab label={<Badge badgeContent={scadenze.length}>Scadenze</Badge>} />
</Tabs>

// Tab 0: Dettagli (layout 2 colonne)
<TabPanel value={activeTab} index={0}>
  <Grid container spacing={2}>
    <Grid item xs={8}>
      {/* Informazioni Base */}
      <Card>Codice, Data, Descrizione, Cliente, Fascicolo, Tipo, Stato...</Card>
    </Grid>
    <Grid item xs={4}>
      {/* File */}
      <Card>Nome file, Percorso, Download</Card>
      {/* Classificazione */}
      <Card>Titolario</Card>
      {/* Metadati */}
      <Card>Creato il, Aggiornato il</Card>
    </Grid>
  </Grid>
</TabPanel>

// Tab 1: Protocollo
<TabPanel value={activeTab} index={1}>
  <Card>
    <Button>Protocolla</Button>
    {/* Protocollo Attivo */}
    {protocolloAttivo && <Alert>Numero, Data, Direzione</Alert>}
    {/* Storico Movimenti */}
    <List>{movimenti.map(mov => <ListItem>...</ListItem>)}</List>
  </Card>
</TabPanel>

// Tab 2: Scadenze
<TabPanel value={activeTab} index={2}>
  <Card>
    <Button>Crea Scadenza</Button>
    <List>{scadenze.map(scad => <Card clickable>...</Card>)}</List>
  </Card>
</TabPanel>
```

### FascicoloDetailPage (1130 righe → ~5 tabs)

```tsx
// Header sempre visibile
<div className="page-header">
  <h1>{fascicolo.codice}</h1>
  <Badge>{stato}</Badge>
  <div>
    <button>Indietro</button>
    <button>Modifica</button>
    <button>Elimina</button>
    <ButtonGroup>
      <button>Protocolla</button>
      <button>Stampa Etichetta</button>
      <button>Stampa Copertina</button>
    </ButtonGroup>
  </div>
</div>

// Tabs scrollabili con contatori
<Tabs value={activeTab} onChange={handleChange} variant="scrollable">
  <Tab label="Generale" />
  <Tab label={<Badge badgeContent={documenti.length}>Documenti</Badge>} />
  <Tab label={<Badge badgeContent={sottofascicoli.length}>Sottofascicoli</Badge>} />
  <Tab label={<Badge badgeContent={fascicoliCollegati.length}>Relazioni</Badge>} />
  <Tab label={<Badge badgeContent={movimenti.length}>Protocollo</Badge>} />
</Tabs>

// Tab 0: Generale
<TabPanel value={activeTab} index={0}>
  <Grid container spacing={2}>
    <Grid item xs={6}>
      <Card>Informazioni Principali</Card>
      <Card>Ubicazione Fisica</Card>
    </Grid>
    <Grid item xs={6}>
      <Card>Date</Card>
      <Card>Note</Card>
      <Card>Pratiche Collegate</Card>
    </Grid>
  </Grid>
</TabPanel>

// Tab 1: Documenti
<TabPanel value={activeTab} index={1}>
  <Card>
    <Button>Crea Documento</Button>
    <Table>{documenti + documentiSottofascicoli}</Table>
  </Card>
</TabPanel>

// Tab 2: Sottofascicoli
<TabPanel value={activeTab} index={2}>
  <Card>
    <Button>Crea Sottofascicolo</Button>
    <Button>Collega Sottofascicolo Esistente</Button>
    <Table>{sottofascicoli}</Table>
  </Card>
  <Card>
    <Input placeholder="Cerca fascicolo da collegare come sottofascicolo" />
    <List>{fascicoliCollegabili}</List>
  </Card>
</TabPanel>

// Tab 3: Relazioni
<TabPanel value={activeTab} index={3}>
  <Card>
    <Input placeholder="Cerca fascicolo da collegare" />
    <List>{fascicoliCollegabiliM2M}</List>
  </Card>
  <Card>
    <h3>Fascicoli Collegati</h3>
    <Table>{fascicoliCollegati}</Table>
  </Card>
</TabPanel>

// Tab 4: Protocollo
<TabPanel value={activeTab} index={4}>
  <Card>
    <Button>Protocolla</Button>
    {protocolloAttivo && <Alert>...</Alert>}
    <List>{movimentiProtocollo}</List>
  </Card>
</TabPanel>
```

### PraticaDetailPage (1104 righe → ~5 tabs)

```tsx
// Header sempre visibile
<div className="page-header">
  <h1>{pratica.codice}</h1>
  <Badge>{stato}</Badge>
  <p>{oggetto}</p>
  <div>
    <button>Indietro</button>
    <button>Modifica</button>
    <button>Elimina</button>
  </div>
</div>

// Tabs scrollabili con contatori
<Tabs value={activeTab} onChange={handleChange} variant="scrollable">
  <Tab label="Generale" />
  <Tab label={<Badge badgeContent={fascicoli.length}>Fascicoli</Badge>} />
  <Tab label={<Badge badgeContent={documenti.length}>Documenti</Badge>} />
  <Tab label={<Badge badgeContent={note.length}>Note</Badge>} />
  <Tab label={<Badge badgeContent={scadenze.length}>Scadenze</Badge>} />
</Tabs>

// Tab 0: Generale
<TabPanel value={activeTab} index={0}>
  <Grid container spacing={2}>
    <Grid item xs={6}>
      <Card>Informazioni Principali (Tipo, Cliente, Responsabile)</Card>
    </Grid>
    <Grid item xs={6}>
      <Card>Date (Apertura, Riferimento, Chiusura)</Card>
    </Grid>
  </Grid>
  {note && <Card>Note Generali</Card>}
  {tag && <Card>Tags</Card>}
</TabPanel>

// Tab 1: Fascicoli
<TabPanel value={activeTab} index={1}>
  <Card>
    <Button>Collega Fascicolo Esistente</Button>
    <Button>Crea Nuovo Fascicolo</Button>
    <Table>{fascicoli con pulsante Scollega}</Table>
  </Card>
</TabPanel>

// Tab 2: Documenti
<TabPanel value={activeTab} index={2}>
  <Card>
    {/* Filtri */}
    <Grid container spacing={1}>
      <Input placeholder="Cerca..." />
      <Select>Tipo</Select>
      <Select>Cliente</Select>
      <Input type="date">Data Da</Input>
      <Input type="date">Data A</Input>
    </Grid>
    {/* Tabella */}
    <Table>{documentiFiltered}</Table>
  </Card>
</TabPanel>

// Tab 3: Note
<TabPanel value={activeTab} index={3}>
  <Card>
    <Button>Aggiungi Nota</Button>
    {showNotaForm && <Form>{NotaForm}</Form>}
    <List>{note.map(nota => <Card editable>...</Card>)}</List>
  </Card>
</TabPanel>

// Tab 4: Scadenze
<TabPanel value={activeTab} index={4}>
  <Card>
    <Button>Crea Scadenza</Button>
    <List>{scadenze.map(scad => <Card clickable>...</Card>)}</List>
  </Card>
</TabPanel>
```

## 🔧 Modifiche Tecniche

### Import Necessari
```tsx
import { Tabs, Tab, Box, Badge } from '@mui/material';
import { TabPanel, a11yProps } from '@/components/common/TabPanel';
```

### State Aggiuntivo
```tsx
const [activeTab, setActiveTab] = useState(0);
```

### Handler Cambio Tab
```tsx
const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
  setActiveTab(newValue);
};
```

### Stile Tabs (scrollable)
```tsx
<Tabs
  value={activeTab}
  onChange={handleTabChange}
  variant="scrollable"
  scrollButtons="auto"
  aria-label="navigation tabs"
>
```

### Badge sui Contatori
```tsx
<Tab 
  label={
    <Badge badgeContent={items.length} color="primary">
      <span style={{ marginRight: items.length ? '20px' : '0' }}>
        Nome Tab
      </span>
    </Badge>
  } 
  {...a11yProps(index)} 
/>
```

## ⚠️ Note Implementazione

1. **Header sempre visibile**: Resta fuori dalle tabs per garantire accessibilità costante alle azioni principali
2. **Tab default**: Sempre tab 0 (Generale) all'apertura
3. **Contatori dinamici**: I badge si aggiornano automaticamente quando cambiano i dati
4. **Scrollable tabs**: Permette di avere molte tab senza problemi di layout
5. **Accessibilità**: Uso di `a11yProps` per screen readers
6. **Logica invariata**: Tutti gli handler, stati, useEffect rimangono identici
7. **Modal/Form**: Continuano a funzionare normalmente (es. Modal "Collega Fascicolo" in PraticaDetailPage)

## 📝 Prossimi Passi

1. Validazione struttura con l'utente
2. Implementazione DocumentoDetailPage (più semplice)
3. Implementazione FascicoloDetailPage (media complessità)
4. Implementazione PraticaDetailPage (più complessa)
5. Test funzionalità complete
6. Test responsive (mobile/tablet)

## 🎨 Esempio CSS Aggiuntivo (se necessario)

```css
/* Stile personalizzato per tabs */
.MuiTabs-root {
  background-color: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.MuiTab-root {
  text-transform: none;
  font-weight: 500;
  min-width: 100px;
}

.MuiTab-root.Mui-selected {
  color: #2563eb;
}

.MuiTabs-indicator {
  background-color: #2563eb;
}

/* Badge personalizzato */
.MuiBadge-badge {
  font-size: 0.75rem;
  height: 18px;
  min-width: 18px;
  padding: 0 4px;
}
```
