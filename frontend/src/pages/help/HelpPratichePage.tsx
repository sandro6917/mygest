import React from 'react';
import { Typography, Box, List, ListItem, ListItemText } from '@mui/material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpPratichePage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Pratiche"
      summary="Workflow operativo con scadenze e stato di avanzamento."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Funzioni principali
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="Gestione workflow pratiche con stati personalizzabili." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Associazione a clienti, fascicoli e documenti." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Sistema di note cronologiche con timestamp." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Collegamento a scadenze e alert automatici." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Come gestire una pratica
          </Typography>
          <List sx={{ listStyleType: 'decimal', pl: 2 }}>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Creare la pratica specificando cliente e tipologia." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Collegare documenti e fascicoli pertinenti." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Aggiornare lo stato avanzamento pratica." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Aggiungere note cronologiche per tracciare le attività." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Stati e workflow
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Stati predefiniti"
                secondary="Aperta, In lavorazione, In attesa, Completata, Archiviata."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Note cronologiche"
                secondary="Ogni modifica di stato viene registrata con timestamp e utente."
              />
            </ListItem>
          </List>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
