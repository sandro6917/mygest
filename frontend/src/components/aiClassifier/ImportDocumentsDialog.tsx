/**
 * Dialog per importare documenti classificati
 */
import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Alert,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Upload as ImportIcon,
  CheckCircle as CheckIcon,
  Description as DocIcon,
} from '@mui/icons-material';
import { useImportDocuments } from '@/hooks/useAiClassifier';

interface ImportDocumentsDialogProps {
  open: boolean;
  onClose: () => void;
  selectedResultIds: number[];
  onSuccess?: () => void;
}

export const ImportDocumentsDialog: React.FC<ImportDocumentsDialogProps> = ({
  open,
  onClose,
  selectedResultIds,
  onSuccess,
}) => {
  const importMutation = useImportDocuments();

  const handleImport = async () => {
    try {
      await importMutation.mutateAsync({
        result_ids: selectedResultIds,
      });
      
      if (onSuccess) {
        onSuccess();
      }
      onClose();
    } catch (error) {
      // Error handled by mutation
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <ImportIcon />
          Importa Documenti Classificati
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box display="flex" flexDirection="column" gap={2}>
          <Alert severity="info">
            {selectedResultIds.length} {selectedResultIds.length === 1 ? 'documento' : 'documenti'} {selectedResultIds.length === 1 ? 'sarà importato' : 'saranno importati'} nell'archivio documentale.
          </Alert>

          <Typography variant="body2" color="text.secondary">
            L'importazione eseguirà le seguenti operazioni:
          </Typography>

          <List dense>
            <ListItem>
              <ListItemIcon>
                <CheckIcon color="success" fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary="Creazione record Documento"
                secondary="Verrà creato un nuovo documento per ogni file"
              />
            </ListItem>

            <ListItem>
              <ListItemIcon>
                <DocIcon color="primary" fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary="Copia file nel NAS"
                secondary="I file verranno copiati nel percorso di archiviazione"
              />
            </ListItem>

            <ListItem>
              <ListItemIcon>
                <CheckIcon color="success" fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary="Assegnazione tipo e metadata"
                secondary="Tipo, cliente, e metadata estratti dall'AI"
              />
            </ListItem>

            <ListItem>
              <ListItemIcon>
                <CheckIcon color="success" fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary="Codice documento automatico"
                secondary="Generazione codice secondo pattern CLI-TIT-ANNO-SEQ"
              />
            </ListItem>
          </List>

          <Alert severity="warning">
            <strong>Nota:</strong> I file sorgente non verranno eliminati dalla
            directory originale.
          </Alert>

          {importMutation.isError && (
            <Alert severity="error">
              Errore durante l'importazione. Riprova o contatta l'assistenza.
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={importMutation.isPending}>
          Annulla
        </Button>
        <Button
          onClick={handleImport}
          variant="contained"
          color="primary"
          disabled={importMutation.isPending || selectedResultIds.length === 0}
          startIcon={<ImportIcon />}
        >
          {importMutation.isPending
            ? 'Importazione...'
            : `Importa ${selectedResultIds.length} ${selectedResultIds.length === 1 ? 'Documento' : 'Documenti'}`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
