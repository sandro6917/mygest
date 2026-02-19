import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Typography,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Divider,
  Stack,
  IconButton,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Chip,
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Autocomplete,
  TextField,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  ArrowBack as BackIcon,
  FilePresent as FileIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { documentiApi } from '@/api/documenti';
import { fascicoliApi } from '@/api/fascicoli';
import { toast } from 'react-toastify';
import type { FascicoloListItem } from '@/types/fascicolo';

type PreviewData = Awaited<ReturnType<typeof documentiApi.importaCedoliniPreview>>;
type ConfirmResult = Awaited<ReturnType<typeof documentiApi.importaCedoliniConfirm>>;

export function ImportaCedoliniPage() {
  const navigate = useNavigate();
  
  // Step 1: Upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  
  // Step 2: Preview
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [expandDatori, setExpandDatori] = useState(false);
  const [expandDipendenti, setExpandDipendenti] = useState(false);
  const [expandDuplicati, setExpandDuplicati] = useState(false);
  const [expandErrori, setExpandErrori] = useState(false);
  const [expandValidi, setExpandValidi] = useState(false);
  
  // Configurazione import
  const [fascicolo, setFascicolo] = useState<FascicoloListItem | null>(null);
  const [fascicoloOptions, setFascicoloOptions] = useState<FascicoloListItem[]>([]);
  const [fascicoloLoading, setFascicoloLoading] = useState(false);
  const [duplicatePolicy, setDuplicatePolicy] = useState<'skip' | 'replace' | 'add'>('skip');
  
  // Step 3: Confirm
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ConfirmResult | null>(null);
  
  // Importa come Libro Unico
  const [importingLibroUnico, setImportingLibroUnico] = useState(false);
  const [libroUnicoResult, setLibroUnicoResult] = useState<any | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const ext = file.name.toLowerCase();
      if (!ext.endsWith('.zip') && !ext.endsWith('.pdf')) {
        toast.error('Seleziona un file ZIP o PDF');
        return;
      }
      setSelectedFile(file);
      setPreview(null);
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      toast.error('Seleziona un file ZIP o PDF');
      return;
    }

    setAnalyzing(true);
    setPreview(null);

    try {
      const response = await documentiApi.importaCedoliniPreview(selectedFile);
      setPreview(response);
      
      toast.success(
        `Analisi completata: ${response.statistiche.totale_validi} cedolini validi, ` +
        `${response.statistiche.totale_duplicati} duplicati, ` +
        `${response.statistiche.totale_errori} errori`
      );
    } catch (error) {
      console.error('Errore analisi cedolini:', error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast.error(
        apiError.response?.data?.detail ||
          'Errore durante l\'analisi del file'
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!preview) {
      toast.error('Nessuna preview disponibile');
      return;
    }

    setImporting(true);
    setResult(null);

    try {
      // Prepara payload: include validi + duplicati (gestiti secondo policy)
      const cedoliniToImport = [...preview.validi, ...preview.duplicati];
      
      const response = await documentiApi.importaCedoliniConfirm({
        temp_dir: preview.temp_dir,
        cedolini: cedoliniToImport,
        fascicolo: fascicolo?.id || null,
        duplicate_policy: duplicatePolicy,
      });
      
      setResult(response);

      const total = response.created + response.replaced + response.skipped;
      
      if (total > 0 && response.errors.length === 0) {
        let message = `Importazione completata! ${response.created} cedolini creati`;
        if (response.replaced > 0) message += `, ${response.replaced} sostituiti`;
        if (response.skipped > 0) message += `, ${response.skipped} saltati`;
        toast.success(message);
      } else if (total > 0 && response.errors.length > 0) {
        toast.warning(
          `Importazione parziale: ${total} processati, ${response.errors.length} errori`
        );
      } else {
        toast.error('Importazione fallita. Verifica gli errori riportati.');
      }
    } catch (error) {
      console.error('Errore importazione cedolini:', error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast.error(
        apiError.response?.data?.detail ||
          'Errore durante l\'importazione dei cedolini'
      );
    } finally {
      setImporting(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    setLibroUnicoResult(null);
    setFascicolo(null);
    setDuplicatePolicy('skip');
  };
  
  const handleImportaLibroUnico = async () => {
    if (!selectedFile) {
      toast.error('Seleziona un file ZIP');
      return;
    }
    
    if (!selectedFile.name.toLowerCase().endsWith('.zip')) {
      toast.error('Per importare come Libro Unico è necessario un file ZIP');
      return;
    }
    
    // Chiedi conferma e azione duplicati
    const azione = window.confirm(
      'Importare lo ZIP come documento Libro Unico?\n\n' +
      'Il file ZIP verrà salvato come singolo documento LIBUNI per il datore di lavoro.\n\n' +
      'Clicca OK per procedere (duplica se esiste), Annulla per annullare.'
    );
    
    if (!azione) return;
    
    setImportingLibroUnico(true);
    setLibroUnicoResult(null);
    
    try {
      const response = await documentiApi.importaZipLibroUnico(selectedFile, 'duplica');
      
      setLibroUnicoResult(response);
      
      if (response.success) {
        const metaInfo = response.duplicato 
          ? `Trovato duplicato (ID ${response.duplicato_id}). Azione: ${response.azione}`
          : `Documento creato con successo (ID ${response.documento_id})`;
        
        toast.success(
          `✅ ${response.metadati.titolo}\n` +
          `${response.metadati.num_cedolini} cedolini per ${response.metadati.dipendenti.length} dipendenti\n` +
          metaInfo
        );
        
        // Reset dopo 3 secondi
        setTimeout(() => {
          handleReset();
        }, 3000);
      } else {
        toast.error(
          `Errore importazione Libro Unico:\n${response.errori.join('\n')}`
        );
      }
    } catch (error) {
      console.error('Errore importazione libro unico:', error);
      const apiError = error as { response?: { data?: { detail?: string; errori?: string[] } } };
      const errori = apiError.response?.data?.errori || [];
      const detail = apiError.response?.data?.detail || 'Errore durante l\'importazione del Libro Unico';
      
      toast.error(
        errori.length > 0 
          ? `Errori:\n${errori.join('\n')}`
          : detail
      );
    } finally {
      setImportingLibroUnico(false);
    }
  };

  const handleSearchFascicoli = async (searchTerm: string) => {
    if (!searchTerm || searchTerm.length < 2) {
      setFascicoloOptions([]);
      return;
    }

    setFascicoloLoading(true);
    try {
      const response = await fascicoliApi.list({ search: searchTerm, page: 1, page_size: 20 });
      setFascicoloOptions(response.results);
    } catch (error) {
      console.error('Errore ricerca fascicoli:', error);
    } finally {
      setFascicoloLoading(false);
    }
  };

  // Estrai liste datori e dipendenti univoci
  const getDatoriList = () => {
    if (!preview) return [];
    const datori = new Map<string, any>();
    [...preview.validi, ...preview.duplicati].forEach((c) => {
      if (!datori.has(c.datore.codice_fiscale)) {
        datori.set(c.datore.codice_fiscale, c.datore);
      }
    });
    return Array.from(datori.values());
  };

  const getDipendentiList = () => {
    if (!preview) return [];
    const dipendenti = new Map<string, any>();
    [...preview.validi, ...preview.duplicati].forEach((c) => {
      if (!dipendenti.has(c.lavoratore.codice_fiscale)) {
        dipendenti.set(c.lavoratore.codice_fiscale, c.lavoratore);
      }
    });
    return Array.from(dipendenti.values());
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/documenti')} sx={{ mr: 2 }}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4">Importa Cedolini Paga</Typography>
      </Box>

      {/* Istruzioni */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2" paragraph>
          <strong>📋 Istruzioni per l'importazione:</strong>
        </Typography>
        <ul style={{ marginTop: 0, paddingLeft: 20, marginBottom: 0 }}>
          <li>
            Seleziona un file <strong>ZIP contenente PDF</strong> oppure un <strong>singolo PDF</strong>
          </li>
          <li>
            I PDF cedolino devono seguire il pattern: <code>CF - ANNO - COGNOME NOME (CF-MATRICOLA).pdf</code>
          </li>
          <li>
            Il sistema estrarrà automaticamente i dati dal PDF e creerà:
            <ul>
              <li>Anagrafica dipendente (se non esiste)</li>
              <li>Cliente datore di lavoro (se non esiste)</li>
              <li>Voce titolario intestata al dipendente (HR-PERS → Dossier Dipendente)</li>
              <li>Fascicolo "Paghe mese anno" (se non specificato diversamente)</li>
              <li>Documento BPAG con tutti gli attributi</li>
            </ul>
          </li>
          <li>
            <strong>💾 Dati salvati come attributi documento:</strong> Tipo, Anno, Mese, Mensilità, Dipendente
          </li>
          <li>
            <strong>📝 Dati estratti per riferimento:</strong> Matricola, Matricola INPS, Date (Nascita/Assunzione/Cessazione), Livello, Netto, Nr. Cedolino, Data/Ora
          </li>
        </ul>
      </Alert>

      {/* STEP 1: UPLOAD E ANALISI */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📤 Step 1: Seleziona file e analizza
          </Typography>
          
          <Stack spacing={3}>
            <Box>
              <input
                accept=".zip,.pdf"
                style={{ display: 'none' }}
                id="cedolini-file"
                type="file"
                onChange={handleFileSelect}
                disabled={analyzing || importing}
              />
              <label htmlFor="cedolini-file">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<FileIcon />}
                  disabled={analyzing || importing}
                  fullWidth
                  sx={{ py: 2 }}
                >
                  {selectedFile
                    ? `📁 ${selectedFile.name} (${(selectedFile.size / 1024 / 1024).toFixed(2)} MB)`
                    : '📁 Seleziona file ZIP o PDF'}
                </Button>
              </label>
            </Box>

            <Box display="flex" gap={2} flexDirection="column">
              <Box display="flex" gap={2}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleAnalyze}
                  disabled={!selectedFile || analyzing || importing || importingLibroUnico}
                  startIcon={<UploadIcon />}
                  fullWidth
                >
                  {analyzing ? '🔄 Analisi in corso...' : '🔍 Analizza e importa come Cedolini'}
                </Button>

                {(selectedFile || preview || result) && (
                  <Button
                    variant="outlined"
                    onClick={handleReset}
                    disabled={analyzing || importing || importingLibroUnico}
                  >
                    ↻ Reset
                  </Button>
                )}
              </Box>
              
              {/* Pulsante Importa come Libro Unico */}
              {selectedFile && selectedFile.name.toLowerCase().endsWith('.zip') && (
                <Button
                  variant="contained"
                  color="secondary"
                  onClick={handleImportaLibroUnico}
                  disabled={analyzing || importing || importingLibroUnico}
                  startIcon={<FileIcon />}
                  fullWidth
                >
                  {importingLibroUnico ? '⏳ Importazione Libro Unico...' : '📚 Importa ZIP come Libro Unico'}
                </Button>
              )}
            </Box>

            {(analyzing || importingLibroUnico) && (
              <Box>
                <LinearProgress />
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ mt: 1, display: 'block' }}
                >
                  {analyzing && 'Estrazione e analisi cedolini in corso...'}
                  {importingLibroUnico && 'Importazione Libro Unico in corso...'}
                </Typography>
              </Box>
            )}
            
            {/* Risultato Libro Unico */}
            {libroUnicoResult && (
              <Alert severity={libroUnicoResult.success ? 'success' : 'error'} sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  {libroUnicoResult.success ? '✅ Libro Unico creato con successo!' : '❌ Errore importazione'}
                </Typography>
                
                {libroUnicoResult.success && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2">
                      <strong>Titolo:</strong> {libroUnicoResult.metadati.titolo}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Periodo:</strong> {libroUnicoResult.metadati.periodo}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Cliente:</strong> {libroUnicoResult.metadati.cliente}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Cedolini:</strong> {libroUnicoResult.metadati.num_cedolini}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Dipendenti:</strong> {libroUnicoResult.metadati.dipendenti.length}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Azione:</strong> {libroUnicoResult.azione}
                    </Typography>
                    {libroUnicoResult.duplicato && (
                      <Typography variant="body2" color="warning.main">
                        ⚠️ Trovato duplicato (ID {libroUnicoResult.duplicato_id})
                      </Typography>
                    )}
                  </Box>
                )}
                
                {libroUnicoResult.errori && libroUnicoResult.errori.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" color="error">
                      Errori:
                    </Typography>
                    <ul>
                      {libroUnicoResult.errori.map((err: string, idx: number) => (
                        <li key={idx}><Typography variant="caption">{err}</Typography></li>
                      ))}
                    </ul>
                  </Box>
                )}
              </Alert>
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* STEP 2: PREVIEW AGGREGATA */}
      {preview && !result && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 Step 2: Verifica dati estratti
            </Typography>

            {/* Statistiche aggregate */}
            <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.lighter' }}>
              <Typography variant="h5" gutterBottom>
                📈 Riepilogo analisi
              </Typography>
              <Stack direction="row" spacing={4} flexWrap="wrap">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Totale cedolini
                  </Typography>
                  <Typography variant="h4">{preview.totale}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    ✅ Validi
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {preview.statistiche.totale_validi}
                  </Typography>
                </Box>
                {preview.statistiche.totale_duplicati > 0 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      ⚠️ Duplicati
                    </Typography>
                    <Typography variant="h4" color="warning.main">
                      {preview.statistiche.totale_duplicati}
                    </Typography>
                  </Box>
                )}
                {preview.statistiche.totale_errori > 0 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      ❌ Errori
                    </Typography>
                    <Typography variant="h4" color="error.main">
                      {preview.statistiche.totale_errori}
                    </Typography>
                  </Box>
                )}
              </Stack>
            </Paper>

            {/* Cards statistiche anagrafiche */}
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} mb={3}>
              {/* Datori */}
              <Card sx={{ flex: 1 }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <BusinessIcon color="primary" />
                    <Typography variant="h6">Datori di lavoro</Typography>
                  </Box>
                  <Stack direction="row" spacing={2} mb={2}>
                    <Chip
                      label={`${preview.statistiche.nuovi_datori} nuovi`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`${getDatoriList().length - preview.statistiche.nuovi_datori} esistenti`}
                      color="info"
                      size="small"
                    />
                  </Stack>
                  <Button
                    size="small"
                    endIcon={expandDatori ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    onClick={() => setExpandDatori(!expandDatori)}
                  >
                    {expandDatori ? 'Nascondi' : 'Mostra'} dettagli
                  </Button>
                  <Collapse in={expandDatori}>
                    <List dense sx={{ mt: 2 }}>
                      {getDatoriList().map((datore, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            {datore.esistente ? (
                              <SuccessIcon color="info" />
                            ) : (
                              <WarningIcon color="success" />
                            )}
                          </ListItemIcon>
                          <ListItemText
                            primary={datore.ragione_sociale || datore.codice_fiscale}
                            secondary={`CF: ${datore.codice_fiscale} - ${datore.esistente ? 'Già presente' : 'Nuovo'}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Collapse>
                </CardContent>
              </Card>

              {/* Dipendenti */}
              <Card sx={{ flex: 1 }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <PersonIcon color="secondary" />
                    <Typography variant="h6">Dipendenti</Typography>
                  </Box>
                  <Stack direction="row" spacing={2} mb={2}>
                    <Chip
                      label={`${preview.statistiche.nuovi_dipendenti} nuovi`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`${getDipendentiList().length - preview.statistiche.nuovi_dipendenti} esistenti`}
                      color="info"
                      size="small"
                    />
                  </Stack>
                  <Button
                    size="small"
                    endIcon={expandDipendenti ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    onClick={() => setExpandDipendenti(!expandDipendenti)}
                  >
                    {expandDipendenti ? 'Nascondi' : 'Mostra'} dettagli
                  </Button>
                  <Collapse in={expandDipendenti}>
                    <List dense sx={{ mt: 2 }}>
                      {getDipendentiList().map((dip, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            {dip.esistente ? (
                              <SuccessIcon color="info" />
                            ) : (
                              <WarningIcon color="success" />
                            )}
                          </ListItemIcon>
                          <ListItemText
                            primary={`${dip.cognome} ${dip.nome}`}
                            secondary={`CF: ${dip.codice_fiscale} - ${dip.esistente ? 'Già presente' : 'Nuovo'}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Collapse>
                </CardContent>
              </Card>
            </Stack>

            {/* Elenchi espandibili */}
            {preview.statistiche.totale_validi > 0 && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle1">
                      ✅ Cedolini validi ({preview.statistiche.totale_validi})
                    </Typography>
                    <Button
                      size="small"
                      endIcon={expandValidi ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      onClick={() => setExpandValidi(!expandValidi)}
                    >
                      {expandValidi ? 'Nascondi' : 'Mostra'}
                    </Button>
                  </Box>
                  
                  {expandValidi && (
                    <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
                      <Typography variant="caption">
                        <strong>💡 Legenda mappatura dati:</strong><br />
                        📊 <strong>Attributi DB</strong> = Dati salvati come attributi del documento (ricercabili e filtrabili)<br />
                        📝 <strong>Dati Note</strong> = Informazioni estratte dal PDF disponibili per riferimento
                      </Typography>
                    </Alert>
                  )}
                  
                  <Collapse in={expandValidi}>
                    <Table size="small" sx={{ mt: 2 }}>
                      <TableHead>
                        <TableRow>
                          <TableCell>File</TableCell>
                          <TableCell>Dipendente</TableCell>
                          <TableCell>Periodo</TableCell>
                          <TableCell>Attributi DB</TableCell>
                          <TableCell>Dati Note</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {preview.validi.slice(0, 20).map((c, idx) => (
                          <TableRow key={idx}>
                            <TableCell>
                              <Typography variant="caption" noWrap sx={{ maxWidth: 150, display: 'block' }}>
                                {c.filename}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {`${c.lavoratore.cognome} ${c.lavoratore.nome}`}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                CF: {c.lavoratore.codice_fiscale}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">{c.cedolino.periodo}</Typography>
                              {c.cedolino.livello && (
                                <Typography variant="caption" color="text.secondary">
                                  {c.cedolino.livello}
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Box sx={{ maxWidth: 200 }}>
                                {c.attributi_db && (
                                  <Stack spacing={0.5}>
                                    <Chip label={`Tipo: ${c.attributi_db.tipo}`} size="small" color="primary" variant="outlined" />
                                    <Chip label={`Anno: ${c.attributi_db.anno_riferimento}`} size="small" color="primary" variant="outlined" />
                                    <Chip label={`Mese: ${c.attributi_db.mese_riferimento}`} size="small" color="primary" variant="outlined" />
                                    <Chip label={`Mensilità: ${c.attributi_db.mensilita}`} size="small" color="primary" variant="outlined" />
                                  </Stack>
                                )}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ maxWidth: 200 }}>
                                {c.dati_note && (
                                  <Stack spacing={0.5}>
                                    {c.dati_note.matricola && (
                                      <Typography variant="caption" color="text.secondary">
                                        🆔 Matricola: {c.dati_note.matricola}
                                      </Typography>
                                    )}
                                    {c.dati_note.matricola_inps && (
                                      <Typography variant="caption" color="text.secondary">
                                        📋 INPS: {c.dati_note.matricola_inps}
                                      </Typography>
                                    )}
                                    {c.dati_note.data_nascita && (
                                      <Typography variant="caption" color="text.secondary">
                                        🎂 Nato: {c.dati_note.data_nascita}
                                      </Typography>
                                    )}
                                    {c.dati_note.data_assunzione && (
                                      <Typography variant="caption" color="text.secondary">
                                        📅 Assunto: {c.dati_note.data_assunzione}
                                      </Typography>
                                    )}
                                    {c.dati_note.data_cessazione && (
                                      <Typography variant="caption" color="error.main">
                                        🚪 Cessato: {c.dati_note.data_cessazione}
                                      </Typography>
                                    )}
                                    {c.dati_note.netto && (
                                      <Typography variant="caption" color="success.main" sx={{ fontWeight: 'bold' }}>
                                        💰 Netto: € {c.dati_note.netto}
                                      </Typography>
                                    )}
                                    {c.dati_note.numero_cedolino && (
                                      <Typography variant="caption" color="primary.main">
                                        🔢 Nr: {c.dati_note.numero_cedolino}
                                      </Typography>
                                    )}
                                    {c.dati_note.data_ora_cedolino && (
                                      <Typography variant="caption" color="text.secondary">
                                        🕒 {c.dati_note.data_ora_cedolino}
                                      </Typography>
                                    )}
                                  </Stack>
                                )}
                              </Box>
                            </TableCell>
                          </TableRow>
                        ))}
                        {preview.validi.length > 20 && (
                          <TableRow>
                            <TableCell colSpan={5} align="center">
                              <Typography variant="caption" color="text.secondary">
                                ... e altri {preview.validi.length - 20} cedolini
                              </Typography>
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </Collapse>
                </CardContent>
              </Card>
            )}

            {preview.statistiche.totale_duplicati > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="subtitle1">
                    ⚠️ Cedolini duplicati rilevati ({preview.statistiche.totale_duplicati})
                  </Typography>
                  <Button
                    size="small"
                    endIcon={expandDuplicati ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    onClick={() => setExpandDuplicati(!expandDuplicati)}
                  >
                    {expandDuplicati ? 'Nascondi' : 'Mostra'}
                  </Button>
                </Box>
                <Collapse in={expandDuplicati}>
                  <List dense sx={{ mt: 2 }}>
                    {preview.duplicati.map((c, idx) => (
                      <ListItem key={idx}>
                        <ListItemIcon>
                          <WarningIcon color="warning" />
                        </ListItemIcon>
                        <ListItemText
                          primary={c.filename}
                          secondary={`${c.lavoratore.cognome} ${c.lavoratore.nome} - ${c.cedolino.periodo} (Documento ID: ${c.documento_duplicato_id})`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Collapse>
              </Alert>
            )}

            {preview.statistiche.totale_errori > 0 && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="subtitle1">
                    ❌ File non processabili ({preview.statistiche.totale_errori})
                  </Typography>
                  <Button
                    size="small"
                    endIcon={expandErrori ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    onClick={() => setExpandErrori(!expandErrori)}
                  >
                    {expandErrori ? 'Nascondi' : 'Mostra'}
                  </Button>
                </Box>
                <Collapse in={expandErrori}>
                  <List dense sx={{ mt: 2 }}>
                    {preview.errori.map((err, idx) => (
                      <ListItem key={idx}>
                        <ListItemIcon>
                          <ErrorIcon color="error" />
                        </ListItemIcon>
                        <ListItemText
                          primary={err.filename}
                          secondary={err.error}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Collapse>
              </Alert>
            )}

            <Divider sx={{ my: 3 }} />

            {/* Configurazione importazione */}
            <Typography variant="h6" gutterBottom>
              ⚙️ Configurazione importazione
            </Typography>

            <Stack spacing={3}>
              {/* Fascicolo target */}
              <Box>
                <FormControl fullWidth>
                  <Autocomplete
                    options={fascicoloOptions}
                    value={fascicolo}
                    onChange={(_, newValue) => setFascicolo(newValue)}
                    onInputChange={(_, value) => handleSearchFascicoli(value)}
                    loading={fascicoloLoading}
                    getOptionLabel={(option) => `${option.codice} - ${option.titolo}`}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Fascicolo destinazione (opzionale)"
                        helperText="Lascia vuoto per usare fascicolo automatico 'Paghe mese anno'"
                        InputProps={{
                          ...params.InputProps,
                          startAdornment: <FolderIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                        }}
                      />
                    )}
                  />
                </FormControl>
              </Box>

              {/* Gestione duplicati */}
              {preview.statistiche.totale_duplicati > 0 && (
                <Box>
                  <FormControl component="fieldset">
                    <FormLabel component="legend">
                      Gestione duplicati
                    </FormLabel>
                    <RadioGroup
                      value={duplicatePolicy}
                      onChange={(e) => setDuplicatePolicy(e.target.value as 'skip' | 'replace' | 'add')}
                    >
                      <FormControlLabel
                        value="skip"
                        control={<Radio />}
                        label="Salta duplicati (non importare)"
                      />
                      <FormControlLabel
                        value="replace"
                        control={<Radio />}
                        label="Sostituisci duplicati (aggiorna documenti esistenti)"
                      />
                      <FormControlLabel
                        value="add"
                        control={<Radio />}
                        label="Crea comunque duplicati"
                      />
                    </RadioGroup>
                  </FormControl>
                </Box>
              )}

              {/* Pulsante conferma */}
              <Button
                variant="contained"
                color="success"
                size="large"
                onClick={handleConfirmImport}
                disabled={
                  importing ||
                  (preview.statistiche.totale_validi === 0 && preview.statistiche.totale_duplicati === 0)
                }
                fullWidth
              >
                {importing 
                  ? '⏳ Importazione in corso...' 
                  : `✅ Conferma e importa ${preview.statistiche.totale_validi + preview.statistiche.totale_duplicati} cedolini`
                }
              </Button>

              {importing && (
                <Box>
                  <LinearProgress />
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ mt: 1, display: 'block', textAlign: 'center' }}
                  >
                    Creazione documenti in corso, attendere...
                  </Typography>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* STEP 3: RISULTATI FINALI */}
      {result && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              ✅ Importazione completata
            </Typography>

            {/* Alert riepilogativo */}
            {result.created > 0 && result.errors.length === 0 && (
              <Alert severity="success" sx={{ mb: 2 }}>
                <strong>✅ Importazione completata con successo!</strong>
                <br />
                {result.created} cedolini creati
                {result.replaced > 0 && `, ${result.replaced} sostituiti`}
                {result.skipped > 0 && `, ${result.skipped} saltati`}
              </Alert>
            )}
            
            {result.created > 0 && result.errors.length > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <strong>⚠️ Importazione parziale</strong>
                <br />
                {result.created} creati
                {result.replaced > 0 && `, ${result.replaced} sostituiti`}
                {result.skipped > 0 && `, ${result.skipped} saltati`}
                {' - '}{result.errors.length} errori
              </Alert>
            )}
            
            {result.created === 0 && result.errors.length > 0 && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <strong>❌ Importazione fallita</strong>
                <br />
                Nessun cedolino importato. Verificare errori riportati.
              </Alert>
            )}

            {/* Riepilogo numerico */}
            <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
              <Stack direction="row" spacing={4} flexWrap="wrap">
                <Box>
                  <Typography variant="body2" color="text.secondary">Creati</Typography>
                  <Typography variant="h5" color="success.main">{result.created}</Typography>
                </Box>
                {result.replaced > 0 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">Sostituiti</Typography>
                    <Typography variant="h5" color="info.main">{result.replaced}</Typography>
                  </Box>
                )}
                {result.skipped > 0 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">Saltati</Typography>
                    <Typography variant="h5" color="warning.main">{result.skipped}</Typography>
                  </Box>
                )}
                {result.errors.length > 0 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">Errori</Typography>
                    <Typography variant="h5" color="error.main">{result.errors.length}</Typography>
                  </Box>
                )}
              </Stack>
            </Paper>

            {/* Documenti creati */}
            {result.documenti.length > 0 && (
              <Box mb={2}>
                <Typography variant="subtitle1" gutterBottom color="success.main">
                  ✅ Documenti importati ({result.documenti.length})
                </Typography>
                <List dense>
                  {result.documenti.map((doc) => (
                    <ListItem
                      key={doc.id}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                      }}
                    >
                      <ListItemIcon>
                        <SuccessIcon color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary={doc.descrizione}
                        secondary={
                          <>
                            <strong>Codice:</strong> {doc.codice} | <strong>File:</strong> {doc.filename}
                            {doc.action && ` | Azione: ${doc.action === 'sostituito' ? 'Sostituito' : 'Creato'}`}
                          </>
                        }
                        secondaryTypographyProps={{ component: 'span' }}
                      />
                      <Button
                        size="small"
                        onClick={() => navigate(`/documenti/${doc.id}`)}
                      >
                        Visualizza
                      </Button>
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {/* Errori */}
            {result.errors.length > 0 && (
              <Box mb={2}>
                <Typography variant="subtitle1" gutterBottom color="error.main">
                  ❌ Errori ({result.errors.length})
                </Typography>
                <List dense>
                  {result.errors.map((error, index) => (
                    <ListItem
                      key={index}
                      sx={{
                        bgcolor: 'error.lighter',
                        borderRadius: 1,
                        mb: 1,
                      }}
                    >
                      <ListItemIcon>
                        <ErrorIcon color="error" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={error.error}
                        secondary={`File: ${error.filename}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            <Divider sx={{ my: 2 }} />

            <Box display="flex" gap={2} justifyContent="flex-end">
              <Button variant="outlined" onClick={() => navigate('/documenti')}>
                Torna alla Lista Documenti
              </Button>
              <Button variant="contained" onClick={handleReset}>
                Nuova Importazione
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Container>
  );
}
