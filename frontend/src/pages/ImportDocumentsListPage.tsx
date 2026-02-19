import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  LinearProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
  Preview as PreviewIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  ArrowBack as ArrowBackIcon,
  Warning as WarningIcon,
  PlayArrow as PlayArrowIcon,
  SkipNext as SkipNextIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { 
  importApi, 
  type ImportSessionDetail, 
  type StatoDocumento,
  type DuplicateCheckResult,
} from '@/api/import';
import { documentiApi } from '@/api/documenti';

const STATO_COLORS: Record<StatoDocumento, 'default' | 'success' | 'error' | 'warning'> = {
  pending: 'warning',
  imported: 'success',
  skipped: 'default',
  error: 'error',
};

const STATO_ICONS: Record<StatoDocumento, React.ReactElement> = {
  pending: <PendingIcon />,
  imported: <CheckCircleIcon />,
  skipped: <CancelIcon />,
  error: <ErrorIcon />,
};

const STATO_LABELS: Record<StatoDocumento, string> = {
  pending: 'In attesa',
  imported: 'Importato',
  skipped: 'Saltato',
  error: 'Errore',
};

export const ImportDocumentsListPage: React.FC = () => {
  const { sessionUuid } = useParams<{ sessionUuid: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<ImportSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [filtroStato, setFiltroStato] = useState<StatoDocumento | 'all'>('all');
  const [duplicatesCheck, setDuplicatesCheck] = useState<Record<string, DuplicateCheckResult>>({});
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);
  const [processingBatch, setProcessingBatch] = useState(false);

  const loadSession = async () => {
    if (!sessionUuid) return;

    try {
      setLoading(true);
      const data = await importApi.getSession(sessionUuid);
      setSession(data);
    } catch (error: any) {
      console.error('Errore caricamento sessione:', error);
      toast.error(error.response?.data?.detail || 'Errore caricamento sessione');
      navigate('/import');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, [sessionUuid]);

  useEffect(() => {
    // Auto-check duplicati quando la sessione è caricata
    if (session && Object.keys(duplicatesCheck).length === 0) {
      checkAllDuplicates();
    }
  }, [session]);

  const checkAllDuplicates = async () => {
    if (!sessionUuid) return;

    try {
      setCheckingDuplicates(true);
      const result = await importApi.checkDuplicates(sessionUuid);
      setDuplicatesCheck(result.duplicates);
    } catch (error: any) {
      console.error('Errore check duplicati:', error);
      toast.error('Errore durante la verifica dei duplicati');
    } finally {
      setCheckingDuplicates(false);
    }
  };

  const handleImportaTuttiNuovi = async () => {
    if (!sessionUuid || !session) return;
    
    const nuovi = session.documents.filter(
      (doc) => doc.stato === 'pending' && !duplicatesCheck[doc.uuid]?.is_duplicate
    );

    if (nuovi.length === 0) {
      toast.info('Nessun documento nuovo da importare');
      return;
    }

    if (!window.confirm(`Importare ${nuovi.length} documenti nuovi?`)) {
      return;
    }

    setProcessingBatch(true);
    let importati = 0;
    let errori = 0;

    for (const doc of nuovi) {
      try {
        await importApi.createDocument(sessionUuid, doc.uuid);
        importati++;
      } catch (error) {
        errori++;
      }
    }

    toast.success(`Importati ${importati} documenti. Errori: ${errori}`);
    setProcessingBatch(false);
    loadSession();
  };

  const handleSaltaTuttiDuplicati = async () => {
    if (!sessionUuid || !session) return;

    const duplicati = session.documents.filter(
      (doc) => doc.stato === 'pending' && duplicatesCheck[doc.uuid]?.is_duplicate
    );

    if (duplicati.length === 0) {
      toast.info('Nessun duplicato da saltare');
      return;
    }

    if (!window.confirm(`Saltare ${duplicati.length} documenti duplicati?`)) {
      return;
    }

    setProcessingBatch(true);
    let saltati = 0;

    for (const doc of duplicati) {
      try {
        await importApi.skipDocument(sessionUuid, doc.uuid);
        saltati++;
      } catch (error) {
        console.error('Errore skip:', error);
      }
    }

    toast.success(`Saltati ${saltati} documenti duplicati`);
    setProcessingBatch(false);
    loadSession();
  };

  const handleSalvaZipLibroUnico = async () => {
    if (!session || !session.file_originale) {
      toast.error('File ZIP non disponibile');
      return;
    }
    
    if (!window.confirm(
      'Salvare l\'intero ZIP come documento Libro Unico?\n\n' +
      'Verrà creato un singolo documento LIBUNI contenente tutti i cedolini del periodo.'
    )) {
      return;
    }
    
    setProcessingBatch(true);
    
    try {
      // Fetch del file ZIP originale dalla sessione
      const response = await fetch(session.file_originale);
      const blob = await response.blob();
      const file = new File([blob], session.file_originale_nome || 'cedolini.zip', { type: 'application/zip' });
      
      // Chiama l'API per creare il Libro Unico
      const result = await documentiApi.importaZipLibroUnico(file, 'duplica');
      
      if (result.success) {
        toast.success(
          `✅ Libro Unico creato con successo!\n` +
          `${result.metadati.titolo}\n` +
          `${result.metadati.num_cedolini} cedolini - ${result.metadati.dipendenti.length} dipendenti`
        );
        
        // Chiedi se vuole visualizzare il documento
        if (result.documento_id && window.confirm('Vuoi visualizzare il documento Libro Unico creato?')) {
          navigate(`/documenti/${result.documento_id}`);
        }
      } else {
        toast.error(`Errore: ${result.errori.join(', ')}`);
      }
    } catch (error: any) {
      console.error('Errore creazione Libro Unico:', error);
      toast.error(
        error.response?.data?.errori?.join('\n') || 
        error.response?.data?.detail || 
        'Errore durante la creazione del Libro Unico'
      );
    } finally {
      setProcessingBatch(false);
    }
  };

  const handleDeleteSession = async () => {
    if (!sessionUuid || !window.confirm('Sei sicuro di voler eliminare questa sessione di importazione?')) {
      return;
    }

    try {
      await importApi.deleteSession(sessionUuid);
      toast.success('Sessione eliminata');
      navigate('/import');
    } catch (error: any) {
      console.error('Errore eliminazione sessione:', error);
      toast.error(error.response?.data?.detail || 'Errore eliminazione sessione');
    }
  };

  const handlePreviewDocument = (docUuid: string) => {
    navigate(`/import/${sessionUuid}/documents/${docUuid}`);
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Box textAlign="center">
            <LinearProgress sx={{ width: 300, mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              Caricamento sessione...
            </Typography>
          </Box>
        </Box>
      </Container>
    );
  }

  if (!session) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Alert severity="error">Sessione non trovata</Alert>
      </Container>
    );
  }

  const documentiFilterati = session.documents.filter((doc) => {
    if (filtroStato === 'all') return true;
    return doc.stato === filtroStato;
  });

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/import')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Box flex={1}>
          <Typography variant="h4">Documenti Estratti - {session.tipo_importazione_display}</Typography>
          <Typography variant="body2" color="text.secondary">
            File: {session.file_originale?.split('/').pop() || 'N/A'}
          </Typography>
        </Box>
        <Box>
          <Tooltip title="Ricarica">
            <IconButton onClick={loadSession} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Elimina sessione">
            <IconButton onClick={handleDeleteSession} color="error">
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Statistiche */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Stato Importazione
          </Typography>
          
          {/* Progress Bar */}
          <Box mb={2}>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2" color="text.secondary">
                Progresso
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {session.progress_percentage}%
              </Typography>
            </Box>
            <LinearProgress variant="determinate" value={session.progress_percentage} />
          </Box>

          {/* Statistiche */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(4, 1fr)' },
              gap: 2,
            }}
          >
            <Box textAlign="center">
              <Typography variant="h4" color="primary">
                {session.num_documenti_totali}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Totali
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="success.main">
                {session.num_documenti_importati}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Importati
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="text.secondary">
                {session.num_documenti_saltati}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Saltati
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h4" color="error.main">
                {session.num_documenti_errore}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Errori
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Filtri e Azioni Batch */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3} gap={2}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel id="filtro-stato-label">Stato</InputLabel>
          <Select
            labelId="filtro-stato-label"
            value={filtroStato}
            onChange={(e) => setFiltroStato(e.target.value as StatoDocumento | 'all')}
            label="Stato"
          >
            <MenuItem value="all">Tutti ({session.documents.length})</MenuItem>
            <MenuItem value="pending">
              In attesa ({session.documents.filter((d) => d.stato === 'pending').length})
            </MenuItem>
            <MenuItem value="imported">
              Importati ({session.num_documenti_importati})
            </MenuItem>
            <MenuItem value="skipped">
              Saltati ({session.num_documenti_saltati})
            </MenuItem>
            <MenuItem value="error">
              Errori ({session.num_documenti_errore})
            </MenuItem>
          </Select>
        </FormControl>

        {/* Pulsanti Batch */}
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={checkingDuplicates ? <LinearProgress /> : <RefreshIcon />}
            onClick={checkAllDuplicates}
            disabled={checkingDuplicates || processingBatch}
            size="small"
          >
            {checkingDuplicates ? 'Verifica...' : 'Verifica Duplicati'}
          </Button>
          
          <Button
            variant="contained"
            color="success"
            startIcon={<PlayArrowIcon />}
            onClick={handleImportaTuttiNuovi}
            disabled={processingBatch || checkingDuplicates}
            size="small"
          >
            Importa Nuovi
          </Button>
          
          <Button
            variant="outlined"
            color="warning"
            startIcon={<SkipNextIcon />}
            onClick={handleSaltaTuttiDuplicati}
            disabled={processingBatch || checkingDuplicates}
            size="small"
          >
            Salta Duplicati
          </Button>
          
          {/* Pulsante Salva ZIP come Libro Unico */}
          {session.tipo_importazione === 'cedolini' && session.file_originale_nome?.toLowerCase().endsWith('.zip') && (
            <Button
              variant="contained"
              color="secondary"
              startIcon={<SaveIcon />}
              onClick={handleSalvaZipLibroUnico}
              disabled={processingBatch || checkingDuplicates}
              size="small"
            >
              Salva ZIP come Libro Unico
            </Button>
          )}
        </Box>
      </Box>

      {/* Lista Documenti */}
      {documentiFilterati.length === 0 ? (
        <Alert severity="info">Nessun documento trovato con i filtri selezionati</Alert>
      ) : (
        <>
          {/* Alert Duplicati Rilevati */}
          {Object.values(duplicatesCheck).filter(check => check.is_duplicate).length > 0 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Attenzione:</strong> Rilevati{' '}
                <strong>{Object.values(duplicatesCheck).filter(check => check.is_duplicate).length}</strong>{' '}
                documenti duplicati. Usa i pulsanti "Importa Nuovi" o "Salta Duplicati" per gestirli in batch.
              </Typography>
            </Alert>
          )}
          
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              md: 'repeat(2, 1fr)',
              lg: 'repeat(3, 1fr)',
            },
            gap: 2,
          }}
        >
          {documentiFilterati.map((doc) => {
            const hasAnagrafiche = doc.anagrafiche_reperite && doc.anagrafiche_reperite.length > 0;
            const anagraficheOk = hasAnagrafiche
              ? doc.anagrafiche_reperite.every((a) => a.match_type === 'exact')
              : false;
            const anagraficheWarning = hasAnagrafiche
              ? doc.anagrafiche_reperite.some((a) => a.match_type === 'multiple' || a.match_type === 'not_found')
              : false;

            return (
              <Card
                key={doc.uuid}
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  border: doc.stato === 'error' ? '2px solid' : undefined,
                  borderColor: doc.stato === 'error' ? 'error.main' : undefined,
                }}
              >
                  <CardContent sx={{ flex: 1 }}>
                    {/* Stato Badge */}
                    <Box position="absolute" top={8} right={8} display="flex" flexDirection="column" gap={0.5} alignItems="flex-end">
                      <Chip
                        icon={STATO_ICONS[doc.stato]}
                        label={STATO_LABELS[doc.stato]}
                        color={STATO_COLORS[doc.stato]}
                        size="small"
                      />
                      
                      {/* Indicatore Duplicato */}
                      {doc.stato === 'pending' && duplicatesCheck[doc.uuid] && (
                        <>
                          {duplicatesCheck[doc.uuid].is_duplicate ? (
                            <Chip
                              icon={<WarningIcon />}
                              label="Duplicato"
                              color="warning"
                              size="small"
                              variant="outlined"
                            />
                          ) : (
                            <Chip
                              label="Nuovo"
                              color="primary"
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </>
                      )}
                      
                      {doc.stato === 'imported' && (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="Importato"
                          color="success"
                          size="small"
                          variant="filled"
                        />
                      )}
                    </Box>

                    {/* Filename */}
                    <Typography variant="h6" gutterBottom noWrap title={doc.filename}>
                      {doc.filename}
                    </Typography>

                    <Divider sx={{ my: 1 }} />

                    {/* Anagrafiche Indicators */}
                    {hasAnagrafiche && (
                      <Box mb={2}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Anagrafiche:
                        </Typography>
                        {doc.anagrafiche_reperite.map((ana, idx) => (
                          <Box key={idx} display="flex" alignItems="center" gap={1} mb={0.5}>
                            {ana.match_type === 'exact' ? (
                              <CheckCircleIcon fontSize="small" color="success" />
                            ) : ana.match_type === 'not_found' ? (
                              <ErrorIcon fontSize="small" color="error" />
                            ) : (
                              <ErrorIcon fontSize="small" color="warning" />
                            )}
                            <Typography variant="body2" fontSize="0.875rem">
                              {ana.ruolo}: {ana.nome || ana.codice_fiscale}
                              {ana.match_type === 'not_found' && ' (non trovata)'}
                              {ana.match_type === 'multiple' && ' (multipla)'}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}

                    {/* Errori */}
                    {doc.stato === 'error' && doc.error_message && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        <Typography variant="body2" fontSize="0.75rem">
                          {doc.error_message}
                        </Typography>
                      </Alert>
                    )}

                    {/* Info Documento Creato */}
                    {doc.stato === 'imported' && doc.documento_creato_detail && (
                      <Box mt={1}>
                        <Chip
                          label={`${doc.documento_creato_detail.codice} - ${doc.documento_creato_detail.titolo}`}
                          size="small"
                          color="success"
                          onClick={() => navigate(`/documenti/${doc.documento_creato_detail!.id}`)}
                          clickable
                        />
                      </Box>
                    )}
                  </CardContent>

                  <CardActions>
                    {doc.stato === 'pending' && (
                      <Button
                        size="small"
                        startIcon={<PreviewIcon />}
                        onClick={() => handlePreviewDocument(doc.uuid)}
                        fullWidth
                        variant="contained"
                        color={anagraficheWarning ? 'warning' : anagraficheOk ? 'success' : 'primary'}
                      >
                        {anagraficheWarning ? 'Verifica e Importa' : 'Anteprima e Importa'}
                      </Button>
                    )}
                    {doc.stato === 'imported' && doc.documento_creato_detail && (
                      <Button
                        size="small"
                        onClick={() => navigate(`/documenti/${doc.documento_creato_detail!.id}`)}
                        fullWidth
                        variant="outlined"
                      >
                        Vai al Documento
                      </Button>
                    )}
                    {doc.stato === 'skipped' && (
                      <Button
                        size="small"
                        startIcon={<PreviewIcon />}
                        onClick={() => handlePreviewDocument(doc.uuid)}
                        fullWidth
                        variant="outlined"
                      >
                        Visualizza
                      </Button>
                    )}
                    {doc.stato === 'error' && (
                      <Button
                        size="small"
                        startIcon={<PreviewIcon />}
                        onClick={() => handlePreviewDocument(doc.uuid)}
                        fullWidth
                        variant="outlined"
                        color="error"
                      >
                        Dettagli Errore
                      </Button>
                    )}
                  </CardActions>
                </Card>
            );
          })}
        </Box>
        </>
      )}
    </Container>
  );
};
