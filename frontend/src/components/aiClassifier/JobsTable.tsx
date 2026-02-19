/**
 * Tabella lista job di classificazione
 */
import React from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Typography,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  SmartToy as AiIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useJobs, useStartJob, useDeleteJob } from '@/hooks/useAiClassifier';
import type { ClassificationJob, JobStatus } from '@/types/aiClassifier';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

const getStatusColor = (status: JobStatus) => {
  switch (status) {
    case 'pending':
      return 'warning';
    case 'running':
      return 'info';
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

const formatDate = (dateString: string | null) => {
  if (!dateString) return '-';
  return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: it });
};

export const JobsTable: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading } = useJobs();
  const startJobMutation = useStartJob();
  const deleteJobMutation = useDeleteJob();

  const handleStartJob = async (id: number) => {
    await startJobMutation.mutateAsync(id);
  };

  const handleDeleteJob = async (id: number) => {
    if (window.confirm('Sei sicuro di voler eliminare questo job?')) {
      await deleteJobMutation.mutateAsync(id);
    }
  };

  const handleViewJob = (id: number) => {
    navigate(`/ai-classifier/jobs/${id}`);
  };

  if (isLoading) {
    return <LinearProgress />;
  }

  if (!data || data.results.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          Nessun job trovato
        </Typography>
        <Typography variant="body2" color="text.secondary" mt={1}>
          Crea il tuo primo job di classificazione
        </Typography>
      </Paper>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>Directory</TableCell>
            <TableCell align="center">Stato</TableCell>
            <TableCell align="center">AI</TableCell>
            <TableCell align="right">File</TableCell>
            <TableCell align="right">Processati</TableCell>
            <TableCell align="right">Successi</TableCell>
            <TableCell align="center">Progresso</TableCell>
            <TableCell>Creato</TableCell>
            <TableCell>Utente</TableCell>
            <TableCell align="center">Azioni</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.results.map((job: ClassificationJob) => (
            <TableRow
              key={job.id}
              hover
              sx={{ cursor: 'pointer' }}
              onClick={() => handleViewJob(job.id)}
            >
              <TableCell>
                <Typography variant="body2" fontWeight="bold">
                  #{job.id}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2" noWrap maxWidth={300}>
                  {job.directory_path}
                </Typography>
              </TableCell>

              <TableCell align="center">
                <Chip
                  label={job.status_display}
                  color={getStatusColor(job.status)}
                  size="small"
                />
              </TableCell>

              <TableCell align="center">
                {job.use_llm && (
                  <Tooltip title={`AI: ${job.llm_provider}`}>
                    <AiIcon color="primary" fontSize="small" />
                  </Tooltip>
                )}
              </TableCell>

              <TableCell align="right">
                <Typography variant="body2">{job.total_files}</Typography>
              </TableCell>

              <TableCell align="right">
                <Typography variant="body2">{job.processed_files}</Typography>
              </TableCell>

              <TableCell align="right">
                <Typography variant="body2" color="success.main">
                  {job.successful_files}
                </Typography>
              </TableCell>

              <TableCell align="center">
                <Box sx={{ minWidth: 100 }}>
                  <LinearProgress
                    variant="determinate"
                    value={job.progress_percentage}
                    color={job.status === 'failed' ? 'error' : 'primary'}
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {job.progress_percentage.toFixed(0)}%
                  </Typography>
                </Box>
              </TableCell>

              <TableCell>
                <Typography variant="body2">
                  {formatDate(job.created_at)}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2">
                  {job.created_by_username}
                </Typography>
              </TableCell>

              <TableCell align="center" onClick={(e) => e.stopPropagation()}>
                <Box display="flex" gap={0.5}>
                  {job.status === 'pending' && (
                    <Tooltip title="Avvia job">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleStartJob(job.id)}
                        disabled={startJobMutation.isPending}
                      >
                        <PlayIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}

                  <Tooltip title="Visualizza dettagli">
                    <IconButton
                      size="small"
                      color="info"
                      onClick={() => handleViewJob(job.id)}
                    >
                      <ViewIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>

                  {job.status === 'pending' && (
                    <Tooltip title="Elimina job">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteJob(job.id)}
                        disabled={deleteJobMutation.isPending}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
