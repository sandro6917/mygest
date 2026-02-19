/**
 * Import Selection Page
 * Step 1: Selezione tipo importazione + upload file
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActionArea,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as PdfIcon,
  FolderZip as ZipIcon,
  AttachMoney as MoneyIcon,
  Work as WorkIcon,
  Assignment as AssignmentIcon,
  Receipt as ReceiptIcon,
  Article as ArticleIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { importApi } from '@/api/import';
import type { ImporterType, TipoImportazione } from '@/api/import';

// Icone per tipo importazione
const TIPO_ICONS: Record<TipoImportazione, React.ReactElement> = {
  cedolini: <WorkIcon fontSize="large" />,
  unilav: <AssignmentIcon fontSize="large" />,
  f24: <MoneyIcon fontSize="large" />,
  dichiarazioni_fiscali: <ArticleIcon fontSize="large" />,
  contratti: <ReceiptIcon fontSize="large" />,
  fatture: <ReceiptIcon fontSize="large" />,
};

// Descrizioni tipo importazione
const TIPO_DESCRIPTIONS: Record<TipoImportazione, string> = {
  cedolini: 'Importa cedolini paga in formato PDF o ZIP contenente multipli cedolini',
  unilav: 'Importa comunicazioni UNILAV (assunzioni, proroghe, trasformazioni, cessazioni)',
  f24: 'Importa modelli F24 per versamenti fiscali e contributivi',
  dichiarazioni_fiscali: 'Importa dichiarazioni fiscali (730, Unico, IVA, etc.)',
  contratti: 'Importa contratti di lavoro, collaborazione, consulenza',
  fatture: 'Importa fatture attive e passive',
};

export const ImportSelectionPage: React.FC = () => {
  const navigate = useNavigate();

  const [tipiDisponibili, setTipiDisponibili] = useState<ImporterType[]>([]);
  const [loadingTipi, setLoadingTipi] = useState(true);
  const [tipoSelezionato, setTipoSelezionato] = useState<TipoImportazione | null>(null);
  const [fileSelezionato, setFileSelezionato] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Carica tipi disponibili
  useEffect(() => {
    loadTipiDisponibili();
  }, []);

  const loadTipiDisponibili = async () => {
    try {
      const tipi = await importApi.getTypes();
      setTipiDisponibili(tipi);
    } catch (error) {
      console.error('Errore caricamento tipi:', error);
      toast.error('Errore caricamento tipi importazione');
    } finally {
      setLoadingTipi(false);
    }
  };

  const handleTipoSelect = (tipo: TipoImportazione) => {
    setTipoSelezionato(tipo);
    setFileSelezionato(null); // Reset file quando cambia tipo
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validazione estensione
    const tipoConfig = tipiDisponibili.find((t) => t.tipo === tipoSelezionato);
    if (!tipoConfig) return;

    const fileExt = `.${file.name.split('.').pop()?.toLowerCase()}`;
    if (!tipoConfig.supported_extensions.includes(fileExt)) {
      toast.error(
        `Estensione ${fileExt} non supportata. ` +
        `Estensioni valide: ${tipoConfig.supported_extensions.join(', ')}`
      );
      return;
    }

    // Validazione dimensione
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > tipoConfig.max_file_size_mb) {
      toast.error(
        `File troppo grande: ${fileSizeMB.toFixed(1)}MB. ` +
        `Dimensione massima: ${tipoConfig.max_file_size_mb}MB`
      );
      return;
    }

    setFileSelezionato(file);
  };

  const handleUpload = async () => {
    if (!tipoSelezionato || !fileSelezionato) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simula progress (reale progress richiede onUploadProgress in axios)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const session = await importApi.createSession({
        tipo_importazione: tipoSelezionato,
        file: fileSelezionato,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      toast.success(
        `Importazione avviata! Estratti ${session.num_documenti_totali} documenti.`
      );

      // Redirect a lista documenti
      setTimeout(() => {
        navigate(`/import/${session.uuid}/documents`);
      }, 500);

    } catch (error: any) {
      console.error('Errore upload:', error);
      toast.error(
        error.response?.data?.error || 
        error.response?.data?.file?.[0] ||
        'Errore durante l\'upload del file'
      );
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  // Info tipo selezionato
  const tipoConfig = tipiDisponibili.find((t) => t.tipo === tipoSelezionato);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Importa Documenti
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Seleziona il tipo di documento da importare e carica il file
        </Typography>
      </Box>

      {/* Loading tipi */}
      {loadingTipi && (
        <Box display="flex" justifyContent="center" py={8}>
          <CircularProgress />
        </Box>
      )}

      {/* Selezione tipo */}
      {!loadingTipi && (
        <>
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              1. Seleziona Tipo Importazione
            </Typography>

            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
                gap: 2,
                mt: 1,
              }}
            >
              {tipiDisponibili.map((tipo) => (
                <Card
                  key={tipo.tipo}
                  variant={tipoSelezionato === tipo.tipo ? 'elevation' : 'outlined'}
                  sx={{
                    height: '100%',
                    border: tipoSelezionato === tipo.tipo ? 2 : 1,
                    borderColor: tipoSelezionato === tipo.tipo ? 'primary.main' : 'divider',
                  }}
                >
                    <CardActionArea
                      onClick={() => handleTipoSelect(tipo.tipo)}
                      sx={{ height: '100%' }}
                    >
                      <CardContent>
                        <Box display="flex" alignItems="center" mb={2}>
                          <Box
                            sx={{
                              color: tipoSelezionato === tipo.tipo ? 'primary.main' : 'action.active',
                              mr: 2,
                            }}
                          >
                            {TIPO_ICONS[tipo.tipo]}
                          </Box>
                          <Box flex={1}>
                            <Typography variant="h6">
                              {tipo.display_name}
                            </Typography>
                            {tipoSelezionato === tipo.tipo && (
                              <CheckIcon color="primary" sx={{ ml: 'auto' }} />
                            )}
                          </Box>
                        </Box>

                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {TIPO_DESCRIPTIONS[tipo.tipo]}
                        </Typography>

                        <Box mt={2}>
                          <Chip
                            label={tipo.batch_mode ? 'Multi-documento' : 'Singolo'}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 1 }}
                          />
                          <Chip
                            label={tipo.supported_extensions.join(', ')}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </CardContent>
                    </CardActionArea>
                  </Card>
                ))}
              </Box>
            </Paper>

          {/* Upload file */}
          {tipoSelezionato && tipoConfig && (
            <Paper sx={{ p: 3, mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                2. Carica File
              </Typography>

              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Estensioni supportate:</strong> {tipoConfig.supported_extensions.join(', ')}
                  <br />
                  <strong>Dimensione massima:</strong> {tipoConfig.max_file_size_mb}MB
                  {tipoConfig.batch_mode && (
                    <>
                      <br />
                      <strong>Modalità batch:</strong> Puoi caricare un file ZIP contenente multipli documenti
                    </>
                  )}
                </Typography>
              </Alert>

              <Box
                sx={{
                  border: 2,
                  borderStyle: 'dashed',
                  borderColor: fileSelezionato ? 'primary.main' : 'divider',
                  borderRadius: 2,
                  p: 6,  // ✅ Aumentato da 4 a 6
                  minHeight: 280,  // ✅ Altezza minima garantita
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  bgcolor: fileSelezionato ? 'action.hover' : 'background.default',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    bgcolor: 'action.hover',
                    borderColor: 'primary.main',
                    transform: 'scale(1.01)',
                  },
                }}
                component="label"
              >
                <input
                  type="file"
                  hidden
                  accept={tipoConfig.supported_extensions.join(',')}
                  onChange={handleFileSelect}
                  disabled={uploading}
                />

                {!fileSelezionato ? (
                  <>
                    <UploadIcon sx={{ fontSize: 80, color: 'action.active', mb: 3 }} />
                    <Typography variant="h5" gutterBottom fontWeight="medium">
                      Clicca per selezionare il file
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      oppure trascina il file qui
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 2 }}>
                      {tipoConfig.supported_extensions.join(', ')} • Max {tipoConfig.max_file_size_mb}MB
                    </Typography>
                  </>
                ) : (
                  <>
                    {fileSelezionato.name.endsWith('.zip') ? (
                      <ZipIcon sx={{ fontSize: 80, color: 'primary.main', mb: 3 }} />
                    ) : (
                      <PdfIcon sx={{ fontSize: 80, color: 'primary.main', mb: 3 }} />
                    )}
                    <Typography variant="h5" gutterBottom fontWeight="medium" color="primary">
                      {fileSelezionato.name}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {(fileSelezionato.size / 1024 / 1024).toFixed(2)} MB
                    </Typography>
                    {!uploading && (
                      <Button 
                        variant="outlined" 
                        size="small" 
                        sx={{ mt: 2 }}
                        onClick={(e) => {
                          e.preventDefault();
                          setFileSelezionato(null);
                        }}
                      >
                        Clicca per cambiare file
                      </Button>
                    )}
                  </>
                )}
              </Box>

              {/* Progress upload */}
              {uploading && (
                <Box sx={{ mt: 3 }}>
                  <LinearProgress variant="determinate" value={uploadProgress} />
                  <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
                    {uploadProgress < 90 ? 'Caricamento...' : 'Elaborazione documenti...'}
                  </Typography>
                </Box>
              )}

              {/* Azioni */}
              <Box display="flex" justifyContent="flex-end" gap={2} mt={3}>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setTipoSelezionato(null);
                    setFileSelezionato(null);
                  }}
                  disabled={uploading}
                >
                  Annulla
                </Button>
                <Button
                  variant="contained"
                  startIcon={uploading ? <CircularProgress size={20} /> : <UploadIcon />}
                  onClick={handleUpload}
                  disabled={!fileSelezionato || uploading}
                >
                  {uploading ? 'Caricamento...' : 'Avvia Importazione'}
                </Button>
              </Box>
            </Paper>
          )}

          {/* Info aggiuntive */}
          {tipoSelezionato && tipoConfig && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Informazioni
              </Typography>

              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Estrazione automatica dati"
                    secondary="Il sistema estrarrà automaticamente i dati dai documenti"
                  />
                </ListItem>

                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Match anagrafiche"
                    secondary="Le anagrafiche verranno ricercate automaticamente nel database"
                  />
                </ListItem>

                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Preview prima dell'importazione"
                    secondary="Potrai verificare e modificare i dati estratti prima di confermare"
                  />
                </ListItem>

                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Importazione selettiva"
                    secondary="Potrai scegliere quali documenti importare e quali saltare"
                  />
                </ListItem>
              </List>
            </Paper>
          )}
        </>
      )}
    </Container>
  );
};
