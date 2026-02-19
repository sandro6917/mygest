/**
 * Componente dettaglio operazione archivio
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  PlayArrow as ProcessIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast } from 'react-toastify';

import {
  getOperazioneArchivio,
  deleteOperazioneArchivio,
  processOperazioneArchivio,
  downloadVerbaleConsegna,
  getVerbaleTemplates,
} from '../../api/archivioFisico';
import type { OperazioneArchivio, VerbaleConsegnaTemplate } from '../../types/archivioFisico';

const OperazioneArchivioDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [operazione, setOperazione] = useState<OperazioneArchivio | null>(null);
  const [templates, setTemplates] = useState<VerbaleConsegnaTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const fetchData = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      const [opData, templatesData] = await Promise.all([
        getOperazioneArchivio(parseInt(id)),
        getVerbaleTemplates(),
      ]);
      setOperazione(opData);
      setTemplates(templatesData);
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento dell\'operazione');
      toast.error('Errore nel caricamento dell\'operazione');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleDelete = async () => {
    if (!operazione?.id || !window.confirm('Sei sicuro di voler eliminare questa operazione?')) {
      return;
    }

    try {
      await deleteOperazioneArchivio(operazione.id);
      toast.success('Operazione eliminata con successo');
      navigate('/archivio-fisico/operazioni');
    } catch (err: any) {
      toast.error('Errore nell\'eliminazione dell\'operazione');
    }
  };

  const handleProcess = async () => {
    if (!operazione?.id || !window.confirm('Processare questa operazione? Verranno aggiornati stati e collocazioni.')) {
      return;
    }

    try {
      setProcessing(true);
      await processOperazioneArchivio(operazione.id);
      toast.success('Operazione processata con successo');
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Errore nel processamento dell\'operazione');
    } finally {
      setProcessing(false);
    }
  };

  const handleDownloadVerbale = async (templateSlug?: string) => {
    if (!operazione?.id) return;

    try {
      await downloadVerbaleConsegna(operazione.id, templateSlug);
      toast.success('Download avviato');
    } catch (err: any) {
      toast.error('Errore nel download del verbale');
    }
    setAnchorEl(null);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !operazione) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error || 'Operazione non trovata'}</Alert>
        <Button
          sx={{ mt: 2 }}
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          component={Link}
          to="/archivio-fisico/operazioni"
        >
          Torna alla Lista
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton component={Link} to="/archivio-fisico/operazioni">
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4">
            Operazione #{operazione.id}
          </Typography>
          <Chip
            label={operazione.tipo_operazione_display}
            color={
              operazione.tipo_operazione === 'entrata' ? 'success' :
              operazione.tipo_operazione === 'uscita' ? 'error' : 'info'
            }
          />
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<ProcessIcon />}
            onClick={handleProcess}
            disabled={processing}
          >
            {processing ? 'Processamento...' : 'Processa'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={(e) => setAnchorEl(e.currentTarget)}
          >
            Verbale
          </Button>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
          >
            <MenuItem onClick={() => handleDownloadVerbale()}>
              Template Default
            </MenuItem>
            {templates.map((template) => (
              <MenuItem key={template.id} onClick={() => handleDownloadVerbale(template.slug)}>
                {template.nome}
              </MenuItem>
            ))}
          </Menu>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            component={Link}
            to={`/archivio-fisico/operazioni/${operazione.id}/modifica`}
          >
            Modifica
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
          >
            Elimina
          </Button>
        </Box>
      </Box>

      {/* Dati Principali */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Informazioni Generali
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Data e Ora
              </Typography>
              <Typography variant="body1">
                {operazione.data_ora && format(new Date(operazione.data_ora), 'dd/MM/yyyy HH:mm', { locale: it })}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="text.secondary">
                Tipo Operazione
              </Typography>
              <Typography variant="body1">
                {operazione.tipo_operazione_display}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="text.secondary">
                Referente Interno
              </Typography>
              <Typography variant="body1">
                {operazione.referente_interno_detail?.display_name || '-'}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="text.secondary">
                Referente Esterno
              </Typography>
              <Typography variant="body1">
                {operazione.referente_esterno_detail?.display_name || '-'}
              </Typography>
            </Box>
          </Box>
          
          {operazione.note && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Note
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {operazione.note}
              </Typography>
            </Box>
          )}
          
          {operazione.verbale_scan_url && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Verbale Scansionato
              </Typography>
              <Button
                variant="outlined"
                size="small"
                href={operazione.verbale_scan_url}
                download
                startIcon={<DownloadIcon />}
              >
                Scarica File
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Righe */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Documenti/Fascicoli Movimentati
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          {!operazione.righe || operazione.righe.length === 0 ? (
            <Alert severity="info">Nessun documento o fascicolo movimentato</Alert>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Oggetto</TableCell>
                    <TableCell>Protocollo</TableCell>
                    <TableCell>Da Unità</TableCell>
                    <TableCell>A Unità</TableCell>
                    <TableCell>Stato Precedente</TableCell>
                    <TableCell>Stato Successivo</TableCell>
                    <TableCell>Note</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {operazione.righe.map((riga, index) => (
                    <TableRow key={riga.id || index}>
                      <TableCell>
                        {riga.documento_detail ? (
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              DOC: {riga.documento_detail.codice}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {riga.documento_detail.descrizione}
                            </Typography>
                          </Box>
                        ) : riga.fascicolo_detail ? (
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              FASC: {riga.fascicolo_detail.codice}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {riga.fascicolo_detail.titolo}
                            </Typography>
                          </Box>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        {riga.movimento_protocollo_detail ? (
                          <Box>
                            <Typography variant="body2">
                              {riga.movimento_protocollo_detail.numero}/{riga.movimento_protocollo_detail.anno}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {riga.movimento_protocollo_detail.direzione === 'IN' ? 'Entrata' : 'Uscita'}
                            </Typography>
                          </Box>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        {riga.unita_fisica_sorgente_detail?.full_path || '-'}
                      </TableCell>
                      <TableCell>
                        {riga.unita_fisica_destinazione_detail?.full_path || '-'}
                      </TableCell>
                      <TableCell>
                        <Chip label={riga.stato_precedente || '-'} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip label={riga.stato_successivo || '-'} size="small" color="primary" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">{riga.note || '-'}</Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default OperazioneArchivioDetail;
