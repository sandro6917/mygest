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
  Paper,
  Divider,
  Stack,
  IconButton,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  ArrowBack as BackIcon,
  CheckCircle as SuccessIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { documentiApi } from '@/api/documenti';
import { toast } from 'react-toastify';

interface PreviewData {
  datore: {
    codice_fiscale: string;
    tipo: 'PF' | 'PG';
    // PG fields
    ragione_sociale?: string;
    // PF fields
    cognome?: string;
    nome?: string;
    // Common fields
    settore?: string;
    comune?: string;
    cap?: string;
    indirizzo?: string;
    telefono?: string;
    email?: string;
    // Flags
    esiste?: boolean;
    anagrafica_id?: number;
    cliente_id?: number;
    crea_se_non_esiste?: boolean;
    crea_cliente?: boolean;
  };
  lavoratore: {
    codice_fiscale: string;
    tipo: 'PF';
    cognome: string;
    nome: string;
    sesso?: string;
    data_nascita?: string;
    comune_nascita?: string;
    cittadinanza?: string;
    comune?: string;
    cap?: string;
    indirizzo?: string;
    livello_istruzione?: string;
    // Flags
    esiste?: boolean;
    anagrafica_id?: number;
    crea_se_non_esiste?: boolean;
  };
  documento: {
    codice_comunicazione: string;
    tipo_comunicazione?: string;
    modello?: string;
    data_comunicazione?: string;
    dipendente?: number;
    tipo?: string;
    data_da?: string;
    data_a?: string;
    data_proroga?: string;  // Data fine proroga per comunicazioni di proroga
    data_trasformazione?: string;  // Data trasformazione per comunicazioni di trasformazione
    causa_trasformazione?: string;  // Motivo trasformazione
    qualifica?: string;
    contratto_collettivo?: string;
    livello?: string;
    retribuzione?: string;
    ore_settimanali?: string;
    tipo_orario?: string;
    centro_impiego?: string;
    provincia_impiego?: string;
    ente_previdenziale?: string;
    codice_ente_previdenziale?: string;
    pat_inail?: string;
  };
  file_temp_path: string;
  // Controllo duplicati
  duplicato?: boolean;
  documento_esistente?: {
    id: number;
    codice: string;
    descrizione: string;
    data_documento: string | null;
    cliente_id: number;
    cliente_nome: string | null;
    url: string;
    attributi_attuali: {
      tipo: string | null;
      data_da: string | null;
      data_a: string | null;
      qualifica: string | null;
      contratto_collettivo: string | null;
      livello: string | null;
      retribuzione: string | null;
    };
  };
}

export function ImportaUnilavPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [editedData, setEditedData] = useState<PreviewData | null>(null);
  const [importing, setImporting] = useState(false);
  const [azioneSelezionata, setAzioneSelezionata] = useState<'crea' | 'sovrascrivi' | 'duplica'>('crea');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        toast.error('Seleziona un file PDF valido');
        return;
      }
      setSelectedFile(file);
      setPreview(null);
      setEditedData(null);
    }
  };

  const handlePreview = async () => {
    if (!selectedFile) {
      toast.error('Seleziona un file PDF');
      return;
    }

    setUploading(true);

    try {
      const response = await documentiApi.importaUnilavPreview(selectedFile);
      setPreview(response);
      setEditedData(response);
      toast.success('Dati estratti con successo! Controlla e conferma.');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Errore durante l\'estrazione dei dati');
      console.error('Errore preview UNILAV:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleConfirm = async () => {
    if (!editedData) {
      toast.error('Nessun dato da importare');
      return;
    }

    setImporting(true);

    try {
      // Prepara payload con azione selezionata
      const payload = {
        ...editedData,
        azione: azioneSelezionata,
        documento_id_esistente: editedData.documento_esistente?.id || null,
      };
      
      const response = await documentiApi.importaUnilavConfirm(payload);
      
      if (response.success) {
        const azione_msg = azioneSelezionata === 'sovrascrivi' 
          ? 'sovrascritto' 
          : azioneSelezionata === 'duplica' 
            ? 'duplicato creato'
            : 'importato';
        toast.success(response.message || `Documento UNILAV ${azione_msg} con successo!`);
        
        // Naviga al documento creato/aggiornato
        if (response.documento_id) {
          setTimeout(() => {
            navigate(`/documenti/${response.documento_id}`);
          }, 1500);
        } else {
          setTimeout(() => {
            navigate('/documenti');
          }, 1500);
        }
      } else {
        toast.error('Errore durante l\'importazione');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Errore durante l\'importazione');
      console.error('Errore conferma UNILAV:', error);
    } finally {
      setImporting(false);
    }
  };

  const updateDatore = (field: string, value: string) => {
    if (!editedData) return;
    setEditedData({
      ...editedData,
      datore: { ...editedData.datore, [field]: value },
    });
  };

  const updateLavoratore = (field: string, value: string) => {
    if (!editedData) return;
    setEditedData({
      ...editedData,
      lavoratore: { ...editedData.lavoratore, [field]: value },
    });
  };

  const updateUnilav = (field: string, value: string) => {
    if (!editedData) return;
    setEditedData({
      ...editedData,
      documento: { ...editedData.documento, [field]: value },
    });
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton onClick={() => navigate('/documenti')} sx={{ mr: 2 }}>
            <BackIcon />
          </IconButton>
          <Typography variant="h4">Importa Documento UNILAV</Typography>
        </Box>

        {/* Upload Section */}
        {!preview && (
          <Card>
            <CardContent>
              <Stack spacing={3}>
                <Alert severity="info">
                  Carica un file PDF UNILAV. Il sistema estrarrà automaticamente i dati del
                  datore di lavoro, del lavoratore e della comunicazione.
                </Alert>

                <Box>
                  <input
                    accept="application/pdf"
                    style={{ display: 'none' }}
                    id="unilav-file-upload"
                    type="file"
                    onChange={handleFileSelect}
                  />
                  <label htmlFor="unilav-file-upload">
                    <Button
                      variant="outlined"
                      component="span"
                      startIcon={<UploadIcon />}
                      fullWidth
                      sx={{ py: 2 }}
                    >
                      Seleziona File PDF UNILAV
                    </Button>
                  </label>
                </Box>

                {selectedFile && (
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      File selezionato:
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {selectedFile.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </Typography>
                  </Paper>
                )}

                {selectedFile && (
                  <Button
                    variant="contained"
                    onClick={handlePreview}
                    disabled={uploading}
                    fullWidth
                    size="large"
                  >
                    {uploading ? 'Estrazione dati in corso...' : 'Estrai Dati'}
                  </Button>
                )}

                {uploading && <LinearProgress />}
              </Stack>
            </CardContent>
          </Card>
        )}

        {/* Preview & Edit Section */}
        {preview && editedData && (
          <Stack spacing={3}>
            <Alert severity="success" icon={<SuccessIcon />}>
              Dati estratti con successo! Controlla i dati e modifica se necessario, poi conferma l'importazione.
            </Alert>

            {/* ALERT DUPLICATO */}
            {editedData.duplicato && editedData.documento_esistente && (
              <Alert 
                severity="error" 
                sx={{ 
                  border: '2px solid',
                  borderColor: 'error.main',
                  '& .MuiAlert-message': { width: '100%' }
                }}
              >
                <Typography variant="h6" gutterBottom color="error">
                  ⚠️ ATTENZIONE: Documento già importato!
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    <strong>Codice documento:</strong> {editedData.documento_esistente.codice}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Descrizione:</strong> {editedData.documento_esistente.descrizione}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Cliente:</strong> {editedData.documento_esistente.cliente_nome || 'N/D'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Data documento:</strong> {editedData.documento_esistente.data_documento || 'N/D'}
                  </Typography>
                  
                  <Button
                    size="small"
                    variant="outlined"
                    color="error"
                    sx={{ mt: 2 }}
                    onClick={() => navigate(`/documenti/${editedData.documento_esistente!.id}`)}
                  >
                    Visualizza documento esistente →
                  </Button>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle2" gutterBottom>
                  📊 Confronto dati (Esistente → Nuovo):
                </Typography>
                
                <Box sx={{ mt: 1, pl: 2 }}>
                  {editedData.documento_esistente.attributi_attuali.tipo !== editedData.documento.tipo && (
                    <Typography variant="body2" color="warning.main">
                      • <strong>Tipo:</strong> {editedData.documento_esistente.attributi_attuali.tipo || 'N/D'} → <strong>{editedData.documento.tipo}</strong>
                    </Typography>
                  )}
                  {editedData.documento_esistente.attributi_attuali.data_da !== editedData.documento.data_da && (
                    <Typography variant="body2" color="warning.main">
                      • <strong>Data inizio:</strong> {editedData.documento_esistente.attributi_attuali.data_da || 'N/D'} → <strong>{editedData.documento.data_da}</strong>
                    </Typography>
                  )}
                  {editedData.documento_esistente.attributi_attuali.data_a !== editedData.documento.data_a && (
                    <Typography variant="body2" color="warning.main">
                      • <strong>Data fine:</strong> {editedData.documento_esistente.attributi_attuali.data_a || 'N/D'} → <strong>{editedData.documento.data_a}</strong>
                    </Typography>
                  )}
                  {editedData.documento_esistente.attributi_attuali.qualifica !== editedData.documento.qualifica && (
                    <Typography variant="body2" color="warning.main">
                      • <strong>Qualifica:</strong> {editedData.documento_esistente.attributi_attuali.qualifica || 'N/D'} → <strong>{editedData.documento.qualifica}</strong>
                    </Typography>
                  )}
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle2" gutterBottom>
                  🎯 Scegli azione:
                </Typography>
                
                <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                  <Button
                    variant={azioneSelezionata === 'sovrascrivi' ? 'contained' : 'outlined'}
                    color="warning"
                    onClick={() => setAzioneSelezionata('sovrascrivi')}
                    size="small"
                  >
                    🔄 Sovrascrivi
                  </Button>
                  <Button
                    variant={azioneSelezionata === 'duplica' ? 'contained' : 'outlined'}
                    color="info"
                    onClick={() => setAzioneSelezionata('duplica')}
                    size="small"
                  >
                    ➕ Aggiungi comunque
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => {
                      setPreview(null);
                      setEditedData(null);
                      setSelectedFile(null);
                    }}
                    size="small"
                  >
                    ❌ Annulla
                  </Button>
                </Stack>
              </Alert>
            )}

            {/* Datore di Lavoro */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📋 Datore di Lavoro
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {/* Alert se anagrafica esiste */}
                {editedData.datore.esiste && editedData.datore.anagrafica_id && (
                  <Alert 
                    severity="info" 
                    sx={{ mb: 2 }}
                    action={
                      <Button
                        color="inherit"
                        size="small"
                        onClick={() => window.open(`/anagrafiche/${editedData.datore.anagrafica_id}`, '_blank')}
                      >
                        Visualizza
                      </Button>
                    }
                  >
                    <strong>Anagrafica esistente trovata</strong> (ID: {editedData.datore.anagrafica_id})
                    <br />
                    L'anagrafica con questo codice fiscale esiste già. Verrà utilizzata quella esistente senza modifiche.
                    {editedData.datore.cliente_id && (
                      <> È già un cliente (ID: {editedData.datore.cliente_id}).</>
                    )}
                  </Alert>
                )}
                
                {!editedData.datore.esiste && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <strong>Nuova anagrafica</strong>
                    <br />
                    Questa anagrafica non esiste. Verrà creata una nuova anagrafica e un nuovo cliente.
                  </Alert>
                )}
                
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Codice Fiscale"
                      value={editedData.datore.codice_fiscale}
                      onChange={(e) => updateDatore('codice_fiscale', e.target.value)}
                      fullWidth
                      required
                      helperText={editedData.datore.tipo === 'PG' ? '11 cifre (P.IVA)' : '16 caratteri (CF)'}
                    />
                    <TextField
                      label="Tipo"
                      value={editedData.datore.tipo}
                      disabled
                      sx={{ maxWidth: 100 }}
                      helperText={editedData.datore.tipo === 'PG' ? 'P.G.' : 'P.F.'}
                    />
                  </Box>
                  
                  {/* Campi specifici per PG */}
                  {editedData.datore.tipo === 'PG' && (
                    <TextField
                      label="Ragione Sociale"
                      value={editedData.datore.ragione_sociale || ''}
                      onChange={(e) => updateDatore('ragione_sociale', e.target.value)}
                      fullWidth
                      required
                    />
                  )}
                  
                  {/* Campi specifici per PF */}
                  {editedData.datore.tipo === 'PF' && (
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <TextField
                        label="Cognome"
                        value={editedData.datore.cognome || ''}
                        onChange={(e) => updateDatore('cognome', e.target.value)}
                        fullWidth
                        required
                      />
                      <TextField
                        label="Nome"
                        value={editedData.datore.nome || ''}
                        onChange={(e) => updateDatore('nome', e.target.value)}
                        fullWidth
                        required
                      />
                    </Box>
                  )}
                  
                  <TextField
                    label="Settore"
                    value={editedData.datore.settore || ''}
                    onChange={(e) => updateDatore('settore', e.target.value)}
                    fullWidth
                  />
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Comune"
                      value={editedData.datore.comune || ''}
                      onChange={(e) => updateDatore('comune', e.target.value)}
                      fullWidth
                    />
                    <TextField
                      label="CAP"
                      value={editedData.datore.cap || ''}
                      onChange={(e) => updateDatore('cap', e.target.value)}
                      sx={{ maxWidth: 150 }}
                    />
                  </Box>
                  <TextField
                    label="Indirizzo"
                    value={editedData.datore.indirizzo || ''}
                    onChange={(e) => updateDatore('indirizzo', e.target.value)}
                    fullWidth
                  />
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Telefono"
                      value={editedData.datore.telefono || ''}
                      onChange={(e) => updateDatore('telefono', e.target.value)}
                      fullWidth
                    />
                    <TextField
                      label="Email"
                      value={editedData.datore.email || ''}
                      onChange={(e) => updateDatore('email', e.target.value)}
                      fullWidth
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Lavoratore */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  👤 Lavoratore
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {/* Alert se anagrafica esiste */}
                {editedData.lavoratore.esiste && editedData.lavoratore.anagrafica_id && (
                  <Alert 
                    severity="info" 
                    sx={{ mb: 2 }}
                    action={
                      <Button
                        color="inherit"
                        size="small"
                        onClick={() => window.open(`/anagrafiche/${editedData.lavoratore.anagrafica_id}`, '_blank')}
                      >
                        Visualizza
                      </Button>
                    }
                  >
                    <strong>Anagrafica esistente trovata</strong> (ID: {editedData.lavoratore.anagrafica_id})
                    <br />
                    L'anagrafica con questo codice fiscale esiste già. Verrà utilizzata quella esistente senza modifiche.
                  </Alert>
                )}
                
                {!editedData.lavoratore.esiste && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <strong>Nuova anagrafica</strong>
                    <br />
                    Questa anagrafica non esiste. Verrà creata una nuova anagrafica (non cliente).
                  </Alert>
                )}
                
                <Stack spacing={2}>
                  <TextField
                    label="Codice Fiscale"
                    value={editedData.lavoratore.codice_fiscale}
                    onChange={(e) => updateLavoratore('codice_fiscale', e.target.value)}
                    fullWidth
                    required
                  />
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Cognome"
                      value={editedData.lavoratore.cognome}
                      onChange={(e) => updateLavoratore('cognome', e.target.value)}
                      fullWidth
                      required
                    />
                    <TextField
                      label="Nome"
                      value={editedData.lavoratore.nome}
                      onChange={(e) => updateLavoratore('nome', e.target.value)}
                      fullWidth
                      required
                    />
                  </Box>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Sesso"
                      value={editedData.lavoratore.sesso || ''}
                      onChange={(e) => updateLavoratore('sesso', e.target.value)}
                      sx={{ maxWidth: 100 }}
                    />
                    <TextField
                      label="Data di Nascita"
                      type="date"
                      value={editedData.lavoratore.data_nascita || ''}
                      onChange={(e) => updateLavoratore('data_nascita', e.target.value)}
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      label="Comune di Nascita"
                      value={editedData.lavoratore.comune_nascita || ''}
                      onChange={(e) => updateLavoratore('comune_nascita', e.target.value)}
                      fullWidth
                    />
                  </Box>
                  <TextField
                    label="Cittadinanza"
                    value={editedData.lavoratore.cittadinanza || ''}
                    onChange={(e) => updateLavoratore('cittadinanza', e.target.value)}
                    fullWidth
                  />
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Comune Domicilio"
                      value={editedData.lavoratore.comune || ''}
                      onChange={(e) => updateLavoratore('comune', e.target.value)}
                      fullWidth
                    />
                    <TextField
                      label="CAP"
                      value={editedData.lavoratore.cap || ''}
                      onChange={(e) => updateLavoratore('cap', e.target.value)}
                      sx={{ maxWidth: 150 }}
                    />
                  </Box>
                  <TextField
                    label="Indirizzo Domicilio"
                    value={editedData.lavoratore.indirizzo || ''}
                    onChange={(e) => updateLavoratore('indirizzo', e.target.value)}
                    fullWidth
                  />
                  <TextField
                    label="Livello di Istruzione"
                    value={editedData.lavoratore.livello_istruzione || ''}
                    onChange={(e) => updateLavoratore('livello_istruzione', e.target.value)}
                    fullWidth
                  />
                </Stack>
              </CardContent>
            </Card>

            {/* Comunicazione UNILAV */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📄 Comunicazione UNILAV
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Codice Comunicazione"
                      value={editedData.documento.codice_comunicazione}
                      onChange={(e) => updateUnilav('codice_comunicazione', e.target.value)}
                      fullWidth
                      required
                    />
                    <TextField
                      label="Tipo Comunicazione"
                      value={editedData.documento.tipo_comunicazione || ''}
                      onChange={(e) => updateUnilav('tipo_comunicazione', e.target.value)}
                      fullWidth
                    />
                  </Box>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Data Comunicazione"
                      type="date"
                      value={editedData.documento.data_comunicazione || ''}
                      onChange={(e) => updateUnilav('data_comunicazione', e.target.value)}
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      label="Data Inizio Rapporto"
                      type="date"
                      value={editedData.documento.data_da || ''}
                      onChange={(e) => updateUnilav('data_da', e.target.value)}
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      label="Data Fine Rapporto"
                      type="date"
                      value={editedData.documento.data_a || ''}
                      onChange={(e) => updateUnilav('data_a', e.target.value)}
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                    />
                  </Box>
                  {/* Data Fine Proroga - visibile solo per comunicazioni di Proroga */}
                  {editedData.documento.tipo === 'Proroga' && (
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <TextField
                        label="Data Fine Proroga"
                        type="date"
                        value={editedData.documento.data_proroga || ''}
                        onChange={(e) => updateUnilav('data_proroga', e.target.value)}
                        fullWidth
                        InputLabelProps={{ shrink: true }}
                        helperText="Data di fine della proroga contrattuale"
                      />
                    </Box>
                  )}
                  {/* Dati Trasformazione - visibili solo per comunicazioni di Trasformazione */}
                  {editedData.documento.tipo === 'Trasformazione' && (
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <TextField
                        label="Data Trasformazione"
                        type="date"
                        value={editedData.documento.data_trasformazione || ''}
                        onChange={(e) => updateUnilav('data_trasformazione', e.target.value)}
                        fullWidth
                        InputLabelProps={{ shrink: true }}
                        helperText="Data di decorrenza della trasformazione"
                      />
                      <TextField
                        label="Causa Trasformazione"
                        value={editedData.documento.causa_trasformazione || ''}
                        onChange={(e) => updateUnilav('causa_trasformazione', e.target.value)}
                        fullWidth
                        helperText="Motivo della trasformazione contrattuale"
                      />
                    </Box>
                  )}
                  <FormControl fullWidth>
                    <InputLabel>Tipologia Comunicazione *</InputLabel>
                    <Select
                      value={editedData.documento.tipo || ''}
                      onChange={(e) => updateUnilav('tipo', e.target.value)}
                      label="Tipologia Comunicazione *"
                      required
                    >
                      <MenuItem value="">
                        <em>Seleziona tipologia</em>
                      </MenuItem>
                      <MenuItem value="Assunzione">Assunzione</MenuItem>
                      <MenuItem value="Proroga">Proroga</MenuItem>
                      <MenuItem value="Trasformazione">Trasformazione</MenuItem>
                      <MenuItem value="Cessazione">Cessazione</MenuItem>
                    </Select>
                  </FormControl>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Tipo Orario"
                      value={editedData.documento.tipo_orario || ''}
                      onChange={(e) => updateUnilav('tipo_orario', e.target.value)}
                      fullWidth
                    />
                    <TextField
                      label="Ore Settimanali"
                      value={editedData.documento.ore_settimanali || ''}
                      onChange={(e) => updateUnilav('ore_settimanali', e.target.value)}
                      fullWidth
                    />
                  </Box>
                  <TextField
                    label="Qualifica Professionale"
                    value={editedData.documento.qualifica || ''}
                    onChange={(e) => updateUnilav('qualifica', e.target.value)}
                    fullWidth
                  />
                  <TextField
                    label="Contratto Collettivo"
                    value={editedData.documento.contratto_collettivo || ''}
                    onChange={(e) => updateUnilav('contratto_collettivo', e.target.value)}
                    fullWidth
                  />
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      label="Livello Inquadramento"
                      value={editedData.documento.livello || ''}
                      onChange={(e) => updateUnilav('livello', e.target.value)}
                      fullWidth
                    />
                    <TextField
                      label="Retribuzione"
                      value={editedData.documento.retribuzione || ''}
                      onChange={(e) => updateUnilav('retribuzione', e.target.value)}
                      fullWidth
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Riepilogo Documento UNILAV da Creare */}
            <Card sx={{ bgcolor: 'primary.50', borderLeft: 4, borderColor: 'primary.main' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom color="primary">
                  📋 Riepilogo Documento da Creare
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Alert severity="info" sx={{ mb: 2 }}>
                  Verrà creato un documento UNILAV con i seguenti dati:
                </Alert>

                <Stack spacing={1.5}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Tipo Documento:
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      UNILAV (Comunicazione Obbligatoria)
                    </Typography>
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Cliente (Datore di Lavoro):
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {editedData.datore.tipo === 'PG' 
                        ? editedData.datore.ragione_sociale 
                        : `${editedData.datore.cognome} ${editedData.datore.nome}`}
                      {' '}
                      <Typography component="span" variant="body2" color="text.secondary">
                        (CF: {editedData.datore.codice_fiscale})
                      </Typography>
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Descrizione:
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      UNILAV {editedData.documento.codice_comunicazione} - {editedData.lavoratore.cognome} {editedData.lavoratore.nome}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Data Documento:
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {editedData.documento.data_comunicazione 
                        ? new Date(editedData.documento.data_comunicazione).toLocaleDateString('it-IT')
                        : 'Non specificata'}
                    </Typography>
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Attributi Dinamici:
                    </Typography>
                    <Stack spacing={0.5} sx={{ pl: 2 }}>
                      {editedData.documento.codice_comunicazione && (
                        <Typography variant="body2">
                          • <strong>Codice Comunicazione:</strong> {editedData.documento.codice_comunicazione}
                        </Typography>
                      )}
                      <Typography variant="body2">
                        • <strong>Dipendente:</strong> {editedData.lavoratore.cognome} {editedData.lavoratore.nome} (CF: {editedData.lavoratore.codice_fiscale})
                      </Typography>
                      {editedData.documento.tipo && (
                        <Typography variant="body2">
                          • <strong>Tipo Contratto:</strong> {editedData.documento.tipo}
                        </Typography>
                      )}
                      {editedData.documento.data_da && (
                        <Typography variant="body2">
                          • <strong>Data Inizio:</strong> {new Date(editedData.documento.data_da).toLocaleDateString('it-IT')}
                        </Typography>
                      )}
                      {editedData.documento.data_a && (
                        <Typography variant="body2">
                          • <strong>Data Fine:</strong> {new Date(editedData.documento.data_a).toLocaleDateString('it-IT')}
                        </Typography>
                      )}
                      {editedData.documento.data_proroga && (
                        <Typography variant="body2">
                          • <strong>Data Fine Proroga:</strong> {new Date(editedData.documento.data_proroga).toLocaleDateString('it-IT')}
                        </Typography>
                      )}
                      {editedData.documento.data_trasformazione && (
                        <Typography variant="body2">
                          • <strong>Data Trasformazione:</strong> {new Date(editedData.documento.data_trasformazione).toLocaleDateString('it-IT')}
                        </Typography>
                      )}
                      {editedData.documento.causa_trasformazione && (
                        <Typography variant="body2">
                          • <strong>Causa Trasformazione:</strong> {editedData.documento.causa_trasformazione}
                        </Typography>
                      )}
                    </Stack>
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Dati Aggiuntivi (salvati nelle Note):
                    </Typography>
                    <Stack spacing={0.5} sx={{ pl: 2 }}>
                      {editedData.documento.qualifica && (
                        <Typography variant="body2">
                          • <strong>Qualifica:</strong> {editedData.documento.qualifica}
                        </Typography>
                      )}
                      {editedData.documento.contratto_collettivo && (
                        <Typography variant="body2">
                          • <strong>CCNL:</strong> {editedData.documento.contratto_collettivo}
                        </Typography>
                      )}
                      {editedData.documento.livello && (
                        <Typography variant="body2">
                          • <strong>Livello:</strong> {editedData.documento.livello}
                        </Typography>
                      )}
                      {editedData.documento.retribuzione && (
                        <Typography variant="body2">
                          • <strong>Retribuzione:</strong> {editedData.documento.retribuzione}
                        </Typography>
                      )}
                      {editedData.documento.ore_settimanali && (
                        <Typography variant="body2">
                          • <strong>Ore Settimanali:</strong> {editedData.documento.ore_settimanali}
                        </Typography>
                      )}
                      {editedData.documento.tipo_orario && (
                        <Typography variant="body2">
                          • <strong>Tipo Orario:</strong> {editedData.documento.tipo_orario}
                        </Typography>
                      )}
                      {!editedData.documento.qualifica && 
                       !editedData.documento.contratto_collettivo && 
                       !editedData.documento.livello && 
                       !editedData.documento.retribuzione && 
                       !editedData.documento.ore_settimanali && 
                       !editedData.documento.tipo_orario && (
                        <Typography variant="body2" color="text.secondary" fontStyle="italic">
                          Nessun dato aggiuntivo
                        </Typography>
                      )}
                    </Stack>
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Caratteristiche Documento:
                    </Typography>
                    <Stack spacing={0.5} sx={{ pl: 2 }}>
                      <Typography variant="body2">
                        • <strong>Digitale:</strong> Sì (file PDF allegato)
                      </Typography>
                      <Typography variant="body2">
                        • <strong>Tracciabile:</strong> Sì (protocollabile)
                      </Typography>
                      <Typography variant="body2">
                        • <strong>Stato:</strong> Definitivo
                      </Typography>
                    </Stack>
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Actions */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={() => {
                  setPreview(null);
                  setEditedData(null);
                  setSelectedFile(null);
                }}
              >
                Annulla
              </Button>
              <Button
                variant="contained"
                onClick={handleConfirm}
                disabled={importing}
                startIcon={<SendIcon />}
                size="large"
              >
                {importing ? 'Importazione in corso...' : 'Conferma Importazione'}
              </Button>
            </Box>

            {importing && <LinearProgress />}
          </Stack>
        )}
      </Box>
    </Container>
  );
}
