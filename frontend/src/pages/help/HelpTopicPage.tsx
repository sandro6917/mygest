import React, { ReactNode } from 'react';
import {
  Container,
  Typography,
  Box,
  Breadcrumbs,
  Link as MuiLink,
  Button,
  Paper,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { Link } from 'react-router-dom';

interface HelpTopicPageProps {
  title: string;
  summary: string;
  children: ReactNode;
}

export const HelpTopicPage: React.FC<HelpTopicPageProps> = ({ title, summary, children }) => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <MuiLink component={Link} to="/" underline="hover" color="inherit">
          Home
        </MuiLink>
        <MuiLink component={Link} to="/help" underline="hover" color="inherit">
          Centro Assistenza
        </MuiLink>
        <Typography color="text.primary">{title}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4" component="h1" fontWeight={600} gutterBottom>
            {title}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {summary}
          </Typography>
        </Box>
        <Button
          component={Link}
          to="/help"
          startIcon={<ArrowBackIcon />}
          variant="outlined"
        >
          Indice Help
        </Button>
      </Box>

      {/* Content */}
      <Paper sx={{ p: 4 }}>
        {children}
      </Paper>
    </Container>
  );
};
