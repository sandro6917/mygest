/**
 * Componente per personalizzare il messaggio di alert (email/webhook)
 */
import React from 'react';
import {
  Box,
  TextField,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Stack,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

interface MessaggioAlertCustomInputProps {
  metodoAlert: 'email' | 'webhook';
  oggettoCustom?: string;
  corpoCustom?: string;
  payloadCustom?: string;
  onOggettoChange: (value: string) => void;
  onCorpoChange: (value: string) => void;
  onPayloadChange: (value: string) => void;
}

export const MessaggioAlertCustomInput: React.FC<MessaggioAlertCustomInputProps> = ({
  metodoAlert,
  oggettoCustom = '',
  corpoCustom = '',
  payloadCustom = '',
  onOggettoChange,
  onCorpoChange,
  onPayloadChange,
}) => {
  const [expanded, setExpanded] = React.useState(false);

  // Variabili disponibili per template
  const variabiliTemplate = [
    { nome: '{titolo}', desc: 'Titolo della scadenza' },
    { nome: '{descrizione}', desc: 'Descrizione dettagliata' },
    { nome: '{inizio}', desc: 'Data/ora inizio (formato 01/02/2026 14:30)' },
    { nome: '{fine}', desc: 'Data/ora fine' },
    { nome: '{categoria}', desc: 'Categoria della scadenza' },
    { nome: '{priorita}', desc: 'Priorità (Alta, Media, Bassa)' },
    { nome: '{offset_alert}', desc: 'Anticipo alert (es. "1 giorni")' },
  ];

  return (
    <Accordion 
      expanded={expanded} 
      onChange={() => setExpanded(!expanded)}
      sx={{ 
        backgroundColor: 'background.paper',
        '&:before': { display: 'none' },
      }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <InfoOutlinedIcon color="info" fontSize="small" />
          <Typography variant="subtitle2">
            Messaggio Personalizzato (Opzionale)
          </Typography>
        </Box>
      </AccordionSummary>
      
      <AccordionDetails>
        <Stack spacing={2}>
          {metodoAlert === 'email' ? (
            <>
              {/* Oggetto Email Custom */}
              <Box>
                <TextField
                  fullWidth
                  label="Oggetto Email Personalizzato"
                  placeholder="Lascia vuoto per usare il titolo della scadenza"
                  value={oggettoCustom}
                  onChange={(e) => onOggettoChange(e.target.value)}
                  helperText="Puoi usare variabili template come {titolo}, {inizio}, etc."
                  variant="outlined"
                  size="small"
                />
              </Box>

              {/* Corpo Email Custom */}
              <Box>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="Corpo Email Personalizzato"
                  placeholder={`Lascia vuoto per template di default:\n\nScadenza: {titolo}\nQuando: {inizio}\nDettagli: {descrizione}`}
                  value={corpoCustom}
                  onChange={(e) => onCorpoChange(e.target.value)}
                  helperText="Usa le variabili template elencate sotto"
                  variant="outlined"
                  size="small"
                />
              </Box>
            </>
          ) : (
            <>
              {/* Payload Webhook Custom */}
              <Box>
                <TextField
                  fullWidth
                  multiline
                  rows={8}
                  label="Payload Webhook Personalizzato (JSON)"
                  placeholder={`Lascia vuoto per payload di default:\n\n{\n  "id": 123,\n  "titolo": "...",\n  "inizio": "2026-02-01T14:30:00",\n  ...\n}`}
                  value={payloadCustom}
                  onChange={(e) => onPayloadChange(e.target.value)}
                  helperText="Inserisci un oggetto JSON valido. Se vuoto, usa payload di default."
                  variant="outlined"
                  size="small"
                  sx={{
                    '& textarea': {
                      fontFamily: 'monospace',
                      fontSize: '0.9rem',
                    },
                  }}
                />
              </Box>
            </>
          )}

          {/* Variabili Template (solo per email) */}
          {metodoAlert === 'email' && (
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                Variabili disponibili:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {variabiliTemplate.map((v) => (
                  <Chip
                    key={v.nome}
                    label={v.nome}
                    size="small"
                    variant="outlined"
                    title={v.desc}
                    sx={{ 
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      cursor: 'help',
                    }}
                  />
                ))}
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                💡 Clicca su una variabile per copiarne il nome e incollalo nel messaggio
              </Typography>
            </Box>
          )}

          {/* Info Webhook */}
          {metodoAlert === 'webhook' && (
            <Box 
              sx={{ 
                p: 1.5, 
                backgroundColor: 'info.light', 
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'info.main',
              }}
            >
              <Typography variant="caption" color="info.dark">
                <strong>Payload di Default:</strong><br />
                Se non specifichi un payload personalizzato, verrà inviato un JSON con:<br />
                - <code>id</code>, <code>scadenza</code>, <code>titolo</code>, <code>inizio</code>, <code>fine</code>, <code>metodo_alert</code><br />
                - <code>alert</code> (offset, periodo, programmata_il)
              </Typography>
            </Box>
          )}
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
};
