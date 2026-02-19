/**
 * Pagina lista job di classificazione
 */
import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Container,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { AiClassifierDashboard } from '@/components/aiClassifier/AiClassifierDashboard';
import { JobsTable } from '@/components/aiClassifier/JobsTable';
import { CreateJobDialog } from '@/components/aiClassifier/CreateJobDialog';
import { useNavigate } from 'react-router-dom';

export const JobsListPage: React.FC = () => {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const navigate = useNavigate();

  const handleJobCreated = (jobId: number) => {
    // Naviga al dettaglio del job appena creato
    navigate(`/ai-classifier/jobs/${jobId}`);
  };

  return (
    <Container maxWidth="xl">
      <Box mb={4}>
        <AiClassifierDashboard />
      </Box>

      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography variant="h5">Job di Classificazione</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Nuovo Job
        </Button>
      </Box>

      <JobsTable />

      <CreateJobDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={handleJobCreated}
      />
    </Container>
  );
};
