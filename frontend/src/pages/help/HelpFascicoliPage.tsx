import React from 'react';
import { Typography, Box, List, ListItem, ListItemText } from '@mui/material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpFascicoliPage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Fascicoli"
      summary="Pratiche aggreganti documenti e protocolli per cliente."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Funzioni principali
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="Organizzazione documenti per cliente in fascicoli tematici." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Classificazione tramite titolario gerarchico." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Gestione sottofascicoli per strutture complesse." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Tracciamento ubicazione fisica per fascicoli cartacei." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Come creare un fascicolo
          </Typography>
          <List sx={{ listStyleType: 'decimal', pl: 2 }}>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Accedere alla sezione Fascicoli dal menu." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Selezionare il cliente di riferimento." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Scegliere la voce di titolario appropriata." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Compilare titolo e descrizione del fascicolo." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Opzionale: specificare ubicazione fisica per fascicoli cartacei." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Titolario e classificazione
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Struttura gerarchica"
                secondary="Il titolario organizza i fascicoli in categorie e sottocategorie per facilitare la ricerca."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Codici automatici"
                secondary="Il sistema genera automaticamente codici fascicolo basati su cliente e titolario."
              />
            </ListItem>
          </List>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
