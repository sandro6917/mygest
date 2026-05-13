import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
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
  FormControlLabel,
  Checkbox,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Save as SaveIcon } from '@mui/icons-material';
import { toast } from 'react-toastify';
import { getUnitaFisica, createUnitaFisica, updateUnitaFisica } from '@/api/archivioFisico';
import type { UnitaFisica, TipoUnitaFisica } from '@/types/archivioFisico';
import UnitaFisicaSelector from '@/components/ArchivioFisico/UnitaFisicaSelector';

const TIPI_UNITA: { value: TipoUnitaFisica; label: string }[] = [
  { value: 'ufficio', label: 'Ufficio' },
  { value: 'stanza', label: 'Stanza' },
  { value: 'scaffale', label: 'Scaffale' },
  { value: 'mobile', label: 'Mobile' },
  { value: 'anta', label: 'Anta' },
  { value: 'ripiano', label: 'Ripiano' },
  { value: 'contenitore', label: 'Contenitore' },
  { value: 'cartellina', label: 'Cartellina' },
];

const UnitaFisicaFormPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<Partial<UnitaFisica>>({
    codice: '',
    nome: '',
    tipo: 'contenitore',
    parent: searchParams.get('parent') ? Number(searchParams.get('parent')) : null,
    attivo: true,
    archivio_fisso: false,
    ordine: 0,
    note: '',
  });

  useEffect(() => {
    if (isEdit && id) {
      loadUnita(Number(id));
    }
  }, [id]);

  const loadUnita = async (unitaId: number) => {
    try {
      setLoading(true);
      const data = await getUnitaFisica(unitaId);
      setFormData({
        codice: data.codice,
        nome: data.nome,
        tipo: data.tipo,
        parent: data.parent ?? null,
        attivo: data.attivo,
        archivio_fisso: data.archivio_fisso,
        ordine: data.ordine ?? 0,
        note: data.note ?? '',
      });
    } catch {
      setError('Errore nel caricamento dei dati');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.codice?.trim() || !formData.nome?.trim() || !formData.tipo) {
      setError('Codice, nome e tipo sono obbligatori');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      if (isEdit && id) {
        await updateUnitaFisica(Number(id), formData);
        toast.success('Unità fisica aggiornata');
        navigate(`/archivio/unita/${id}`);
      } else {
        const created = await createUnitaFisica(formData);
        toast.success('Unità fisica creata');
        navigate(`/archivio/unita/${created.id}`);
      }
    } catch {
      setError('Errore durante il salvataggio');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (isEdit && id) {
      navigate(`/archivio/unita/${id}`);
    } else {
      navigate('/archivio');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 700, mx: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={handleCancel} variant="outlined" size="small">
          Indietro
        </Button>
        <Typography variant="h5">
          {isEdit ? 'Modifica Unità Fisica' : 'Nuova Unità Fisica'}
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Card>
        <CardContent>
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Codice"
                value={formData.codice ?? ''}
                onChange={e => setFormData(p => ({ ...p, codice: e.target.value }))}
                required
                size="small"
                sx={{ flex: 1 }}
              />
              <TextField
                label="Nome"
                value={formData.nome ?? ''}
                onChange={e => setFormData(p => ({ ...p, nome: e.target.value }))}
                required
                size="small"
                sx={{ flex: 2 }}
              />
            </Box>

            <FormControl size="small" required>
              <InputLabel>Tipo</InputLabel>
              <Select
                value={formData.tipo ?? ''}
                label="Tipo"
                onChange={e => setFormData(p => ({ ...p, tipo: e.target.value as TipoUnitaFisica }))}
              >
                {TIPI_UNITA.map(t => (
                  <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <UnitaFisicaSelector
              value={formData.parent ?? null}
              onChange={parentId => setFormData(p => ({ ...p, parent: parentId }))}
              label="Unità Padre (opzionale)"
            />

            <TextField
              label="Ordine"
              type="number"
              value={formData.ordine ?? 0}
              onChange={e => setFormData(p => ({ ...p, ordine: Number(e.target.value) }))}
              size="small"
              inputProps={{ min: 0 }}
              sx={{ width: 150 }}
            />

            <TextField
              label="Note"
              value={formData.note ?? ''}
              onChange={e => setFormData(p => ({ ...p, note: e.target.value }))}
              multiline
              rows={3}
              size="small"
            />

            <Box sx={{ display: 'flex', gap: 3 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.attivo ?? true}
                    onChange={e => setFormData(p => ({ ...p, attivo: e.target.checked }))}
                  />
                }
                label="Attivo"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.archivio_fisso ?? false}
                    onChange={e => setFormData(p => ({ ...p, archivio_fisso: e.target.checked }))}
                  />
                }
                label="Archivio Fisso"
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button onClick={handleCancel} variant="outlined" disabled={saving}>
                Annulla
              </Button>
              <Button
                type="submit"
                variant="contained"
                startIcon={saving ? <CircularProgress size={18} /> : <SaveIcon />}
                disabled={saving}
              >
                {isEdit ? 'Salva modifiche' : 'Crea unità'}
              </Button>
            </Box>

          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default UnitaFisicaFormPage;
