/**
 * Dialog per creare un nuovo job di classificazione
 */
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControlLabel,
  Switch,
  Box,
  Alert,
  Typography,
} from '@mui/material';
import { FolderOpen as FolderIcon } from '@mui/icons-material';
import { useCreateJob } from '@/hooks/useAiClassifier';
import type { CreateJobRequest } from '@/types/aiClassifier';
import { DirectoryPicker } from './DirectoryPicker';

interface CreateJobDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (jobId: number) => void;
}

export const CreateJobDialog: React.FC<CreateJobDialogProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<CreateJobRequest>({
    directory_path: '',
    use_llm: true,
    recursive: false,
  });

  const createJobMutation = useCreateJob();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await createJobMutation.mutateAsync(formData);
      if (onSuccess) {
        onSuccess(result.id);
      }
      handleClose();
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleClose = () => {
    setFormData({
      directory_path: '',
      use_llm: true,
      recursive: false,
    });
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <FolderIcon />
            Nuovo Job di Classificazione
          </Box>
        </DialogTitle>

        <DialogContent>
          <Box display="flex" flexDirection="column" gap={3} pt={1}>
            <Alert severity="info">
              Il sistema scannerizzerà la directory specificata e classificherà
              automaticamente tutti i documenti trovati.
            </Alert>

            <DirectoryPicker
              value={formData.directory_path}
              onChange={(value) =>
                setFormData({ ...formData, directory_path: value })
              }
              label="Percorso Directory"
              required
            />

            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.use_llm}
                    onChange={(e) =>
                      setFormData({ ...formData, use_llm: e.target.checked })
                    }
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">
                      Usa AI (GPT-4o-mini)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Classificazione più accurata con intelligenza artificiale
                    </Typography>
                  </Box>
                }
              />
            </Box>

            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.recursive}
                    onChange={(e) =>
                      setFormData({ ...formData, recursive: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Scansione Ricorsiva</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Include sottocartelle nella scansione
                    </Typography>
                  </Box>
                }
              />
            </Box>

            {formData.use_llm && (
              <Alert severity="warning">
                <strong>Nota costi:</strong> L'uso di GPT-4o-mini ha un costo
                di ~$0.15 per 1M token. Stimato: ~$0.001 per documento.
              </Alert>
            )}
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={createJobMutation.isPending}>
            Annulla
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={
              createJobMutation.isPending || !formData.directory_path.trim()
            }
          >
            {createJobMutation.isPending ? 'Creazione...' : 'Crea Job'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
