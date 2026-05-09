/**
 * Pagina Gestione Template di Estrazione
 */
import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  Autocomplete,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

import {
  useTemplates,
  useCreateTemplate,
  useDeleteTemplate,
} from '@/hooks/useAIImport';
import { documentiApi } from '@/api/documenti';
import type { CreateTemplateRequest } from '@/types/aiImport';
import type { DocumentiTipo } from '@/types/documento';

export const TemplateListPage: React.FC = () => {
  const navigate = useNavigate();
  
  const { data, isLoading, error } = useTemplates();
  const createTemplateMutation = useCreateTemplate();
  const deleteTemplateMutation = useDeleteTemplate();
  
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [tipiDocumento, setTipiDocumento] = useState<DocumentiTipo[]>([]);
  const [loadingTipi, setLoadingTipi] = useState(false);
  const [selectedTipo, setSelectedTipo] = useState<DocumentiTipo | null>(null);
  
  const [formData, setFormData] = useState<CreateTemplateRequest>({
    tipo_documento: 0,
    nome: '',
    descrizione: '',
    numero_pagine: 1,
    attivo: true,
    priorita: 0,
  });

  // Carica tipi documento quando si apre il dialog
  useEffect(() => {
    if (createDialogOpen) {
      loadTipiDocumento();
    }
  }, [createDialogOpen]);

  const loadTipiDocumento = async () => {
    setLoadingTipi(true);
    try {
      const tipi = await documentiApi.listTipi();
      setTipiDocumento(tipi);
    } catch (error) {
      toast.error('Errore caricamento tipi documento');
    } finally {
      setLoadingTipi(false);
    }
  };

  const handleCloseDialog = () => {
    setCreateDialogOpen(false);
    setSelectedTipo(null);
  };

  const handleCreate = async () => {
    if (!formData.tipo_documento || !formData.nome) {
      toast.error('Tipo documento e nome sono obbligatori');
      return;
    }

    try {
      const newTemplate = await createTemplateMutation.mutateAsync(formData);
      toast.success('Template creato con successo');
      setCreateDialogOpen(false);
      setSelectedTipo(null);
      setFormData({
        tipo_documento: 0,
        nome: '',
        descrizione: '',
        numero_pagine: 1,
        attivo: true,
        priorita: 0,
      });
      
      // Naviga all'editor del template
      navigate(`/admin/templates/${newTemplate.id}`);
    } catch (error: any) {
      toast.error(`Errore creazione template: ${error.message}`);
    }
  };

  const handleDelete = async (id: number, nome: string) => {
    if (!confirm(`Eliminare il template "${nome}"?`)) return;

    try {
      await deleteTemplateMutation.mutateAsync(id);
      toast.success('Template eliminato');
    } catch (error: any) {
      toast.error(`Errore eliminazione: ${error.message}`);
    }
  };

  if (isLoading) {
    return (
      <Container maxWidth="xl">
        <Box py={4}>
          <Typography>Caricamento...</Typography>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl">
        <Box py={4}>
          <Alert severity="error">
            Errore caricamento template: {(error as Error).message}
          </Alert>
        </Box>
      </Container>
    );
  }

  const templates = data?.results || [];

  return (
    <Container maxWidth="xl">
      <Box py={4}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Template di Estrazione AI
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Gestisci template per estrazione automatica dati da documenti
            </Typography>
          </Box>
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Nuovo Template
          </Button>
        </Box>

        {/* Lista Template */}
        {templates.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Nessun template configurato
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Crea il primo template per iniziare l'estrazione automatica
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Crea Template
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {templates.map((template) => (
              <Grid size={{ xs: 12, md: 6, lg: 4 }} key={template.id}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                      <Typography variant="h6" component="div">
                        {template.nome}
                      </Typography>
                      <Chip
                        label={template.attivo ? 'Attivo' : 'Inattivo'}
                        color={template.attivo ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {template.tipo_documento_codice} - {template.tipo_documento_descrizione}
                    </Typography>

                    {template.descrizione && (
                      <Typography variant="body2" color="text.secondary" mt={1}>
                        {template.descrizione}
                      </Typography>
                    )}

                    <Box display="flex" gap={1} mt={2} flexWrap="wrap">
                      <Chip
                        label={`${template.pagine?.length || 0} pagine`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`${template.pagine?.reduce((sum, p) => sum + (p.zone?.length || 0), 0) || 0} zone`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`Priorità: ${template.priorita}`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>

                    <Typography variant="caption" color="text.secondary" display="block" mt={2}>
                      Creato: {new Date(template.creato_il).toLocaleDateString('it-IT')}
                      {template.creato_da_username && ` da ${template.creato_da_username}`}
                    </Typography>
                  </CardContent>

                  <CardActions>
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                      onClick={() => navigate(`/admin/templates/${template.id}`)}
                    >
                      Visualizza
                    </Button>
                    <Button
                      size="small"
                      startIcon={<EditIcon />}
                      onClick={() => navigate(`/admin/templates/${template.id}/edit`)}
                    >
                      Modifica
                    </Button>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(template.id, template.nome)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      {/* Dialog Creazione Template */}
      <Dialog
        open={createDialogOpen}
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Crea Nuovo Template</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <Autocomplete
              options={tipiDocumento}
              getOptionLabel={(option) => `${option.codice} - ${option.nome}`}
              value={selectedTipo}
              onChange={(_, newValue) => {
                setSelectedTipo(newValue);
                setFormData({ ...formData, tipo_documento: newValue?.id || 0 });
              }}
              loading={loadingTipi}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Tipo Documento *"
                  required
                  helperText="Seleziona il tipo di documento per questo template"
                />
              )}
              renderOption={(props, option) => (
                <li {...props} key={option.id}>
                  <Box>
                    <Typography variant="body1">
                      <strong>{option.codice}</strong> - {option.nome}
                    </Typography>
                    {option.estensioni_permesse && (
                      <Typography variant="caption" color="text.secondary">
                        Estensioni: {option.estensioni_permesse}
                      </Typography>
                    )}
                  </Box>
                </li>
              )}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              noOptionsText="Nessun tipo documento trovato"
              fullWidth
            />
            
            <TextField
              label="Nome Template"
              value={formData.nome}
              onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
              required
              fullWidth
              placeholder="es. UNILAV Standard 2026"
            />
            
            <TextField
              label="Descrizione"
              value={formData.descrizione}
              onChange={(e) => setFormData({ ...formData, descrizione: e.target.value })}
              multiline
              rows={3}
              fullWidth
              placeholder="Descrizione dettagliata del template..."
            />
            
            <TextField
              label="Numero Pagine"
              type="number"
              value={formData.numero_pagine}
              onChange={(e) =>
                setFormData({ ...formData, numero_pagine: parseInt(e.target.value) })
              }
              fullWidth
              inputProps={{ min: 1, max: 10 }}
            />
            
            <TextField
              label="Priorità"
              type="number"
              value={formData.priorita}
              onChange={(e) =>
                setFormData({ ...formData, priorita: parseInt(e.target.value) })
              }
              fullWidth
              helperText="Maggiore = più priorità (0-100)"
              inputProps={{ min: 0, max: 100 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={formData.attivo}
                  onChange={(e) => setFormData({ ...formData, attivo: e.target.checked })}
                />
              }
              label="Template Attivo"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Annulla</Button>
          <Button
            onClick={handleCreate}
            variant="contained"
            disabled={createTemplateMutation.isPending}
          >
            {createTemplateMutation.isPending ? 'Creazione...' : 'Crea'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
