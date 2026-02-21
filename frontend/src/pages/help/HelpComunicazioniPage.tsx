import React from 'react';
import { Typography, Box, List, ListItem, ListItemText } from '@mui/material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpComunicazioniPage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Comunicazioni"
      summary="Creazione, invio e protocollazione dei messaggi verso i clienti."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Funzioni principali
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="Creazione comunicazioni basate su template personalizzabili con campi dinamici." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Invio email con allegati e tracciamento dello stato." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Protocollazione automatica delle comunicazioni inviate." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Gestione destinatari multipli e CC/BCC." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Come creare una comunicazione
          </Typography>
          <List sx={{ listStyleType: 'decimal', pl: 2 }}>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Accedere alla sezione Comunicazioni dal menu." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Selezionare il template appropriato o creare una comunicazione custom." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Compilare i campi richiesti e aggiungere eventuali allegati." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Inviare la comunicazione o salvarla come bozza." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Template e campi dinamici
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Template personalizzabili"
                secondary="I template supportano variabili dinamiche che vengono sostuite automaticamente con i dati del cliente."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Campi disponibili"
                secondary="Nome, cognome, ragione sociale, indirizzo, codice fiscale e altri dati anagrafici."
              />
            </ListItem>
          </List>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
