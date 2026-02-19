import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  TextField,
  Alert,
  LinearProgress,
  Chip,
  IconButton,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Autocomplete,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormControl,
  FormLabel,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  PictureAsPdf as PdfIcon,
  Close as CloseIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import {
  importApi,
  type ImportSessionDocument,
  type AnagraficaReperita,
} from '@/api/import';
import type { AnagraficaDetail } from '@/types/anagrafiche';
import type { Cliente } from '@/types/anagrafiche';
import type { FascicoloListItem } from '@/types/fascicolo';
import { anagraficheApi } from '@/api/anagrafiche';
import { fascicoliApi } from '@/api/fascicoli';

export const ImportDocumentPreviewPage: React.FC = () => {
  const { sessionUuid, docUuid } = useParams<{ sessionUuid: string; docUuid: string }>();
  const navigate = useNavigate();

  const [document, setDocument] = useState<ImportSessionDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [pdfDialogOpen, setPdfDialogOpen] = useState(false);
  
  // Gestione duplicati
  const [isDuplicate, setIsDuplicate] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<any>(null);
  const [duplicatePolicy, setDuplicatePolicy] = useState<'skip' | 'replace' | 'add'>('skip');
  
  // Dialog post-creazione
  const [successDialogOpen, setSuccessDialogOpen] = useState(false);
  const [createdDocumento, setCreatedDocumento] = useState<any>(null);

  // Stati per modifiche
  const [valoriEditabili, setValoriEditabili] = useState<Record<string, any>>({});

  // Stati per selezioni
  const [clienteSelezionato, setClienteSelezionato] = useState<AnagraficaDetail | null>(null);
  const [fascicoloSelezionato, setFascicoloSelezionato] = useState<FascicoloListItem | null>(null);

  // Autocomplete options
  const [clientiOptions, setClientiOptions] = useState<AnagraficaDetail[]>([]);
  const [fascicoliOptions, setFascicoliOptions] = useState<FascicoloListItem[]>([]);
  const [loadingClienti, setLoadingClienti] = useState(false);
  const [loadingFascicoli, setLoadingFascicoli] = useState(false);

  const loadDocument = async () => {
    if (!sessionUuid || !docUuid) return;

    try {
      setLoading(true);
      const data = await importApi.getDocument(sessionUuid, docUuid);
      setDocument(data);
      setValoriEditabili(data.valori_editabili || {});

      // Pre-seleziona cliente se anagrafica trovata esattamente
      if (data.anagrafiche_reperite) {
        const anaDatore = data.anagrafiche_reperite.find(
          (a) => a.ruolo === 'datore' && a.match_type === 'exact' && a.cliente_id
        );
        if (anaDatore?.cliente_id) {
          loadClientiByIds([anaDatore.cliente_id]);
        }
      }
      
      // Controlla se il documento è duplicato
      try {
        const duplicateCheck = await importApi.checkDuplicates(sessionUuid);
        if (duplicateCheck.duplicates[docUuid]) {
          const checkResult = duplicateCheck.duplicates[docUuid];
          setIsDuplicate(checkResult.is_duplicate);
          setDuplicateInfo(checkResult.duplicate_info);
        }
      } catch (dupError) {
        console.warn('Errore verifica duplicato:', dupError);
        // Non blocca il caricamento
      }
    } catch (error: any) {
      console.error('Errore caricamento documento:', error);
      toast.error(error.response?.data?.detail || 'Errore caricamento documento');
      navigate(`/import/${sessionUuid}/documents`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocument();
  }, [sessionUuid, docUuid]);

  const loadClientiByIds = async (ids: number[]) => {
    try {
      setLoadingClienti(true);
      // Prova a caricare i clienti per ID
      const promises = ids.map(async (id) => {
        try {
          return await anagraficheApi.getCliente(id);
        } catch (error: any) {
          console.warn(`Cliente ${id} non trovato:`, error);
          return null;
        }
      });
      const risultati = await Promise.all(promises);
      const clienti = risultati.filter((c: Cliente | null): c is Cliente => c !== null);
      
      // TODO: getCliente restituisce solo Cliente, non l'anagrafica completa
      // Per ora impostiamo opzioni vuote e lasciamo che l'utente cerchi manualmente
      if (clienti.length === 0) {
        console.warn('Nessun cliente trovato per gli ID:', ids);
        return;
      }
      
      // Convertiamo i clienti in AnagraficaDetail (mapping temporaneo)
      // Idealmente dovremmo chiamare /api/v1/anagrafiche/anagrafiche/{cliente.anagrafica}/
      setClientiOptions(clienti as any[]);
    } catch (error) {
      console.error('Errore caricamento clienti:', error);
    } finally {
      setLoadingClienti(false);
    }
  };

  const searchClienti = async (query: string) => {
    if (!query || query.length < 2) {
      setClientiOptions([]);
      return;
    }

    try {
      setLoadingClienti(true);
      const response = await anagraficheApi.listClienti({ search: query });
      // Convertiamo Cliente[] in AnagraficaDetail[]
      // TODO: correggere API per restituire AnagraficaDetail
      setClientiOptions(response.results as any);
    } catch (error) {
      console.error('Errore ricerca clienti:', error);
    } finally {
      setLoadingClienti(false);
    }
  };

  const searchFascicoli = async (query: string) => {
    if (!query || query.length < 2) {
      setFascicoliOptions([]);
      return;
    }

    try {
      setLoadingFascicoli(true);
      const params: any = { search: query };
      if (clienteSelezionato) {
        params.cliente = clienteSelezionato.id;
      }
      const response = await fascicoliApi.list(params);
      setFascicoliOptions(response.results);
    } catch (error) {
      console.error('Errore ricerca fascicoli:', error);
    } finally {
      setLoadingFascicoli(false);
    }
  };

  const handleValoreChange = (campo: string, valore: any) => {
    setValoriEditabili((prev) => ({ ...prev, [campo]: valore }));
  };

  const handleConferma = async () => {
    if (!sessionUuid || !docUuid) return;

    try {
      setSubmitting(true);

      const requestData: any = {
        valori_editabili: valoriEditabili,
      };

      if (clienteSelezionato) {
        requestData.cliente_id = clienteSelezionato.id;
      }

      if (fascicoloSelezionato) {
        requestData.fascicolo_id = fascicoloSelezionato.id;
      }
      
      // Aggiungi policy di duplicazione se il documento è duplicato
      if (isDuplicate && duplicatePolicy) {
        requestData.duplicate_policy = duplicatePolicy;
      }

      const response = await importApi.createDocument(sessionUuid, docUuid, requestData);

      console.log('✅ Documento creato con successo:', response);
      
      // Salva documento creato e apri dialog successo
      setCreatedDocumento(response.documento);
      setSuccessDialogOpen(true);
      
    } catch (error: any) {
      console.error('🔴 CATCH ERRORE:', error);
      console.log('📊 Status:', error.response?.status);
      console.log('📦 Data:', error.response?.data);
      
      // Gestione errore duplicato (HTTP 409)
      if (error.response?.status === 409 && error.response?.data?.duplicate_info) {
        console.log('✅ ENTRATO IN GESTIONE DUPLICATO');
        const dupInfo = error.response.data.duplicate_info;
        const documentoId = dupInfo.id;
        
        // Mostra toast con azione per visualizzare documento
        toast.warning(
          <div>
            <strong>⚠️ Cedolino già presente</strong>
            <div style={{ marginTop: '8px', fontSize: '0.9em' }}>
              <div>📄 Documento: <strong>{dupInfo.codice}</strong></div>
              {dupInfo.numero_cedolino && (
                <div>🔢 Numero: {dupInfo.numero_cedolino}</div>
              )}
              {dupInfo.data_ora_cedolino && (
                <div>📅 Data/Ora: {dupInfo.data_ora_cedolino}</div>
              )}
              {dupInfo.confidence && (
                <div style={{ marginTop: '4px', fontSize: '0.85em', opacity: 0.8 }}>
                  Match: {(dupInfo.confidence * 100).toFixed(0)}% su {dupInfo.matched_fields?.join(', ')}
                </div>
              )}
            </div>
            {documentoId && (
              <button
                onClick={() => {
                  navigate(`/documenti/${documentoId}`);
                }}
                style={{
                  marginTop: '12px',
                  padding: '6px 12px',
                  backgroundColor: '#fff',
                  border: '1px solid #ff9800',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.9em',
                  fontWeight: 'bold',
                  color: '#ff9800'
                }}
              >
                📂 Visualizza documento esistente
              </button>
            )}
          </div>,
          { 
            autoClose: 10000,
            closeButton: true,
            style: { minWidth: '400px' }
          }
        );
      } else {
        // Altri errori
        const errorMsg = error.response?.data?.error || 
                        error.response?.data?.detail || 
                        'Errore importazione documento';
        toast.error(errorMsg);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleSalta = async () => {
    if (!sessionUuid || !docUuid || !window.confirm('Sei sicuro di voler saltare questo documento?')) {
      return;
    }

    try {
      setSubmitting(true);
      await importApi.skipDocument(sessionUuid, docUuid);
      toast.info('Documento saltato');
      navigate(`/import/${sessionUuid}/documents`);
    } catch (error: any) {
      console.error('Errore salto documento:', error);
      toast.error(error.response?.data?.detail || 'Errore salto documento');
    } finally {
      setSubmitting(false);
    }
  };

  const getAnagraficaIcon = (anagrafica: AnagraficaReperita) => {
    // Determina se persona fisica o giuridica dal CF
    const isPF = anagrafica.codice_fiscale?.length === 16;
    return isPF ? <PersonIcon /> : <BusinessIcon />;
  };

  const getMatchTypeColor = (
    matchType: 'exact' | 'multiple' | 'not_found'
  ): 'success' | 'warning' | 'error' => {
    switch (matchType) {
      case 'exact':
        return 'success';
      case 'multiple':
        return 'warning';
      case 'not_found':
        return 'error';
    }
  };

  const getMatchTypeLabel = (matchType: 'exact' | 'multiple' | 'not_found'): string => {
    switch (matchType) {
      case 'exact':
        return 'Trovata';
      case 'multiple':
        return 'Multipla';
      case 'not_found':
        return 'Non trovata';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Box textAlign="center">
            <LinearProgress sx={{ width: 300, mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              Caricamento documento...
            </Typography>
          </Box>
        </Box>
      </Container>
    );
  }

  if (!document) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Documento non trovato</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate(`/import/${sessionUuid}/documents`)} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Box flex={1}>
          <Typography variant="h4">Anteprima Documento</Typography>
          <Typography variant="body2" color="text.secondary">
            {document.filename}
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          {/* Pulsante Preview PDF */}
          {document.file_url && (
            <Button
              variant="outlined"
              startIcon={<PdfIcon />}
              onClick={() => setPdfDialogOpen(true)}
              color="primary"
            >
              Apri PDF
            </Button>
          )}
          <Chip
            label={document.stato === 'pending' ? 'In attesa' : document.stato}
            color={document.stato === 'error' ? 'error' : 'default'}
          />
        </Box>
      </Box>

      {/* Errore */}
      {document.stato === 'error' && document.error_message && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight="bold">
            Errore durante il parsing:
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {document.error_message}
          </Typography>
          {document.error_traceback && (
            <Box
              component="pre"
              sx={{
                mt: 2,
                p: 1,
                bgcolor: 'grey.900',
                color: 'grey.100',
                borderRadius: 1,
                fontSize: '0.75rem',
                overflow: 'auto',
                maxHeight: 200,
              }}
            >
              {document.error_traceback}
            </Box>
          )}
        </Alert>
      )}
      
      {/* Alert Duplicato con scelta policy */}
      {isDuplicate && duplicateInfo && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon /> Documento Duplicato Rilevato
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2">
              Questo cedolino sembra già esistente nel database:
            </Typography>
            <Box sx={{ mt: 1, pl: 2 }}>
              <Typography variant="body2">
                📄 <strong>Codice:</strong> {duplicateInfo.codice}
              </Typography>
              {duplicateInfo.numero_cedolino && (
                <Typography variant="body2">
                  🔢 <strong>Numero:</strong> {duplicateInfo.numero_cedolino}
                </Typography>
              )}
              {duplicateInfo.data_ora_cedolino && (
                <Typography variant="body2">
                  📅 <strong>Data/Ora:</strong> {duplicateInfo.data_ora_cedolino}
                </Typography>
              )}
              {duplicateInfo.confidence && (
                <Typography variant="body2" sx={{ mt: 0.5, fontSize: '0.85rem', opacity: 0.8 }}>
                  🎯 Match: {(duplicateInfo.confidence * 100).toFixed(0)}% su {duplicateInfo.matched_fields?.join(', ')}
                </Typography>
              )}
            </Box>
          </Box>
          
          <FormControl component="fieldset">
            <FormLabel component="legend">
              <Typography variant="body2" fontWeight="bold">
                Come vuoi procedere?
              </Typography>
            </FormLabel>
            <RadioGroup
              value={duplicatePolicy}
              onChange={(e) => setDuplicatePolicy(e.target.value as 'skip' | 'replace' | 'add')}
              sx={{ mt: 1 }}
            >
              <FormControlLabel
                value="skip"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      Salta importazione
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Non importare, mantieni solo il documento esistente
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                value="replace"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      Sostituisci esistente
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Elimina il documento esistente e importa questo nuovo
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                value="add"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      Importa comunque
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Crea un nuovo documento anche se duplicato
                    </Typography>
                  </Box>
                }
              />
            </RadioGroup>
          </FormControl>
          
          <Box sx={{ mt: 2 }}>
            <Button
              size="small"
              variant="outlined"
              onClick={() => window.open(`/documenti/${duplicateInfo.id}`, '_blank')}
            >
              📂 Visualizza documento esistente
            </Button>
          </Box>
        </Alert>
      )}

      {/* Sezione 1: Anagrafiche Reperite */}
      {document.anagrafiche_reperite && document.anagrafiche_reperite.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Anagrafiche Reperite
            </Typography>
            <List>
              {document.anagrafiche_reperite.map((ana, idx) => (
                <React.Fragment key={idx}>
                  <ListItem>
                    <ListItemIcon>{getAnagraficaIcon(ana)}</ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1" fontWeight="bold">
                            {ana.nome || 'N/A'}
                          </Typography>
                          <Chip
                            size="small"
                            label={getMatchTypeLabel(ana.match_type)}
                            color={getMatchTypeColor(ana.match_type)}
                            icon={
                              ana.match_type === 'exact' ? (
                                <CheckCircleIcon />
                              ) : ana.match_type === 'multiple' ? (
                                <WarningIcon />
                              ) : (
                                <ErrorIcon />
                              )
                            }
                          />
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography variant="body2" component="span">
                            Codice Fiscale: {ana.codice_fiscale}
                          </Typography>
                          {ana.ruolo && (
                            <Typography variant="body2" component="span" sx={{ ml: 2 }}>
                              Ruolo: {ana.ruolo}
                            </Typography>
                          )}
                          {ana.match_type === 'not_found' && (
                            <Typography variant="body2" color="error" sx={{ mt: 0.5 }}>
                              ⚠️ Anagrafica non trovata nel sistema. Sarà necessario crearla prima
                              dell'importazione.
                            </Typography>
                          )}
                          {ana.match_type === 'multiple' && (
                            <Typography variant="body2" color="warning.main" sx={{ mt: 0.5 }}>
                              ⚠️ Trovate più anagrafiche con questo codice fiscale. Selezionare
                              manualmente.
                            </Typography>
                          )}
                        </>
                      }
                    />
                  </ListItem>
                  {idx < document.anagrafiche_reperite!.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Sezione 2: Valori Editabili */}
      {document.valori_editabili && Object.keys(document.valori_editabili).length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Valori Estratti (Modificabili)
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
                gap: 2,
                mt: 2,
              }}
            >
              {Object.entries(valoriEditabili).map(([campo, valore]) => (
                <TextField
                  key={campo}
                  label={campo
                    .split('_')
                    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
                    .join(' ')}
                  value={valore ?? ''}
                  onChange={(e) => handleValoreChange(campo, e.target.value)}
                  fullWidth
                  variant="outlined"
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Sezione 3: Mappatura Database (Preview) */}
      {document.mappatura_db && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Anteprima Dati da Salvare
            </Typography>

            {/* Tipo Documento */}
            {document.mappatura_db.tipo && (
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Tipo Documento:
                </Typography>
                <Chip label={document.mappatura_db.tipo} color="primary" />
              </Box>
            )}

            {/* Attributi */}
            {document.mappatura_db.attributi && document.mappatura_db.attributi.length > 0 && (
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="body1" fontWeight="bold">
                    Attributi ({document.mappatura_db.attributi.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {document.mappatura_db.attributi.map((attr: any, idx: number) => (
                      <ListItem key={idx}>
                        <ListItemText
                          primary={attr.nome || attr.codice}
                          secondary={`Valore: ${attr.valore}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Note Preview */}
            {document.mappatura_db.note_preview && (
              <Box mt={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Note che verranno salvate:
                </Typography>
                <TextField
                  multiline
                  rows={8}
                  value={document.mappatura_db.note_preview}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  variant="outlined"
                  sx={{
                    '& .MuiInputBase-input': {
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                    },
                  }}
                />
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Sezione 4: Selezione Cliente e Fascicolo */}
      {document.stato === 'pending' && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Assegnazione Documento
            </Typography>

            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
                gap: 2,
                mt: 2,
              }}
            >
              {/* Cliente */}
              <Autocomplete
                options={clientiOptions}
                value={clienteSelezionato}
                onChange={(_, newValue) => {
                  setClienteSelezionato(newValue);
                  setFascicoloSelezionato(null); // Reset fascicolo
                }}
                onInputChange={(_, newInputValue) => {
                  if (newInputValue) {
                    searchClienti(newInputValue);
                  }
                }}
                getOptionLabel={(option) =>
                  `${option.display_name} - ${option.codice_fiscale}`
                }
                loading={loadingClienti}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Cliente (Opzionale)"
                    helperText="Se non selezionato, verrà usata l'anagrafica datore se presente"
                  />
                )}
              />

              {/* Fascicolo */}
              <Autocomplete
                options={fascicoliOptions}
                value={fascicoloSelezionato}
                onChange={(_, newValue) => setFascicoloSelezionato(newValue)}
                onInputChange={(_, newInputValue) => {
                  if (newInputValue) {
                    searchFascicoli(newInputValue);
                  }
                }}
                getOptionLabel={(option) => `${option.codice} - ${option.titolo}`}
                loading={loadingFascicoli}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Fascicolo (Opzionale)"
                    helperText="L'assegnazione del fascicolo è opzionale"
                  />
                )}
                disabled={!clienteSelezionato}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Azioni */}
      <Box display="flex" justifyContent="flex-end" gap={2}>
        <Button
          variant="outlined"
          startIcon={<CancelIcon />}
          onClick={handleSalta}
          disabled={submitting || document.stato !== 'pending'}
        >
          Salta Documento
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleConferma}
          disabled={submitting || document.stato !== 'pending'}
        >
          {submitting ? 'Importazione...' : 'Conferma e Importa'}
        </Button>
      </Box>

      {/* Alert se documento già importato/saltato */}
      {document.stato !== 'pending' && (
        <Alert severity="info" sx={{ mt: 3 }}>
          {document.stato === 'imported' && document.documento_creato_detail && (
            <>
              Documento già importato:{' '}
              <Button
                size="small"
                onClick={() => navigate(`/documenti/${document.documento_creato_detail!.id}`)}
              >
                {document.documento_creato_detail.codice} -{' '}
                {document.documento_creato_detail.titolo}
              </Button>
            </>
          )}
          {document.stato === 'skipped' && 'Documento saltato. Non sarà importato.'}
        </Alert>
      )}

      {/* Dialog Preview PDF */}
      <Dialog
        open={pdfDialogOpen}
        onClose={() => setPdfDialogOpen(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box display="flex" alignItems="center" gap={1}>
            <PdfIcon />
            <Typography variant="h6">Anteprima PDF</Typography>
          </Box>
          <IconButton
            edge="end"
            color="inherit"
            onClick={() => setPdfDialogOpen(false)}
            aria-label="chiudi"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 0, height: '100%' }}>
          {document?.file_url && (
            <iframe
              src={document.file_url}
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
              }}
              title="PDF Preview"
            />
          )}
        </DialogContent>
      </Dialog>
      
      {/* Dialog Successo Importazione */}
      <Dialog
        open={successDialogOpen}
        onClose={() => setSuccessDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircleIcon color="success" />
          <Typography variant="h6">Documento Importato con Successo!</Typography>
        </DialogTitle>
        <DialogContent>
          {createdDocumento && (
            <Box>
              <Typography variant="body1" gutterBottom>
                Il documento è stato importato correttamente:
              </Typography>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                <Typography variant="body2">
                  <strong>Codice:</strong> {createdDocumento.codice}
                </Typography>
                <Typography variant="body2">
                  <strong>Titolo:</strong> {createdDocumento.titolo || 'N/D'}
                </Typography>
                {createdDocumento.cliente_nome && (
                  <Typography variant="body2">
                    <strong>Cliente:</strong> {createdDocumento.cliente_nome}
                  </Typography>
                )}
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Cosa vuoi fare ora?
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => {
              setSuccessDialogOpen(false);
              navigate(`/import/${sessionUuid}/documents`);
            }}
            fullWidth
          >
            Continua Importazione
          </Button>
          <Button
            variant="contained"
            startIcon={<DescriptionIcon />}
            onClick={() => {
              if (createdDocumento) {
                navigate(`/documenti/${createdDocumento.id}`);
              }
            }}
            fullWidth
          >
            Vai al Documento
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
