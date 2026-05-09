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
  Stack,
  IconButton,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  FolderZip as ZipIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  OpenInNew as OpenIcon,
} from '@mui/icons-material';
import { documentiApi } from '@/api/documenti';
import { toast } from 'react-toastify';

type AzioneDuplicati = 'sostituisci' | 'duplica' | 'skip';

type ImportResult = Awaited<ReturnType<typeof documentiApi.importaZipCU>>;

export function ImportaArchivioCUPage() {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [azioneDuplicati, setAzioneDuplicati] = useState<AzioneDuplicati>('duplica');
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.zip')) {
      toast.error('Seleziona un file ZIP');
      return;
    }
    setSelectedFile(file);
    setResult(null);
  };

  const handleImporta = async () => {
    if (!selectedFile) {
      toast.error('Seleziona un file ZIP');
      return;
    }

    setImporting(true);
    setResult(null);

    try {
      const response = await documentiApi.importaZipCU(selectedFile, azioneDuplicati);
      setResult(response);

      if (response.success) {
        toast.success(
          `Archivio CU importato: ${response.metadati.num_certificazioni} certificazioni`
        );
      } else {
        toast.error('Importazione non riuscita');
      }
    } catch (error) {
      const apiError = error as { response?: { data?: { detail?: string; errori?: string[] } } };
      const errori = apiError.response?.data?.errori ?? [];
      const detail = apiError.response?.data?.detail ?? "Errore durante l'importazione";
      const msg = errori.length > 0 ? errori.join('\n') : detail;
      toast.error(msg);
      setResult({ success: false, documento_id: undefined, duplicato: false, azione: '', metadati: { titolo: '', anno_imposta: 0, datore: '', datore_cf: '', num_certificazioni: 0, dipendenti: [] }, errori: [msg] } as unknown as ImportResult);
    } finally {
      setImporting(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setAzioneDuplicati('duplica');
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/import')} sx={{ mr: 2 }}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4">Importa Archivio CU</Typography>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2" paragraph sx={{ mb: 1 }}>
          <strong>Importazione ZIP come documento unico (CU-ZIP)</strong>
        </Typography>
        <Typography variant="body2" component="div">
          L'intero file ZIP verrà salvato come singolo documento <strong>Archivio CU</strong> associato
          al committente (datore di lavoro). Il sistema estrarrà automaticamente:
          <ul style={{ marginTop: 4, marginBottom: 4, paddingLeft: 20 }}>
            <li>Anno imposta</li>
            <li>Dati del datore di lavoro (committente)</li>
            <li>Elenco dei dipendenti contenuti nel ZIP</li>
          </ul>
          <strong>Attenzione:</strong> il committente deve essere già presente in anagrafica.
        </Typography>
      </Alert>

      {/* Upload e opzioni */}
      {!result && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Stack spacing={3}>
              {/* Selezione file */}
              <Box>
                <input
                  accept=".zip"
                  style={{ display: 'none' }}
                  id="archivio-cu-file"
                  type="file"
                  onChange={handleFileSelect}
                  disabled={importing}
                />
                <label htmlFor="archivio-cu-file">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<ZipIcon />}
                    disabled={importing}
                    fullWidth
                    sx={{ py: 2 }}
                  >
                    {selectedFile
                      ? `${selectedFile.name} (${(selectedFile.size / 1024 / 1024).toFixed(2)} MB)`
                      : 'Seleziona file ZIP'}
                  </Button>
                </label>
              </Box>

              {/* Azione duplicati */}
              <FormControl>
                <FormLabel>Azione se esiste già un archivio per lo stesso anno e committente</FormLabel>
                <RadioGroup
                  row
                  value={azioneDuplicati}
                  onChange={(e) => setAzioneDuplicati(e.target.value as AzioneDuplicati)}
                >
                  <FormControlLabel value="duplica" control={<Radio />} label="Duplica" />
                  <FormControlLabel value="sostituisci" control={<Radio />} label="Sostituisci" />
                  <FormControlLabel value="skip" control={<Radio />} label="Salta" />
                </RadioGroup>
              </FormControl>

              {/* Pulsante importa */}
              <Box display="flex" gap={2} justifyContent="flex-end">
                <Button variant="outlined" onClick={() => navigate('/import')} disabled={importing}>
                  Annulla
                </Button>
                <Button
                  variant="contained"
                  onClick={handleImporta}
                  disabled={!selectedFile || importing}
                  startIcon={importing ? undefined : <ZipIcon />}
                >
                  {importing ? 'Importazione in corso...' : 'Importa Archivio CU'}
                </Button>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Risultato */}
      {result && (
        <Card>
          <CardContent>
            {result.success ? (
              <Stack spacing={2}>
                <Box display="flex" alignItems="center" gap={1}>
                  <SuccessIcon color="success" />
                  <Typography variant="h6" color="success.main">
                    Importazione completata
                  </Typography>
                  <Chip
                    label={result.azione}
                    size="small"
                    color={result.duplicato ? 'warning' : 'success'}
                    sx={{ ml: 1 }}
                  />
                </Box>

                <Divider />

                <Box>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Documento creato
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {result.metadati.titolo}
                  </Typography>
                </Box>

                <Box display="flex" gap={4} flexWrap="wrap">
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Anno imposta
                    </Typography>
                    <Typography variant="body2">{result.metadati.anno_imposta}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Committente (CF)
                    </Typography>
                    <Typography variant="body2">{result.metadati.datore_cf}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Certificazioni
                    </Typography>
                    <Typography variant="body2">{result.metadati.num_certificazioni}</Typography>
                  </Box>
                </Box>

                {result.metadati.dipendenti.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Dipendenti ({result.metadati.dipendenti.length})
                    </Typography>
                    <List dense disablePadding>
                      {result.metadati.dipendenti.map((nome) => (
                        <ListItem key={nome} disableGutters disablePadding>
                          <ListItemText primary={nome} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                <Box display="flex" gap={2} justifyContent="flex-end" pt={1}>
                  <Button variant="outlined" onClick={handleReset}>
                    Nuova importazione
                  </Button>
                  {result.documento_id && (
                    <Button
                      variant="contained"
                      endIcon={<OpenIcon />}
                      onClick={() => navigate(`/documenti/${result.documento_id}`)}
                    >
                      Apri documento
                    </Button>
                  )}
                </Box>
              </Stack>
            ) : (
              <Stack spacing={2}>
                <Box display="flex" alignItems="center" gap={1}>
                  <ErrorIcon color="error" />
                  <Typography variant="h6" color="error">
                    Importazione non riuscita
                  </Typography>
                </Box>

                {result.errori.length > 0 && (
                  <Alert severity="error">
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {result.errori.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  </Alert>
                )}

                <Box display="flex" justifyContent="flex-end">
                  <Button variant="outlined" onClick={handleReset}>
                    Riprova
                  </Button>
                </Box>
              </Stack>
            )}
          </CardContent>
        </Card>
      )}
    </Container>
  );
}
