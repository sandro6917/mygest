/**
 * Dashboard AI Classifier con statistiche e overview
 */
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  FolderOpen as FolderIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Description as DocIcon,
  SmartToy as AiIcon,
} from '@mui/icons-material';
import { useJobStats } from '@/hooks/useAiClassifier';

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color?: 'primary' | 'success' | 'error' | 'warning' | 'info';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color = 'primary' }) => {
  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value.toLocaleString()}
            </Typography>
          </Box>
          <Box
            sx={{
              backgroundColor: `${color}.light`,
              borderRadius: '50%',
              p: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export const AiClassifierDashboard: React.FC = () => {
  const { data: stats, isLoading } = useJobStats();

  if (isLoading) {
    return <LinearProgress />;
  }

  if (!stats) {
    return null;
  }

  const successRate =
    stats.total_jobs > 0
      ? ((stats.completed_jobs / stats.total_jobs) * 100).toFixed(1)
      : '0';

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          <AiIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          AI Document Classifier
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Sistema di classificazione automatica documenti con intelligenza artificiale
        </Typography>
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(4, 1fr)',
          },
          gap: 3,
        }}
      >
        {/* Totale Job */}
        <StatCard
          title="Totale Job"
          value={stats.total_jobs}
          icon={<FolderIcon fontSize="large" />}
          color="primary"
        />

        {/* Job Completati */}
        <StatCard
          title="Completati"
          value={stats.completed_jobs}
          icon={<CheckIcon fontSize="large" />}
          color="success"
        />

        {/* Job Falliti */}
        <StatCard
          title="Falliti"
          value={stats.failed_jobs}
          icon={<ErrorIcon fontSize="large" />}
          color="error"
        />

        {/* File Processati */}
        <StatCard
          title="File Processati"
          value={stats.total_files_processed}
          icon={<DocIcon fontSize="large" />}
          color="info"
        />
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
          gap: 3,
          mt: 3,
        }}
      >
        {/* Success Rate Card */}
        <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tasso di Successo
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="h3" color="success.main">
                  {successRate}%
                </Typography>
                <Box flex={1}>
                  <LinearProgress
                    variant="determinate"
                    value={parseFloat(successRate)}
                    color="success"
                    sx={{ height: 10, borderRadius: 1 }}
                  />
                </Box>
              </Box>
              <Box mt={2} display="flex" gap={1}>
                <Chip
                  label={`${stats.completed_jobs} Completati`}
                  color="success"
                  size="small"
                />
                <Chip
                  label={`${stats.failed_jobs} Falliti`}
                  color="error"
                  size="small"
                />
                <Chip
                  label={`${stats.pending_jobs + stats.running_jobs} In corso`}
                  color="warning"
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>

        {/* Documenti Importati Card */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Documenti Importati
            </Typography>
            <Box display="flex" alignItems="baseline" gap={1}>
              <Typography variant="h3" color="primary.main">
                {stats.total_documents_imported}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                documenti creati nell'archivio
              </Typography>
            </Box>
            <Box mt={2}>
              <Typography variant="body2" color="text.secondary">
                Media: {stats.total_jobs > 0 
                  ? (stats.total_documents_imported / stats.total_jobs).toFixed(1)
                  : '0'} documenti per job
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};
