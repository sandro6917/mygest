import React from 'react';
import { Typography, Box, List, ListItem, ListItemText } from '@mui/material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpArchivioFisicoPage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Archivio Fisico"
      summary="Tracciamento collocazione fisica di documenti e fascicoli."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Funzioni principali
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="Gestione gerarchica unità fisiche (uffici, stanze, scaffali, contenitori)." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Tracciamento ubicazione di documenti e fascicoli cartacei." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Operazioni di archivio: versamento, prelievo, scarto." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Stampa etichette e liste contenuti per unità fisiche." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Struttura gerarchica
          </Typography>
          <List sx={{ listStyleType: 'decimal', pl: 2 }}>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Ufficio: livello più alto della gerarchia." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Stanza: contenuta in un ufficio." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Scaffale/Mobile: contenuto in una stanza." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Ripiano: contenuto in scaffale/mobile." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Contenitore/Cartellina: livello finale." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Operazioni di archivio
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Versamento"
                secondary="Archiviazione di documenti/fascicoli in una ubicazione specifica."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Prelievo"
                secondary="Estrazione temporanea dall'archivio per consultazione."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Scarto"
                secondary="Eliminazione definitiva di documenti secondo normative."
              />
            </ListItem>
          </List>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
