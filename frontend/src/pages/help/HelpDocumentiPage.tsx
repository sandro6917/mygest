import React, { useState, useMemo } from 'react';
import {
  Container,
  Typography,
  Grid,
  TextField,
  InputAdornment,
  Box,
  Paper,
  Breadcrumbs,
  Link as MuiLink,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  HelpOutline as HelpIcon,
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentiApi } from '@/api/documenti';
import { HelpCard } from '@/components/help';
import type { DocumentiTipo } from '@/types/documento';

export const HelpDocumentiPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch tipi documento con dati help
  const { data: tipi, isLoading, error } = useQuery({
    queryKey: ['documenti-tipi-help'],
    queryFn: async () => {
      const response = await documentiApi.listTipi();
      // Filtra solo i tipi che hanno help_data popolato e sono attivi
      return response.filter(
        (tipo: DocumentiTipo) => 
          tipo.attivo && tipo.help_data && Object.keys(tipo.help_data).length > 0
      ).sort((a: DocumentiTipo, b: DocumentiTipo) => 
        (a.help_ordine || 0) - (b.help_ordine || 0)
      );
    },
  });

  // Filtro tipi in base alla ricerca
  const filteredTipi = useMemo(() => {
    if (!tipi) return [];
    if (!searchQuery.trim()) return tipi;

    const query = searchQuery.toLowerCase();
    return tipi.filter((tipo: DocumentiTipo) => {
      const matchCodice = tipo.codice.toLowerCase().includes(query);
      const matchNome = tipo.nome.toLowerCase().includes(query);
      const matchDescrizione = tipo.help_data?.descrizione_breve?.toLowerCase().includes(query);
      
      return matchCodice || matchNome || matchDescrizione;
    });
  }, [tipi, searchQuery]);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <MuiLink component={Link} to="/" underline="hover" color="inherit">
          Home
        </MuiLink>
        <Typography color="text.primary">Help</Typography>
        <Typography color="text.primary">Tipi di Documento</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <HelpIcon sx={{ fontSize: 40 }} color="primary" />
          <Typography variant="h4" component="h1" fontWeight={600}>
            Guida Tipi di Documento
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Consulta la documentazione per ogni tipo di documento. Scopri quando usarli,
          quali campi compilare e come configurarli correttamente.
        </Typography>
      </Box>

      {/* Search bar */}
      <Paper sx={{ p: 2, mb: 4 }}>
        <TextField
          fullWidth
          placeholder="Cerca tipo documento per codice, nome o descrizione..."
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
      </Paper>

      {/* Loading */}
      {isLoading && (
        <Box display="flex" justifyContent="center" py={8}>
          <CircularProgress />
        </Box>
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          Errore nel caricamento dei tipi documento. Riprova più tardi.
        </Alert>
      )}

      {/* Results */}
      {!isLoading && !error && filteredTipi.length === 0 && searchQuery && (
        <Alert severity="info">
          Nessun tipo documento trovato per "{searchQuery}"
        </Alert>
      )}

      {!isLoading && !error && filteredTipi.length === 0 && !searchQuery && (
        <Alert severity="info">
          Nessun tipo documento ha documentazione help disponibile.
          Contatta l'amministratore per aggiungere guide.
        </Alert>
      )}

      {/* Cards Grid */}
      {!isLoading && !error && filteredTipi.length > 0 && (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {filteredTipi.length} {filteredTipi.length === 1 ? 'tipo trovato' : 'tipi trovati'}
          </Typography>
          
          <Grid container spacing={3}>
            {filteredTipi.map((tipo: DocumentiTipo) => (
              <Grid key={tipo.id} size={{ xs: 12, md: 6, lg: 4 }}>
                <HelpCard tipo={tipo} />
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </Container>
  );
};
