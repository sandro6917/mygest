import React from 'react';
import { Typography, Box, List, ListItem, ListItemText, Alert } from '@mui/material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpScadenzePage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Guida App Scadenze"
      summary="Passaggi essenziali backend/frontend con esempi pratici."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <Alert severity="info" sx={{ mb: 3 }}>
          Sistema completo di gestione scadenze con alert multipli e ricorrenze.
        </Alert>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Funzioni principali
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Scadenze singole e ricorrenti"
                secondary="Supporto per scadenze una tantum o ricorrenti (giornaliere, settimanali, mensili, annuali)."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Alert multipli configurabili"
                secondary="Possibilità di configurare più alert per ogni scadenza con anticipo personalizzabile."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Notifiche via email"
                secondary="Invio automatico di email di promemoria secondo configurazione alert."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Calendario integrato"
                secondary="Visualizzazione calendario con FullCalendar per panoramica mensile/settimanale."
              />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Tipi di ricorrenza
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Giornaliera"
                secondary="La scadenza si ripete ogni N giorni."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Settimanale"
                secondary="La scadenza si ripete ogni N settimane in giorni specifici."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Mensile"
                secondary="La scadenza si ripete ogni N mesi in un giorno specifico."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Annuale"
                secondary="La scadenza si ripete ogni anno nella stessa data."
              />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Configurazione alert
          </Typography>
          <Typography paragraph color="text.secondary">
            Ogni scadenza può avere multipli alert configurati con:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Giorni di anticipo"
                secondary="Numero di giorni prima della scadenza per l'invio dell'alert."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Tipo notifica"
                secondary="Email, notifica in-app o WhatsApp (se configurato)."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Destinatari"
                secondary="Utenti che riceveranno l'alert, configurabili per ogni alert."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Messaggio personalizzato"
                secondary="Template del messaggio con placeholder per dati dinamici."
              />
            </ListItem>
          </List>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Viste disponibili
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Scadenziario"
                secondary="Lista completa di tutte le occorrenze di scadenza con filtri e ricerca."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Calendario"
                secondary="Vista calendario mensile/settimanale/giornaliera con eventi cliccabili."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Widget Dashboard"
                secondary="Riepilogo scadenze imminenti nella pagina principale."
              />
            </ListItem>
          </List>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
