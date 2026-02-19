/**
 * Pagina lista operazioni di archivio fisico
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Pagination,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast } from 'react-toastify';

import { getOperazioniArchivio, deleteOperazioneArchivio } from '../../api/archivioFisico';
import type { OperazioneArchivio, TipoOperazioneArchivio, OperazioneArchivioFilters } from '../../types/archivioFisico';

const OperazioniArchivioList: React.FC = () => {
  const [operazioni, setOperazioni] = useState<OperazioneArchivio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  const [filters, setFilters] = useState<OperazioneArchivioFilters>({});
  const [showFilters, setShowFilters] = useState(false);

  const fetchOperazioni = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getOperazioniArchivio(filters, page, pageSize);
      setOperazioni(response.results);
      setTotalCount(response.count);
      setTotalPages(Math.ceil(response.count / pageSize));
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento delle operazioni');
      toast.error('Errore nel caricamento delle operazioni');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOperazioni();
  }, [page, filters]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questa operazione?')) {
      return;
    }

    try {
      await deleteOperazioneArchivio(id);
      toast.success('Operazione eliminata con successo');
      fetchOperazioni();
    } catch (err: any) {
      toast.error('Errore nell\'eliminazione dell\'operazione');
    }
  };

  const handleFilterChange = (field: keyof OperazioneArchivioFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value || undefined,
    }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  const getTipoChipColor = (tipo: TipoOperazioneArchivio) => {
    switch (tipo) {
      case 'entrata':
        return 'success';
      case 'uscita':
        return 'error';
      case 'interna':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Operazioni Archivio Fisico
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
          >
            {showFilters ? 'Nascondi Filtri' : 'Mostra Filtri'}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            component={Link}
            to="/archivio-fisico/operazioni/nuova"
          >
            Nuova Operazione
          </Button>
        </Box>
      </Box>

      {/* Filtri */}
      {showFilters && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Tipo Operazione</InputLabel>
                <Select
                  value={filters.tipo_operazione || ''}
                  onChange={(e) => handleFilterChange('tipo_operazione', e.target.value)}
                  label="Tipo Operazione"
                >
                  <MenuItem value="">Tutti</MenuItem>
                  <MenuItem value="entrata">Entrata</MenuItem>
                  <MenuItem value="uscita">Uscita</MenuItem>
                  <MenuItem value="interna">Movimento Interno</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label="Data Dal"
                type="date"
                value={filters.data_dal || ''}
                onChange={(e) => handleFilterChange('data_dal', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
              
              <TextField
                fullWidth
                label="Data Al"
                type="date"
                value={filters.data_al || ''}
                onChange={(e) => handleFilterChange('data_al', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
              
              <TextField
                fullWidth
                label="Cerca"
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Note, referente..."
              />
            </Box>
            
            <Box sx={{ mt: 2 }}>
              <Button variant="outlined" onClick={clearFilters}>
                Pulisci Filtri
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Contenuto */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : operazioni.length === 0 ? (
        <Alert severity="info">Nessuna operazione trovata</Alert>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Data/Ora</TableCell>
                  <TableCell>Referente Interno</TableCell>
                  <TableCell>Referente Esterno</TableCell>
                  <TableCell align="center">N. Righe</TableCell>
                  <TableCell>Note</TableCell>
                  <TableCell align="center">Azioni</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {operazioni.map((operazione) => (
                  <TableRow key={operazione.id} hover>
                    <TableCell>{operazione.id}</TableCell>
                    <TableCell>
                      <Chip
                        label={operazione.tipo_operazione_display}
                        color={getTipoChipColor(operazione.tipo_operazione)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {operazione.data_ora && format(new Date(operazione.data_ora), 'dd/MM/yyyy HH:mm', { locale: it })}
                    </TableCell>
                    <TableCell>
                      {operazione.referente_interno_detail?.display_name || '-'}
                    </TableCell>
                    <TableCell>
                      {operazione.referente_esterno_detail?.display_name || '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Chip label={operazione.righe_count || 0} size="small" />
                    </TableCell>
                    <TableCell>
                      {operazione.note ? (
                        <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                          {operazione.note}
                        </Typography>
                      ) : '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                        <IconButton
                          size="small"
                          component={Link}
                          to={`/archivio-fisico/operazioni/${operazione.id}`}
                          color="primary"
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          component={Link}
                          to={`/archivio-fisico/operazioni/${operazione.id}/modifica`}
                          color="info"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => operazione.id && handleDelete(operazione.id)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Paginazione */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Totale: {totalCount} operazioni
            </Typography>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, value) => setPage(value)}
              color="primary"
            />
          </Box>
        </>
      )}
    </Box>
  );
};

export default OperazioniArchivioList;
