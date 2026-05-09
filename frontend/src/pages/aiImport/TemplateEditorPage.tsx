/**
 * Pagina Editor Template di Estrazione
 */
import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  Divider,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'react-toastify';

import {
  useTemplate,
  useAddTemplatePage,
  useAddTemplateZone,
  useDeleteTemplateZone,
  useAvailableFields,
  useAvailableTransformations,
  useAddFieldMapping,
  useDeleteFieldMapping,
} from '@/hooks/useAIImport';
import { ZoneDrawingCanvas } from '@/components/aiImport/ZoneDrawingCanvas';
import type {
  ExtractionTemplateZone,
  CreateTemplatePageRequest,
  CreateTemplateZoneRequest,
} from '@/types/aiImport';

export const TemplateEditorPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const templateId = parseInt(id || '0');

  const { data: template, isLoading, error, refetch } = useTemplate(templateId);
  const addPageMutation = useAddTemplatePage();
  const addZoneMutation = useAddTemplateZone();
  const deleteZoneMutation = useDeleteTemplateZone();
  const addMappingMutation = useAddFieldMapping();
  const deleteMappingMutation = useDeleteFieldMapping();

  const [selectedPageIndex, setSelectedPageIndex] = useState(0);
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadPageNumber, setUploadPageNumber] = useState(1);
  
  // Field Mapping state
  const [mappingDialogOpen, setMappingDialogOpen] = useState(false);
  const [selectedMappingZone, setSelectedMappingZone] = useState<number | null>(null);
  const [selectedDocumentField, setSelectedDocumentField] = useState<string | null>(null);
  const [selectedTransformation, setSelectedTransformation] = useState<string | null>(null);
  
  // Load available fields for this template's document type
  const { data: availableFieldsData } = useAvailableFields(template?.tipo_documento_id);
  const { data: transformationsData } = useAvailableTransformations();

  // Debug log
  useEffect(() => {
    console.log('🔍 Available Fields Data:', availableFieldsData);
    console.log('📋 Template tipo_documento_id:', template?.tipo_documento_id);
  }, [availableFieldsData, template?.tipo_documento_id]);

  // Reset selectedPageIndex se fuori range
  useEffect(() => {
    if (template?.pagine) {
      const maxIndex = template.pagine.length - 1;
      if (selectedPageIndex > maxIndex) {
        setSelectedPageIndex(Math.max(0, maxIndex));
      }
    }
  }, [template?.pagine, selectedPageIndex]);

  if (isLoading) {
    return (
      <Container maxWidth="xl">
        <Box py={4} display="flex" justifyContent="center">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error || !template) {
    return (
      <Container maxWidth="xl">
        <Box py={4}>
          <Alert severity="error">
            Template non trovato o errore caricamento
          </Alert>
          <Button startIcon={<BackIcon />} onClick={() => navigate('/admin/templates')} sx={{ mt: 2 }}>
            Torna alla Lista
          </Button>
        </Box>
      </Container>
    );
  }

  const currentPage = template.pagine?.[selectedPageIndex];
  const currentZones = currentPage?.zone || [];
  
  // DEBUG: Log template data
  console.log('🔍 Template Editor Debug:', {
    templateId,
    totalPages: template.pagine?.length || 0,
    selectedPageIndex,
    currentPage: currentPage ? {
      id: currentPage.id,
      numero_pagina: currentPage.numero_pagina,
      immagine_url: currentPage.immagine_url,
      larghezza: currentPage.larghezza,
      altezza: currentPage.altezza,
    } : null,
  });

  const handleUploadPage = async () => {
    if (!uploadFile) {
      toast.error('Seleziona un file');
      return;
    }

    try {
      // Leggi dimensioni immagine
      const img = new Image();
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        img.src = e.target?.result as string;
        img.onload = async () => {
          const pageData: CreateTemplatePageRequest = {
            template_id: templateId,
            numero_pagina: uploadPageNumber,
            immagine: uploadFile,
            larghezza: img.width,
            altezza: img.height,
          };

          await addPageMutation.mutateAsync({ templateId, data: pageData });
          toast.success('Pagina aggiunta al template');
          
          // Ricarica template per mostrare nuova pagina
          const result = await refetch();
          
          // Seleziona la nuova pagina (ultima nell'array - indice length-1)
          if (result.data?.pagine && result.data.pagine.length > 0) {
            setSelectedPageIndex(result.data.pagine.length - 1);
          }
          
          setUploadDialogOpen(false);
          setUploadFile(null);
          setUploadPageNumber(1);
        };
      };
      
      reader.readAsDataURL(uploadFile);
    } catch (error: any) {
      toast.error(`Errore upload pagina: ${error.message}`);
    }
  };

  const handleZoneCreate = async (zoneData: Omit<ExtractionTemplateZone, 'id' | 'absolute_coordinates'>) => {
    if (!currentPage) {
      toast.error('Nessuna pagina selezionata');
      return;
    }

    try {
      const request: CreateTemplateZoneRequest = {
        pagina_id: currentPage.id,
        ...zoneData,
      };

      await addZoneMutation.mutateAsync(request);
      toast.success('Zona aggiunta');
    } catch (error: any) {
      toast.error(`Errore creazione zona: ${error.message}`);
    }
  };

  const handleZoneDelete = async (zoneId: number) => {
    if (!confirm('Eliminare questa zona?')) return;

    try {
      await deleteZoneMutation.mutateAsync(zoneId);
      toast.success('Zona eliminata');
      setSelectedZoneId(null);
    } catch (error: any) {
      toast.error(`Errore eliminazione zona: ${error.message}`);
    }
  };

  const handleCreateMapping = async () => {
    if (!selectedMappingZone || !selectedDocumentField) {
      toast.error('Seleziona una zona e un campo documento');
      return;
    }

    // Trova la zona selezionata per ottenere il nome_campo
    const allZones = template?.pagine?.flatMap(p => p.zone || []) || [];
    const zone = allZones.find(z => z.id === selectedMappingZone);
    
    if (!zone) {
      toast.error('Zona non trovata');
      return;
    }

    // Determina il tipo di campo (field, attribute, note, metadata)
    let tipo_campo: 'field' | 'attribute' | 'note' | 'metadata' = 'field';
    if (selectedDocumentField.startsWith('attributi.')) {
      tipo_campo = 'attribute';
    } else if (selectedDocumentField === 'note') {
      tipo_campo = 'note';
    }

    try {
      await addMappingMutation.mutateAsync({
        template_id: templateId,
        nome_campo_template: zone.nome_campo,
        tipo_campo_destinazione: tipo_campo,
        nome_campo_destinazione: selectedDocumentField,
        funzione_trasformazione: selectedTransformation || undefined,
      });
      
      toast.success('Mapping creato');
      setMappingDialogOpen(false);
      setSelectedMappingZone(null);
      setSelectedDocumentField(null);
      setSelectedTransformation(null);
    } catch (error: any) {
      toast.error(`Errore creazione mapping: ${error.message}`);
    }
  };

  const handleDeleteMapping = async (mappingId: number) => {
    if (!confirm('Eliminare questo mapping?')) return;

    try {
      await deleteMappingMutation.mutateAsync(mappingId);
      toast.success('Mapping eliminato');
    } catch (error: any) {
      toast.error(`Errore eliminazione mapping: ${error.message}`);
    }
  };

  const selectedZone = currentZones.find((z) => z.id === selectedZoneId);

  return (
    <Container maxWidth="xl">
      <Box py={4}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Box>
            <Button
              startIcon={<BackIcon />}
              onClick={() => navigate('/admin/templates')}
              sx={{ mb: 2 }}
            >
              Torna alla Lista
            </Button>
            <Typography variant="h4" gutterBottom>
              {template.nome}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {template.tipo_documento_codice} - {template.tipo_documento_descrizione}
            </Typography>
          </Box>

          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
          >
            Carica Pagina
          </Button>
        </Box>

        {/* Content */}
        <Grid container spacing={3}>
          {/* Canvas Area */}
          <Grid size={{ xs: 12, lg: 8 }}>
            {template.pagine && template.pagine.length > 0 ? (
              <>
                {/* Tabs Pagine */}
                {template.pagine.length > 1 && (
                  <Paper sx={{ mb: 2 }}>
                    <Tabs
                      value={selectedPageIndex}
                      onChange={(_, newValue) => {
                        setSelectedPageIndex(newValue);
                        setSelectedZoneId(null);
                      }}
                    >
                      {template.pagine.map((page, index) => (
                        <Tab
                          key={page.id}
                          label={`Pagina ${page.numero_pagina}`}
                          value={index}
                        />
                      ))}
                    </Tabs>
                  </Paper>
                )}

                {/* Canvas */}
                {currentPage && (
                  <ZoneDrawingCanvas
                    imageUrl={currentPage.immagine_url}
                    imageWidth={currentPage.larghezza}
                    imageHeight={currentPage.altezza}
                    zones={currentZones}
                    selectedZoneId={selectedZoneId || undefined}
                    onZoneCreate={handleZoneCreate}
                    onZoneSelect={setSelectedZoneId}
                    onZoneDelete={handleZoneDelete}
                  />
                )}
              </>
            ) : (
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Nessuna pagina caricata
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={3}>
                  Carica un'immagine template per iniziare a definire le zone di estrazione
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<UploadIcon />}
                  onClick={() => setUploadDialogOpen(true)}
                >
                  Carica Prima Pagina
                </Button>
              </Paper>
            )}
          </Grid>

          {/* Sidebar */}
          <Grid size={{ xs: 12, lg: 4 }}>
            {/* Info Template */}
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Info Template
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Chip label={template.attivo ? 'Attivo' : 'Inattivo'} color={template.attivo ? 'success' : 'default'} />
                <Typography variant="body2">
                  <strong>Priorità:</strong> {template.priorita}
                </Typography>
                <Typography variant="body2">
                  <strong>Pagine:</strong> {template.pagine?.length || 0}
                </Typography>
                <Typography variant="body2">
                  <strong>Zone Totali:</strong>{' '}
                  {template.pagine?.reduce((sum, p) => sum + (p.zone?.length || 0), 0) || 0}
                </Typography>
              </Box>
            </Paper>

            {/* Lista Zone Pagina Corrente */}
            {currentPage && (
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Zone Pagina {currentPage.numero_pagina}
                </Typography>
                {currentZones.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    Nessuna zona definita. Disegna una zona sul canvas.
                  </Typography>
                ) : (
                  <List dense>
                    {currentZones.map((zone) => (
                      <ListItem
                        key={zone.id}
                        onClick={() => setSelectedZoneId(zone.id)}
                        sx={{
                          cursor: 'pointer',
                          bgcolor: zone.id === selectedZoneId ? 'action.selected' : 'transparent',
                        }}
                      >
                        <ListItemText
                          primary={zone.etichetta}
                          secondary={
                            <>
                              <Typography variant="caption" display="block">
                                Campo: {zone.nome_campo}
                              </Typography>
                              <Typography variant="caption" display="block">
                                Tipo: {zone.tipo_dato}
                                {zone.obbligatorio && ' • Obbligatorio'}
                              </Typography>
                            </>
                          }
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            edge="end"
                            size="small"
                            color="error"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleZoneDelete(zone.id);
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                )}
              </Paper>
            )}

            {/* Dettagli Zona Selezionata */}
            {selectedZone && (
              <Paper sx={{ p: 2, mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Dettagli Zona
                </Typography>
                <Box display="flex" flexDirection="column" gap={1}>
                  <Typography variant="body2">
                    <strong>Campo:</strong> {selectedZone.nome_campo}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Etichetta:</strong> {selectedZone.etichetta}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Tipo Dato:</strong> {selectedZone.tipo_dato}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Obbligatorio:</strong> {selectedZone.obbligatorio ? 'Sì' : 'No'}
                  </Typography>
                  {selectedZone.pattern_validazione && (
                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                      <strong>Pattern:</strong> {selectedZone.pattern_validazione}
                    </Typography>
                  )}
                  <Typography variant="body2">
                    <strong>Coordinate:</strong>
                  </Typography>
                  <Typography variant="caption" component="div">
                    X: {Number(selectedZone.x_percent).toFixed(2)}%, Y: {Number(selectedZone.y_percent).toFixed(2)}%
                    <br />
                    W: {Number(selectedZone.width_percent).toFixed(2)}%, H: {Number(selectedZone.height_percent).toFixed(2)}%
                  </Typography>
                </Box>
              </Paper>
            )}

            {/* Field Mapping */}
            <Paper sx={{ p: 2, mt: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Field Mapping</Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => setMappingDialogOpen(true)}
                  variant="outlined"
                >
                  Nuovo
                </Button>
              </Box>
              
              <Divider sx={{ mb: 2 }} />
              
              {!template?.mapping_campi || template.mapping_campi.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Nessun mapping definito. Associa le zone ai campi del documento.
                </Typography>
              ) : (
                <List dense>
                  {template.mapping_campi.map((mapping) => (
                    <ListItem key={mapping.id}>
                      <ListItemText
                        primary={
                          <Typography variant="body2">
                            <strong>{mapping.nome_campo_template}</strong> →{' '}
                            {mapping.nome_campo_destinazione}
                            {mapping.funzione_trasformazione && (
                              <Chip 
                                label={`📐 ${mapping.funzione_trasformazione}`} 
                                size="small" 
                                sx={{ ml: 1 }}
                                variant="outlined"
                              />
                            )}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary">
                            Tipo: {mapping.tipo_campo_destinazione}
                            {mapping.funzione_trasformazione && (
                              <> • Trasformazione: {
                                transformationsData?.transformations.find(
                                  t => t.value === mapping.funzione_trasformazione
                                )?.label || mapping.funzione_trasformazione
                              }</>
                            )}
                          </Typography>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          size="small"
                          color="error"
                          onClick={() => handleDeleteMapping(mapping.id)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Dialog Upload Pagina */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Carica Pagina Template</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField
              label="Numero Pagina"
              type="number"
              value={uploadPageNumber}
              onChange={(e) => setUploadPageNumber(parseInt(e.target.value))}
              fullWidth
              inputProps={{ min: 1, max: 10 }}
            />

            <Button variant="outlined" component="label" fullWidth>
              {uploadFile ? uploadFile.name : 'Seleziona Immagine'}
              <input
                type="file"
                hidden
                accept="image/*"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              />
            </Button>

            {uploadFile && (
              <Alert severity="info">
                File selezionato: {uploadFile.name} ({(uploadFile.size / 1024).toFixed(2)} KB)
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Annulla</Button>
          <Button
            onClick={handleUploadPage}
            variant="contained"
            disabled={!uploadFile || addPageMutation.isPending}
          >
            {addPageMutation.isPending ? 'Upload...' : 'Carica'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog Nuovo Field Mapping */}
      <Dialog 
        open={mappingDialogOpen} 
        onClose={() => {
          setMappingDialogOpen(false);
          setSelectedMappingZone(null);
          setSelectedDocumentField(null);
        }} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Nuovo Field Mapping</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={3} mt={2}>
            {/* Select Zona */}
            <Autocomplete
              options={template?.pagine?.flatMap(p => p.zone || []) || []}
              getOptionLabel={(zone) => `${zone.etichetta} (${zone.nome_campo})`}
              value={
                template?.pagine
                  ?.flatMap(p => p.zone || [])
                  .find(z => z.id === selectedMappingZone) || null
              }
              onChange={(_, newValue) => setSelectedMappingZone(newValue?.id || null)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Zona Template"
                  placeholder="Seleziona una zona..."
                  required
                />
              )}
              isOptionEqualToValue={(option, value) => option.id === value.id}
            />

            {/* Autocomplete Campo Documento */}
            <Autocomplete
              options={availableFieldsData?.campi || []}
              getOptionLabel={(field) => field.label}
              groupBy={(field) => 
                field.value.startsWith('attributi.') ? 'Attributi Dinamici' : 'Campi Fissi'
              }
              value={
                availableFieldsData?.campi.find(f => f.value === selectedDocumentField) || null
              }
              onChange={(_, newValue) => setSelectedDocumentField(newValue?.value || null)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Campo Documento"
                  placeholder="Seleziona campo destinazione..."
                  required
                  helperText={
                    selectedDocumentField === '__note__'
                      ? '📝 Il valore verrà aggiunto alle Note del documento'
                      : 'Seleziona il campo del documento dove salvare il valore estratto'
                  }
                />
              )}
              renderOption={(props, option) => {
                const { key, ...otherProps } = props as any;
                return (
                  <li key={key} {...otherProps}>
                    <Box>
                      <Typography variant="body2">{option.label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {option.value} • {option.type}
                      </Typography>
                    </Box>
                  </li>
                );
              }}
              isOptionEqualToValue={(option, value) => option.value === value.value}
            />

            {/* Autocomplete Funzione Trasformazione (opzionale) */}
            <Autocomplete
              options={transformationsData?.transformations || []}
              getOptionLabel={(trans) => trans.label}
              groupBy={(trans) => trans.category}
              value={
                transformationsData?.transformations.find(t => t.value === selectedTransformation) || null
              }
              onChange={(_, newValue) => setSelectedTransformation(newValue?.value || null)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Funzione Trasformazione (opzionale)"
                  placeholder="Nessuna trasformazione..."
                  helperText="Applica normalizzazione/validazione al valore estratto"
                />
              )}
              renderOption={(props, option) => {
                const { key, ...otherProps } = props as any;
                return (
                  <li key={key} {...otherProps}>
                    <Box>
                      <Typography variant="body2">{option.label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {option.value}
                      </Typography>
                    </Box>
                  </li>
                );
              }}
              isOptionEqualToValue={(option, value) => option.value === value.value}
            />

            {selectedDocumentField && (
              <Alert severity="info" sx={{ mt: 1 }}>
                Il valore estratto dalla zona <strong>{
                  template?.pagine
                    ?.flatMap(p => p.zone || [])
                    .find(z => z.id === selectedMappingZone)?.nome_campo
                }</strong> sarà salvato in <strong>{selectedDocumentField}</strong>
                {selectedTransformation && (
                  <> dopo trasformazione: <strong>{
                    transformationsData?.transformations.find(t => t.value === selectedTransformation)?.label
                  }</strong></>
                )}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setMappingDialogOpen(false);
              setSelectedMappingZone(null);
              setSelectedDocumentField(null);
              setSelectedTransformation(null);
            }}
          >
            Annulla
          </Button>
          <Button
            onClick={handleCreateMapping}
            variant="contained"
            disabled={!selectedMappingZone || !selectedDocumentField || addMappingMutation.isPending}
          >
            {addMappingMutation.isPending ? 'Creazione...' : 'Crea Mapping'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
