/**
 * Form per creazione/modifica operazione archivio
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Typography,
  TextField,
  MenuItem,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  Divider,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { toast } from 'react-toastify';

import {
  getOperazioneArchivio,
  createOperazioneArchivio,
  updateOperazioneArchivio,
  getUtenti,
  searchAnagrafiche,
} from '../../api/archivioFisico';
import type {
  OperazioneArchivioFormData,
  RigaOperazioneFormData,
  TipoOperazioneArchivio,
  User,
  Anagrafica,
  DocumentoTracciabile,
  FascicoloTracciabile,
} from '../../types/archivioFisico';
import DocumentoFascicoloSelector from '../../components/ArchivioFisico/DocumentoFascicoloSelector';
import UnitaFisicaSelector from '../../components/ArchivioFisico/UnitaFisicaSelector';

// ID dell'Archivio di scarico (hardcoded come richiesto)
const ARCHIVIO_SCARICO_ID = 28;

const OperazioneArchivioForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id) && id !== 'new';

  console.log('OperazioneArchivioForm - id:', id, 'isEdit:', isEdit);

  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<OperazioneArchivioFormData>({
    tipo_operazione: 'entrata',
    referente_interno: 0,
    referente_esterno: null,
    note: '',
    verbale_scan: null,
    righe: [],
  });

  const [utenti, setUtenti] = useState<User[]>([]);
  const [anagrafiche, setAnagrafiche] = useState<Anagrafica[]>([]);
  const [searchAnagrafica, setSearchAnagrafica] = useState('');

  useEffect(() => {
    if (isEdit && id) {
      fetchOperazione();
    }
    fetchReferenceData();
  }, [id, isEdit]);

  useEffect(() => {
    if (searchAnagrafica) {
      fetchAnagrafiche();
    }
  }, [searchAnagrafica]);

  const fetchOperazione = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const data = await getOperazioneArchivio(parseInt(id));
      setFormData({
        tipo_operazione: data.tipo_operazione,
        referente_interno: data.referente_interno,
        referente_esterno: data.referente_esterno || null,
        note: data.note || '',
        verbale_scan: null,
        righe: data.righe?.map(r => ({
          id: r.id,
          fascicolo: r.fascicolo || null,
          documento: r.documento || null,
          movimento_protocollo: r.movimento_protocollo || null,
          unita_fisica_sorgente: r.unita_fisica_sorgente || null,
          unita_fisica_destinazione: r.unita_fisica_destinazione || null,
          stato_precedente: r.stato_precedente || '',
          stato_successivo: r.stato_successivo || '',
          note: r.note || '',
        })) || [],
      });
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento dell\'operazione');
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const fetchReferenceData = async () => {
    try {
      const utentiData = await getUtenti();
      console.log('Utenti caricati:', utentiData);
      
      // Gestisce sia array diretto che risposta paginata
      const utenti = Array.isArray(utentiData) ? utentiData : ((utentiData as any)?.results || []);
      
      setUtenti(utenti);
    } catch (err) {
      console.error('Errore caricamento dati di riferimento:', err);
      toast.error('Errore nel caricamento dei dati');
    }
  };

  const fetchAnagrafiche = async () => {
    try {
      const data = await searchAnagrafiche(searchAnagrafica);
      setAnagrafiche(data);
    } catch (err) {
      console.error('Errore ricerca anagrafiche:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.referente_interno) {
      toast.error('Seleziona un referente interno');
      return;
    }

    if (formData.righe.length === 0) {
      toast.error('Aggiungi almeno una riga');
      return;
    }

    console.log('Form data da inviare:', JSON.stringify(formData, null, 2));
    console.log('isEdit:', isEdit, 'id:', id);

    try {
      setSaving(true);
      if (isEdit && id) {
        console.log('Eseguendo UPDATE operazione:', id);
        await updateOperazioneArchivio(parseInt(id), formData);
        toast.success('Operazione aggiornata con successo');
      } else {
        console.log('Eseguendo CREATE operazione');
        const created = await createOperazioneArchivio(formData);
        console.log('Operazione creata:', created);
        toast.success('Operazione creata con successo');
        
        // Verifica che created.id esista
        if (!created || !created.id) {
          console.error('Risposta API non valida:', created);
          toast.error('Operazione creata ma impossibile recuperare l\'ID');
          navigate('/archivio-fisico/operazioni');
          return;
        }
        
        navigate(`/archivio-fisico/operazioni/${created.id}`);
        return;
      }
      navigate(`/archivio-fisico/operazioni/${id}`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Errore nel salvataggio';
      toast.error(errorMsg);
      console.error('Errore salvataggio:', err);
    } finally {
      setSaving(false);
    }
  };

  const addRiga = () => {
    setFormData(prev => ({
      ...prev,
      righe: [
        ...prev.righe,
        {
          fascicolo: null,
          documento: null,
          movimento_protocollo: null,
          unita_fisica_sorgente: null,
          unita_fisica_destinazione: null,
          stato_precedente: '',
          stato_successivo: '',
          note: '',
        },
      ],
    }));
  };

  const removeRiga = (index: number) => {
    setFormData(prev => ({
      ...prev,
      righe: prev.righe.filter((_, i) => i !== index),
    }));
  };

  const updateRiga = (index: number, field: keyof RigaOperazioneFormData, value: any, oggetto?: DocumentoTracciabile | FascicoloTracciabile) => {
    setFormData(prev => {
      const newRighe = prev.righe.map((r, i) => {
        if (i !== index) return r;

        const updated = { ...r, [field]: value };

        // Quando viene selezionato un documento o fascicolo, aggiorna le unità fisiche
        if ((field === 'documento' || field === 'fascicolo') && oggetto) {
          const ubicazioneId = oggetto.ubicazione;

          if (prev.tipo_operazione === 'entrata') {
            // Entrata: "Da unità" non compilato, "A unità" = ubicazione documento/fascicolo (modificabile)
            updated.unita_fisica_sorgente = null;
            updated.unita_fisica_destinazione = ubicazioneId || null;
          } else if (prev.tipo_operazione === 'uscita') {
            // Uscita: "Da unità" = ubicazione documento/fascicolo (non modificabile), "A unità" = Archivio di scarico
            updated.unita_fisica_sorgente = ubicazioneId || null;
            updated.unita_fisica_destinazione = ARCHIVIO_SCARICO_ID;
          } else if (prev.tipo_operazione === 'interna') {
            // Interna: entrambe = ubicazione documento/fascicolo (modificabili)
            updated.unita_fisica_sorgente = ubicazioneId || null;
            updated.unita_fisica_destinazione = ubicazioneId || null;
          }
        }

        return updated;
      });

      return { ...prev, righe: newRighe };
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton component={Link} to="/archivio-fisico/operazioni">
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">
          {isEdit ? 'Modifica Operazione' : 'Nuova Operazione'}
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <form onSubmit={handleSubmit}>
        {/* Dati Principali */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Informazioni Generali
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
                <FormControl fullWidth required>
                  <InputLabel>Tipo Operazione</InputLabel>
                  <Select
                    value={formData.tipo_operazione}
                    onChange={(e) => setFormData({ ...formData, tipo_operazione: e.target.value as TipoOperazioneArchivio })}
                    label="Tipo Operazione"
                  >
                    <MenuItem value="entrata">Entrata</MenuItem>
                    <MenuItem value="uscita">Uscita</MenuItem>
                    <MenuItem value="interna">Movimento Interno</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth required>
                  <InputLabel>Referente Interno</InputLabel>
                  <Select
                    value={formData.referente_interno || ''}
                    onChange={(e) => setFormData({ ...formData, referente_interno: Number(e.target.value) })}
                    label="Referente Interno"
                  >
                    {utenti.map((utente) => (
                      <MenuItem key={utente.id} value={utente.id}>
                        {utente.display_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <Box sx={{ width: '100%' }}>
                  <Autocomplete
                    options={anagrafiche}
                    getOptionLabel={(option) => option.display_name}
                    value={anagrafiche.find(a => a.id === formData.referente_esterno) || null}
                    onChange={(_, newValue) => {
                      setFormData({ ...formData, referente_esterno: newValue?.id || null });
                    }}
                    onInputChange={(_, newInputValue) => {
                      setSearchAnagrafica(newInputValue);
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Referente Esterno"
                        helperText="Cerca per nome, cognome o ragione sociale"
                      />
                    )}
                    isOptionEqualToValue={(option, value) => option.id === value.id}
                    noOptionsText="Nessuna anagrafica trovata"
                  />
                </Box>
              </Box>

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Note"
                value={formData.note}
                onChange={(e) => setFormData({ ...formData, note: e.target.value })}
              />

              <Box>
                <input
                  accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff"
                  style={{ display: 'none' }}
                  id="verbale-scan-file"
                  type="file"
                  onChange={(e) => setFormData({ ...formData, verbale_scan: e.target.files?.[0] || null })}
                />
                <label htmlFor="verbale-scan-file">
                  <Button variant="outlined" component="span">
                    Carica Verbale Scansionato
                  </Button>
                </label>
                {formData.verbale_scan && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    File: {formData.verbale_scan.name}
                  </Typography>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Righe */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Documenti/Fascicoli Movimentati
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={addRiga}
              >
                Aggiungi Riga
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />

            {formData.righe.length === 0 ? (
              <Alert severity="info">Nessuna riga aggiunta. Clicca "Aggiungi Riga" per iniziare.</Alert>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Documento/Fascicolo</TableCell>
                      <TableCell>Da Unità</TableCell>
                      <TableCell>A Unità</TableCell>
                      <TableCell>Stato Nuovo</TableCell>
                      <TableCell>Note</TableCell>
                      <TableCell width={50}></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {formData.righe.map((riga, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <DocumentoFascicoloSelector
                              tipo="documento"
                              tipoOperazione={formData.tipo_operazione}
                              referenteEsterno={formData.referente_esterno}
                              value={riga.documento}
                              onChange={(id, oggetto) => updateRiga(index, 'documento', id, oggetto)}
                            />
                            <DocumentoFascicoloSelector
                              tipo="fascicolo"
                              tipoOperazione={formData.tipo_operazione}
                              referenteEsterno={formData.referente_esterno}
                              value={riga.fascicolo}
                              onChange={(id, oggetto) => updateRiga(index, 'fascicolo', id, oggetto)}
                            />
                          </Box>
                        </TableCell>
                        <TableCell>
                          <UnitaFisicaSelector
                            value={riga.unita_fisica_sorgente}
                            onChange={(id) => updateRiga(index, 'unita_fisica_sorgente', id)}
                            disabled={formData.tipo_operazione === 'entrata'}
                            label="Da Unità"
                            helperText={
                              formData.tipo_operazione === 'entrata' 
                                ? 'Non necessaria per entrate'
                                : formData.tipo_operazione === 'uscita'
                                  ? 'Ubicazione corrente (non modificabile)'
                                  : 'Ubicazione di partenza (modificabile)'
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <UnitaFisicaSelector
                            value={riga.unita_fisica_destinazione}
                            onChange={(id) => updateRiga(index, 'unita_fisica_destinazione', id)}
                            disabled={formData.tipo_operazione === 'uscita'}
                            label="A Unità"
                            helperText={
                              formData.tipo_operazione === 'entrata'
                                ? 'Ubicazione di arrivo (modificabile)'
                                : formData.tipo_operazione === 'uscita'
                                  ? 'Archivio di scarico (automatico)'
                                  : 'Ubicazione di arrivo (modificabile)'
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            fullWidth
                            label="Stato"
                            value={riga.stato_successivo || ''}
                            onChange={(e) => updateRiga(index, 'stato_successivo', e.target.value)}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            fullWidth
                            label="Note"
                            value={riga.note || ''}
                            onChange={(e) => updateRiga(index, 'note', e.target.value)}
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => removeRiga(index)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>

        {/* Azioni */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            component={Link}
            to="/archivio-fisico/operazioni"
            disabled={saving}
          >
            Annulla
          </Button>
          <Button
            type="submit"
            variant="contained"
            startIcon={<SaveIcon />}
            disabled={saving}
          >
            {saving ? 'Salvataggio...' : 'Salva'}
          </Button>
        </Box>
      </form>
    </Box>
  );
};

export default OperazioneArchivioForm;
