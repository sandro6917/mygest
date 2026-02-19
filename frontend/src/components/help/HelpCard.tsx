import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Stack,
  Avatar,
} from '@mui/material';
import {
  Description as DocumentIcon,
  CheckCircle as CheckIcon,
  Settings as AttributeIcon,
  ArrowForward as ArrowIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import type { DocumentiTipo } from '@/types/documento';

interface HelpCardProps {
  tipo: DocumentiTipo;
}

export const HelpCard: React.FC<HelpCardProps> = ({ tipo }) => {
  const navigate = useNavigate();

  const campiObbligatoriCount = tipo.help_data?.campi_obbligatori?.sempre?.length || 0;
  const attributiCount = tipo.help_data?.attributi_dinamici?.disponibili?.length || 0;

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 6,
        },
      }}
    >
      <CardHeader
        avatar={
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <DocumentIcon />
          </Avatar>
        }
        title={tipo.nome}
        subheader={`Codice: ${tipo.codice}`}
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
      />
      
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {tipo.help_data?.descrizione_breve || 'Nessuna descrizione disponibile'}
        </Typography>

        {tipo.help_data && (
          <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
            {campiObbligatoriCount > 0 && (
              <Chip
                icon={<CheckIcon />}
                label={`${campiObbligatoriCount} campi`}
                size="small"
                variant="outlined"
                color="success"
              />
            )}
            {attributiCount > 0 && (
              <Chip
                icon={<AttributeIcon />}
                label={`${attributiCount} attributi`}
                size="small"
                variant="outlined"
                color="info"
              />
            )}
            {tipo.help_data.faq && tipo.help_data.faq.length > 0 && (
              <Chip
                label={`${tipo.help_data.faq.length} FAQ`}
                size="small"
                variant="outlined"
              />
            )}
          </Stack>
        )}
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Button
          size="small"
          onClick={() => navigate(`/help/documenti/${tipo.codice}`)}
          endIcon={<ArrowIcon />}
        >
          Leggi Guida
        </Button>
        <Button
          size="small"
          variant="contained"
          onClick={() => navigate(`/documenti/nuovo?tipo=${tipo.codice}`)}
        >
          Crea Documento
        </Button>
      </CardActions>
    </Card>
  );
};
