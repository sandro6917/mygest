import React from 'react';
import { Typography, Box, List, ListItem, ListItemText } from '@mui/material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpProtocolloPage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Protocollo"
      summary="Movimentazione IN/OUT con numerazione progressiva per cliente."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Funzioni principali
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="Registrazione movimenti di protocollo IN (entrata) e OUT (uscita)." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Numerazione progressiva automatica per cliente." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Collegamento a documenti e fascicoli." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Tracciamento ubicazione fisica dopo movimenti." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Protocollazione documenti
          </Typography>
          <List sx={{ listStyleType: 'decimal', pl: 2 }}>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Accedere al documento da protocollare." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Selezionare tipo movimento (IN per entrata, OUT per uscita)." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Il sistema assegna automaticamente il numero progressivo." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Opzionale: specificare ubicazione fisica per documenti cartacei." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Numerazione e registro
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Progressivo per cliente"
                secondary="Ogni cliente ha un registro protocollo indipendente con numerazione progressiva."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Stati magazzino"
                secondary="Disponibile, Uscito, Non tracciato per documenti digitali o non tracciabili."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Registro cronologico"
                secondary="Tutti i movimenti sono registrati con timestamp e utente."
              />
            </ListItem>
          </List>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
