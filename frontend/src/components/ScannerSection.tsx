import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Alert, AlertTitle, Button, CircularProgress, FormControl, InputLabel, 
  MenuItem, Select, SelectChangeEvent, Slider, Typography, Box, 
  Accordion, AccordionSummary, AccordionDetails, FormControlLabel, Checkbox
} from '@mui/material';
import { 
  Scanner as ScannerIcon, Delete as DeleteIcon, RotateRight as RotateIcon, 
  Merge as MergeIcon, ExpandMore as ExpandMoreIcon, Settings as SettingsIcon 
} from '@mui/icons-material';

const SCANNER_SERVICE_URL = 'http://localhost:8765';

interface Scanner {
  id: string;
  name: string;
  vendor: string;
  model: string;
  type: string;
  capabilities?: {
    duplex: boolean;
    adf: boolean;
    max_dpi: number;
  };
}

interface Scan {
  scan_id: string;
  status: 'scanning' | 'completed' | 'error';
  pages_scanned: number;
  error?: string;
}

interface ScannedPage {
  scan_id: string;
  page_number: number;
  preview_url: string;
}

interface ScannerSectionProps {
  onFileGenerated: (file: File) => void;
  disabled?: boolean;
}

export function ScannerSection({ onFileGenerated, disabled = false }: ScannerSectionProps) {
  const [serviceAvailable, setServiceAvailable] = useState<boolean | null>(null);
  const [scanners, setScanners] = useState<Scanner[]>([]);
  const [selectedScanner, setSelectedScanner] = useState<string>('');
  const [scanning, setScanning] = useState(false);
  const [scannedPages, setScannedPages] = useState<ScannedPage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Parametri di scansione configurabili
  const [dpi, setDpi] = useState<number>(300);
  const [scanMode, setScanMode] = useState<string>('gray');
  const [duplex, setDuplex] = useState<boolean>(true);
  const [brightness, setBrightness] = useState<number>(0);
  const [contrast, setContrast] = useState<number>(0);
  const [optimize, setOptimize] = useState<boolean>(true); // Ottimizzazione attiva per default

  // Verifica disponibilità del servizio scanner all'avvio
  useEffect(() => {
    checkServiceAvailability();
  }, []);

  const checkServiceAvailability = async () => {
    try {
      const response = await axios.get(`${SCANNER_SERVICE_URL}/health`, { timeout: 2000 });
      if (response.data.status === 'ok') {
        setServiceAvailable(true);
        loadScanners();
      } else {
        setServiceAvailable(false);
      }
    } catch (err) {
      console.error('Scanner service not available:', err);
      setServiceAvailable(false);
    }
  };

  const loadScanners = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${SCANNER_SERVICE_URL}/scanners`);
      setScanners(response.data.scanners || []);
      setError(null);
    } catch (err) {
      console.error('Error loading scanners:', err);
      setError('Impossibile caricare la lista degli scanner');
    } finally {
      setLoading(false);
    }
  };

  const handleScannerChange = (event: SelectChangeEvent) => {
    setSelectedScanner(event.target.value);
  };

  const startScan = async () => {
    if (!selectedScanner) {
      setError('Seleziona uno scanner prima di avviare la scansione');
      return;
    }

    try {
      setScanning(true);
      setError(null);

      const response = await axios.post<Scan>(`${SCANNER_SERVICE_URL}/scan`, {
        scanner_id: selectedScanner,
        pages: 0, // 0 = scansiona tutte le pagine dal feeder
        dpi: dpi,
        mode: scanMode,
        duplex: duplex,
        brightness: brightness,
        contrast: contrast,
        optimize: optimize,
      });

      if (response.data.status === 'completed') {
        // Carica le preview delle pagine scansionate
        const pages: ScannedPage[] = [];
        for (let i = 1; i <= response.data.pages_scanned; i++) {
          pages.push({
            scan_id: response.data.scan_id,
            page_number: i,
            preview_url: `${SCANNER_SERVICE_URL}/scan/${response.data.scan_id}/preview/${i}`,
          });
        }
        setScannedPages((prev) => [...prev, ...pages]);
      } else if (response.data.status === 'error') {
        setError(response.data.error || 'Errore durante la scansione');
      }
    } catch (err) {
      console.error('Error starting scan:', err);
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || 'Errore di comunicazione con lo scanner');
      } else {
        setError('Errore imprevisto durante la scansione');
      }
    } finally {
      setScanning(false);
    }
  };

  const removePage = (index: number) => {
    setScannedPages((prev) => prev.filter((_, i) => i !== index));
  };

  const rotatePage = (index: number) => {
    // TODO: Implementare rotazione immagine
    console.log('Rotate page', index);
  };

  const mergeToPdf = async () => {
    if (scannedPages.length === 0) {
      setError('Nessuna pagina da unire');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Raggruppa per scan_id
      const scanIds = Array.from(new Set(scannedPages.map((p) => p.scan_id)));

      // Richiedi merge al servizio
      const response = await axios.post(
        `${SCANNER_SERVICE_URL}/scan/merge`,
        {
          scan_ids: scanIds,
          filename: `scansione_${new Date().toISOString().split('T')[0]}.pdf`,
        },
        {
          responseType: 'blob',
        }
      );

      // Crea File object dal blob
      const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
      const pdfFile = new File([pdfBlob], `scansione_${Date.now()}.pdf`, {
        type: 'application/pdf',
      });

      // Passa il file al componente padre
      onFileGenerated(pdfFile);

      // Pulisci le scansioni
      setScannedPages([]);

      // Cleanup delle scansioni sul server
      for (const scanId of scanIds) {
        try {
          await axios.delete(`${SCANNER_SERVICE_URL}/scan/${scanId}`);
        } catch (err) {
          console.warn('Failed to cleanup scan:', scanId, err);
        }
      }
    } catch (err) {
      console.error('Error merging scans:', err);
      setError('Errore durante la creazione del PDF');
    } finally {
      setLoading(false);
    }
  };

  // Se il servizio non è disponibile, mostra messaggio di errore
  if (serviceAvailable === false) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        <AlertTitle>Servizio Scanner Non Disponibile</AlertTitle>
        Il servizio di scansione non è raggiungibile. Per utilizzare la funzionalità di
        scansione:
        <ol style={{ marginTop: '0.5rem', marginBottom: 0, paddingLeft: '1.5rem' }}>
          <li>Assicurati che il servizio scanner sia avviato</li>
          <li>
            Usa <code>Quick_Start_Scanner.bat</code> nella cartella{' '}
            <code>windows_manager</code>
          </li>
          <li>Oppure avvialo dal WSL Server Manager (opzione D)</li>
        </ol>
      </Alert>
    );
  }

  // Se stiamo ancora verificando la disponibilità
  if (serviceAvailable === null) {
    return (
      <div style={{ textAlign: 'center', padding: '1rem' }}>
        <CircularProgress size={24} />
        <p style={{ marginTop: '0.5rem', color: '#6b7280' }}>
          Verifica servizio scanner...
        </p>
      </div>
    );
  }

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: '0.5rem', padding: '1rem' }}>
      <h3
        style={{
          fontSize: '1rem',
          fontWeight: '600',
          marginBottom: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        <ScannerIcon />
        Scansione Documento
      </h3>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* Selezione scanner */}
        <FormControl fullWidth disabled={disabled || scanning}>
          <InputLabel id="scanner-select-label">Scanner</InputLabel>
          <Select
            labelId="scanner-select-label"
            value={selectedScanner}
            label="Scanner"
            onChange={handleScannerChange}
          >
            {scanners.map((scanner) => (
              <MenuItem key={scanner.id} value={scanner.id}>
                {scanner.name}
                {scanner.capabilities?.duplex && ' (Duplex)'}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Parametri di scansione avanzati */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <SettingsIcon fontSize="small" />
              <Typography variant="body2">Impostazioni Avanzate</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box display="flex" flexDirection="column" gap={2}>
              {/* DPI / Risoluzione */}
              <Box>
                <Typography variant="body2" gutterBottom>
                  Risoluzione (DPI): {dpi}
                </Typography>
                <Slider
                  value={dpi}
                  onChange={(_, value) => setDpi(value as number)}
                  min={75}
                  max={600}
                  step={75}
                  marks={[
                    { value: 75, label: '75' },
                    { value: 150, label: '150' },
                    { value: 300, label: '300' },
                    { value: 600, label: '600' },
                  ]}
                  disabled={disabled || scanning}
                />
              </Box>

              {/* Modalità colore */}
              <FormControl fullWidth disabled={disabled || scanning}>
                <InputLabel id="scan-mode-label">Modalità Colore</InputLabel>
                <Select
                  labelId="scan-mode-label"
                  value={scanMode}
                  label="Modalità Colore"
                  onChange={(e) => setScanMode(e.target.value)}
                >
                  <MenuItem value="gray">Scala di grigi</MenuItem>
                  <MenuItem value="color">Colore</MenuItem>
                  <MenuItem value="lineart">Bianco e nero (lineart)</MenuItem>
                </Select>
              </FormControl>

              {/* Duplex */}
              <FormControl fullWidth disabled={disabled || scanning}>
                <InputLabel id="duplex-label">Fronte/Retro</InputLabel>
                <Select
                  labelId="duplex-label"
                  value={duplex ? 'true' : 'false'}
                  label="Fronte/Retro"
                  onChange={(e) => setDuplex(e.target.value === 'true')}
                >
                  <MenuItem value="true">Automatico (Duplex)</MenuItem>
                  <MenuItem value="false">Solo fronte</MenuItem>
                </Select>
              </FormControl>

              {/* Luminosità */}
              <Box>
                <Typography variant="body2" gutterBottom>
                  Luminosità: {brightness > 0 ? `+${brightness}` : brightness}%
                </Typography>
                <Slider
                  value={brightness}
                  onChange={(_, value) => setBrightness(value as number)}
                  min={-50}
                  max={50}
                  step={5}
                  marks={[
                    { value: -50, label: '-50%' },
                    { value: 0, label: '0%' },
                    { value: 50, label: '+50%' },
                  ]}
                  disabled={disabled || scanning}
                />
              </Box>

              {/* Contrasto */}
              <Box>
                <Typography variant="body2" gutterBottom>
                  Contrasto: {contrast > 0 ? `+${contrast}` : contrast}%
                </Typography>
                <Slider
                  value={contrast}
                  onChange={(_, value) => setContrast(value as number)}
                  min={-50}
                  max={50}
                  step={5}
                  marks={[
                    { value: -50, label: '-50%' },
                    { value: 0, label: '0%' },
                    { value: 50, label: '+50%' },
                  ]}
                  disabled={disabled || scanning}
                />
              </Box>

              {/* Ottimizzazione B/N */}
              <Box>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={optimize}
                      onChange={(e) => setOptimize(e.target.checked)}
                      disabled={disabled || scanning}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2" fontWeight="600">
                        Ottimizza per B/N leggibile
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Converte in bianco/nero puro, aumenta contrasto e riduce dimensioni file (~70% più piccolo)
                      </Typography>
                    </Box>
                  }
                />
              </Box>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Pulsante scansione */}
        <Button
          variant="contained"
          color="primary"
          onClick={startScan}
          disabled={disabled || !selectedScanner || scanning || loading}
          startIcon={scanning ? <CircularProgress size={20} /> : <ScannerIcon />}
          fullWidth
        >
          {scanning ? 'Scansione in corso...' : 'Avvia Scansione'}
        </Button>

        {/* Preview pagine scansionate */}
        {scannedPages.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              Pagine scansionate ({scannedPages.length})
            </h4>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
                gap: '0.5rem',
                maxHeight: '300px',
                overflowY: 'auto',
                padding: '0.5rem',
                backgroundColor: '#f9fafb',
                borderRadius: '0.375rem',
              }}
            >
              {scannedPages.map((page, index) => (
                <div
                  key={`${page.scan_id}-${page.page_number}`}
                  style={{
                    position: 'relative',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.25rem',
                    overflow: 'hidden',
                  }}
                >
                  <img
                    src={page.preview_url}
                    alt={`Pagina ${index + 1}`}
                    onClick={() => window.open(page.preview_url, '_blank')}
                    style={{
                      width: '100%',
                      height: '150px',
                      objectFit: 'cover',
                      cursor: 'pointer',
                    }}
                    title="Clicca per aprire in una nuova scheda"
                  />
                  <div
                    style={{
                      position: 'absolute',
                      top: '0.25rem',
                      right: '0.25rem',
                      display: 'flex',
                      gap: '0.25rem',
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => rotatePage(index)}
                      style={{
                        padding: '0.25rem',
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        border: 'none',
                        borderRadius: '0.25rem',
                        cursor: 'pointer',
                      }}
                      title="Ruota"
                    >
                      <RotateIcon style={{ fontSize: '1rem' }} />
                    </button>
                    <button
                      type="button"
                      onClick={() => removePage(index)}
                      style={{
                        padding: '0.25rem',
                        backgroundColor: 'rgba(220, 53, 69, 0.9)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '0.25rem',
                        cursor: 'pointer',
                      }}
                      title="Elimina"
                    >
                      <DeleteIcon style={{ fontSize: '1rem' }} />
                    </button>
                  </div>
                  <div
                    style={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      padding: '0.25rem',
                      backgroundColor: 'rgba(0, 0, 0, 0.7)',
                      color: 'white',
                      fontSize: '0.75rem',
                      textAlign: 'center',
                    }}
                  >
                    Pagina {index + 1}
                  </div>
                </div>
              ))}
            </div>

            {/* Pulsante unisci in PDF */}
            <Button
              variant="contained"
              color="success"
              onClick={mergeToPdf}
              disabled={disabled || loading}
              startIcon={loading ? <CircularProgress size={20} /> : <MergeIcon />}
              fullWidth
              sx={{ mt: 1 }}
            >
              {loading ? 'Creazione PDF in corso...' : 'Unisci e Allega come PDF'}
            </Button>
          </div>
        )}

        {/* Informazioni parametri correnti */}
        <div
          style={{
            fontSize: '0.75rem',
            color: '#6b7280',
            padding: '0.5rem',
            backgroundColor: '#f9fafb',
            borderRadius: '0.25rem',
          }}
        >
          <strong>Parametri scansione correnti:</strong>
          <ul style={{ margin: '0.25rem 0', paddingLeft: '1.5rem' }}>
            <li>Risoluzione: {dpi} DPI</li>
            <li>Modalità: {scanMode === 'gray' ? 'Scala di grigi' : scanMode === 'color' ? 'Colore' : 'Bianco e nero'}</li>
            <li>Formato: A4</li>
            <li>Fronte/retro: {duplex ? 'Automatico (Duplex)' : 'Solo fronte'}</li>
            <li>Luminosità: {brightness > 0 ? `+${brightness}` : brightness}%</li>
            <li>Contrasto: {contrast > 0 ? `+${contrast}` : contrast}%</li>
            <li>Ottimizzazione: {optimize ? '✅ Attiva (B/N, contrasto aumentato, file ridotti)' : '❌ Disattivata'}</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
