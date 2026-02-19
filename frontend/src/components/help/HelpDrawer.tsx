import React from 'react';
import {
  Drawer,
  Box,
  Typography,
  Divider,
  Button,
  IconButton,
  Stack,
  Chip,
  Alert,
} from '@mui/material';
import {
  Close as CloseIcon,
  OpenInNew as OpenIcon,
  Description as DocumentIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import type { DocumentiTipo } from '@/types/documento';

interface HelpDrawerProps {
  open: boolean;
  onClose: () => void;
  tipo: DocumentiTipo | null;
}

export const HelpDrawer: React.FC<HelpDrawerProps> = ({ open, onClose, tipo }) => {
  const navigate = useNavigate();

  if (!tipo) return null;

  const handleOpenFullGuide = () => {
    navigate(`/help/documenti/${tipo.codice}`);
    onClose();
  };

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 450, p: 3 }}>
        {/* Header */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <DocumentIcon color="primary" />
            <Typography variant="h6">
              {tipo.nome}
            </Typography>
          </Stack>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>

        <Divider sx={{ mb: 3 }} />

        {/* Descrizione */}
        <Box mb={3}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Descrizione
          </Typography>
          <Typography variant="body2">
            {tipo.help_data?.descrizione_breve || 'Nessuna descrizione disponibile'}
          </Typography>
        </Box>

        {/* Quando usare */}
        {tipo.help_data?.quando_usare && (
          <Box mb={3}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Quando usare
            </Typography>
            <Stack spacing={0.5}>
              {tipo.help_data.quando_usare.casi_uso.slice(0, 3).map((caso, index) => (
                <Typography key={index} variant="body2" sx={{ pl: 2 }}>
                  • {caso}
                </Typography>
              ))}
            </Stack>
          </Box>
        )}

        {/* Campi obbligatori */}
        {tipo.help_data?.campi_obbligatori && (
          <Box mb={3}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Campi richiesti
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
              {tipo.help_data.campi_obbligatori.sempre.map((campo) => (
                <Chip key={campo} label={campo} size="small" variant="outlined" />
              ))}
            </Stack>
          </Box>
        )}

        {/* Note speciali */}
        {tipo.help_data?.note_speciali?.attenzioni && tipo.help_data.note_speciali.attenzioni.length > 0 && (
          <Box mb={3}>
            <Alert severity="warning" sx={{ fontSize: '0.875rem' }}>
              {tipo.help_data.note_speciali.attenzioni[0]}
            </Alert>
          </Box>
        )}

        {/* Suggerimenti */}
        {tipo.help_data?.note_speciali?.suggerimenti && tipo.help_data.note_speciali.suggerimenti.length > 0 && (
          <Box mb={3}>
            <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
              {tipo.help_data.note_speciali.suggerimenti[0]}
            </Alert>
          </Box>
        )}

        {/* Actions */}
        <Stack spacing={2}>
          <Button
            variant="outlined"
            fullWidth
            startIcon={<OpenIcon />}
            onClick={handleOpenFullGuide}
          >
            Apri Guida Completa
          </Button>
          <Button
            variant="contained"
            fullWidth
            onClick={() => {
              navigate(`/documenti/nuovo?tipo=${tipo.codice}`);
              onClose();
            }}
          >
            Crea Nuovo Documento
          </Button>
        </Stack>
      </Box>
    </Drawer>
  );
};
