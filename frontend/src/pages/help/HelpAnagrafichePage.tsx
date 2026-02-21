import React from 'react';
import { Typography, Box, List, ListItem, ListItemText } from '@mui/material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpAnagrafichePage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Anagrafiche"
      summary="Gestione dei soggetti con dati fiscali, recapiti e relazioni cliente."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Funzioni principali
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="Creazione di soggetti persona fisica o giuridica con validazione codice fiscale/partita IVA." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Gestione recapiti (email, PEC, telefono) e indirizzi multipli." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Relazione 1:1 con il modello Cliente per soggetti attivi nel gestionale." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Collegamento rapido a pratiche, fascicoli e documenti tramite schermata dettaglio." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Come aggiungere un nuovo cliente
          </Typography>
          <List sx={{ listStyleType: 'decimal', pl: 2 }}>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Accedere a Anagrafiche dal menu principale." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Creare l'anagrafica specificando tipo soggetto, dati identificativi e recapiti." />
            </ListItem>
            <ListItem sx={{ display: 'list-item' }}>
              <ListItemText primary="Dal dettaglio anagrafica utilizzare l'azione &quot;Crea cliente&quot; per impostare dati contrattuali e fatturazione." />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Controlli automatici
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="Normalizzazione automatica di campi in fase di salvataggio (maiuscolo, trimming spazi)." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Verifica coerenza indirizzi associati al cliente." />
            </ListItem>
            <ListItem>
              <ListItemText primary="Indice e vincoli su PEC, partita IVA e codice cliente per prevenire duplicati." />
            </ListItem>
          </List>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
