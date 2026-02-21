import React, { useState, useMemo } from 'react';
import {
  Container,
  Typography,
  Grid,
  TextField,
  InputAdornment,
  Box,
  Breadcrumbs,
  Link as MuiLink,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardActions,
  Button,
} from '@mui/material';
import {
  Search as SearchIcon,
  HelpOutline as HelpIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { helpApi } from '@/api/help';

export const HelpIndexPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch help topics dal backend
  const { data: topics, isLoading, error } = useQuery({
    queryKey: ['help-topics'],
    queryFn: helpApi.listTopics,
  });

  // Filtra topics in base alla ricerca
  const filteredTopics = useMemo(() => {
    if (!topics) return [];
    if (!searchQuery.trim()) return topics;

    const query = searchQuery.toLowerCase();
    return topics.filter((topic) => {
      const matchName = topic.name.toLowerCase().includes(query);
      const matchSummary = topic.summary.toLowerCase().includes(query);
      
      return matchName || matchSummary;
    });
  }, [topics, searchQuery]);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <MuiLink component={Link} to="/" underline="hover" color="inherit">
          Home
        </MuiLink>
        <Typography color="text.primary">Centro Assistenza</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <HelpIcon sx={{ fontSize: 40 }} color="primary" />
          <Typography variant="h4" component="h1" fontWeight={600}>
            Centro Assistenza
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Scegli un'applicazione per consultare la relativa guida operativa.
        </Typography>
      </Box>

      {/* Search bar */}
      <Box sx={{ mb: 4 }}>
        <TextField
          fullWidth
          placeholder="Cerca nelle guide..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Loading */}
      {isLoading && (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Errore nel caricamento delle guide. Riprova più tardi.
        </Alert>
      )}

      {/* Topics Grid */}
      {!isLoading && !error && (
        <>
          {filteredTopics.length === 0 ? (
            <Alert severity="info">
              Nessuna guida trovata con i criteri di ricerca specificati.
            </Alert>
          ) : (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3 }}>
              {filteredTopics.map((topic) => (
                <Card 
                  key={topic.slug}
                  sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 6,
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="h2" gutterBottom fontWeight={600}>
                      {topic.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {topic.summary}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      component={Link}
                      to={`/help/${topic.slug}`}
                      size="small"
                      endIcon={<ChevronRightIcon />}
                      sx={{ ml: 'auto' }}
                    >
                      Apri guida
                    </Button>
                  </CardActions>
                </Card>
              ))}
            </Box>
          )}
        </>
      )}
    </Container>
  );
};

