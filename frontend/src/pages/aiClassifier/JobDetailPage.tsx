/**
 * Pagina dettaglio job con risultati di classificazione
 */
import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Container,
  Paper,
  Alert,
  Chip,
  LinearProgress,
  IconButton,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  PlayArrow as StartIcon,
  Upload as ImportIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useJob, useStartJob, useResults } from '@/hooks/useAiClassifier';
import { ResultsTable } from '@/components/aiClassifier/ResultsTable';
import { ImportDocumentsDialog } from '@/components/aiClassifier/ImportDocumentsDialog';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

const formatDate = (dateString: string | null) => {
  if (!dateString) return '-';
  return format(new Date(dateString), 'dd/MM/yyyy HH:mm:ss', { locale: it });
};

export const JobDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const jobId = id ? parseInt(id, 10) : 0;

  // Verifica ID valido
  if (!id || isNaN(jobId) || jobId === 0) {
    return (
      <Container maxWidth="xl">
        <Alert severity="error">ID Job non valido</Alert>
        <Button onClick={() => navigate('/ai-classifier/jobs')} sx={{ mt: 2 }}>
          Torna alla lista
        </Button>
      </Container>
    );
  }

  const { data: job, isLoading: jobLoading } = useJob(jobId);
  const { data: results, refetch: refetchResults } = useResults({ job: jobId });
  const startJobMutation = useStartJob();

  const [selectedResultIds, setSelectedResultIds] = useState<number[]>([]);
  const [importDialogOpen, setImportDialogOpen] = useState(false);

  const handleStartJob = async () => {
    await startJobMutation.mutateAsync(jobId);
  };

  const handleImportSelected = () => {
    if (selectedResultIds.length > 0) {
      setImportDialogOpen(true);
    }
  };

  const handleImportSuccess = () => {
    setSelectedResultIds([]);
    refetchResults();
  };

  if (jobLoading) {
    return (
      <Container maxWidth="xl">
        <LinearProgress />
      </Container>
    );
  }

  if (!job) {
    return (
      <Container maxWidth="xl">
        <Alert severity="error">Job non trovato</Alert>
      </Container>
    );
  }

  const canStartJob = job.status === 'pending';
  const canImport = job.status === 'completed' && results && results.count > 0;

  return (
    <Container maxWidth="xl">
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <IconButton onClick={() => navigate('/ai-classifier/jobs')}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4" flex={1}>
          Job #{job.id}
        </Typography>

        {canStartJob && (
          <Button
            variant="contained"
            startIcon={<StartIcon />}
            onClick={handleStartJob}
            disabled={startJobMutation.isPending}
          >
            Avvia Job
          </Button>
        )}

        {canImport && selectedResultIds.length > 0 && (
          <Button
            variant="contained"
            color="success"
            startIcon={<ImportIcon />}
            onClick={handleImportSelected}
          >
            Importa {selectedResultIds.length} Selezionati
          </Button>
        )}

        <IconButton onClick={() => refetchResults()}>
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* Job Info Card */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(3, 1fr)',
            },
            gap: 3,
          }}
        >
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Directory
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {job.directory_path}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Stato
            </Typography>
            <Chip label={job.status_display} color="primary" />
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Usa AI
            </Typography>
            <Typography variant="body1">
              {job.use_llm ? `Sì (${job.llm_provider})` : 'No (solo regole)'}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              File Totali
            </Typography>
            <Typography variant="h5" color="primary.main">
              {job.total_files}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Processati
            </Typography>
            <Typography variant="h5" color="info.main">
              {job.processed_files}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Successi
            </Typography>
            <Typography variant="h5" color="success.main">
              {job.successful_files}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Falliti
            </Typography>
            <Typography variant="h5" color="error.main">
              {job.failed_files}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Creato
            </Typography>
            <Typography variant="body1">
              {formatDate(job.created_at)}
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Utente
            </Typography>
            <Typography variant="body1">{job.created_by_username}</Typography>
          </Box>
        </Box>

        {/* Progress Bar */}
        {job.status === 'running' && (
          <Box mt={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Progresso
            </Typography>
            <LinearProgress
              variant="determinate"
              value={job.progress_percentage}
              sx={{ height: 12, borderRadius: 1 }}
            />
            <Typography variant="caption" color="text.secondary" mt={0.5}>
              {job.progress_percentage.toFixed(1)}% completato
            </Typography>
          </Box>
        )}

        {/* Errors */}
        {job.errors && job.errors.length > 0 && (
          <Box mt={3}>
            <Alert severity="error">
              <Typography variant="body2" fontWeight="bold" gutterBottom>
                Errori ({job.errors.length})
              </Typography>
              {job.errors.map((error, index) => (
                <Typography key={index} variant="body2">
                  • {error}
                </Typography>
              ))}
            </Alert>
          </Box>
        )}
      </Paper>

      {/* Results Table */}
      <Box mb={3}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h5">
            Risultati Classificazione
            {results && ` (${results.count})`}
          </Typography>
        </Box>

        <ResultsTable
          jobId={jobId}
          selectable={canImport}
          onSelectionChange={setSelectedResultIds}
        />
      </Box>

      {/* Import Dialog */}
      <ImportDocumentsDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        selectedResultIds={selectedResultIds}
        onSuccess={handleImportSuccess}
      />
    </Container>
  );
};
