import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Breadcrumbs,
  Link as MuiLink,
  Button,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Chip,
  Stack,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  ExpandMore as ExpandIcon,
  Add as AddIcon,
  PictureAsPdf as PdfIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentiApi } from '@/api/documenti';
import { exportHelpToPDF } from '@/utils/pdfExport';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

export const HelpDocumentoTipoDetailPage: React.FC = () => {
  const { codice } = useParams<{ codice: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);

  // Fetch tipo documento
  const { data: tipi, isLoading, error } = useQuery({
    queryKey: ['documenti-tipi'],
    queryFn: () => documentiApi.listTipi(),
  });

  const tipo = tipi?.find(t => t.codice === codice);

  const handleDownloadPDF = () => {
    if (tipo && tipo.help_data) {
      exportHelpToPDF(tipo.nome, tipo.codice, tipo.help_data);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !tipo) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          Tipo documento non trovato o errore nel caricamento.
        </Alert>
      </Container>
    );
  }

  if (!tipo.help_data || Object.keys(tipo.help_data).length === 0) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="info">
          Nessuna documentazione disponibile per questo tipo di documento.
        </Alert>
        <Button sx={{ mt: 2 }} onClick={() => navigate('/help/documenti')}>
          Torna alla lista
        </Button>
      </Container>
    );
  }

  const helpData = tipo.help_data;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <MuiLink component={Link} to="/" underline="hover" color="inherit">
          Home
        </MuiLink>
        <MuiLink component={Link} to="/help/documenti" underline="hover" color="inherit">
          Help Documenti
        </MuiLink>
        <Typography color="text.primary">{tipo.nome}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={2} alignItems="center" mb={1}>
          <Typography variant="h3" component="h1" fontWeight={600}>
            {tipo.nome}
          </Typography>
          <Chip label={tipo.codice} color="primary" />
        </Stack>
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          {helpData.descrizione_breve}
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate(`/documenti/nuovo?tipo=${tipo.codice}`)}
          >
            Crea Nuovo {tipo.nome}
          </Button>
          <Button
            variant="outlined"
            startIcon={<PdfIcon />}
            onClick={handleDownloadPDF}
            color="error"
          >
            Scarica PDF
          </Button>
        </Stack>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* Tabs */}
      <Paper>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="📖 Panoramica" />
          <Tab label="✏️ Guida" />
          <Tab label="🔧 Attributi" />
          <Tab label="📝 Pattern Codice" />
          <Tab label="📦 Archiviazione" />
          <Tab label="📁 Fascicoli" />
          <Tab label="⚙️ Workflow" />
          <Tab label="📋 Protocollazione" />
          <Tab label="📊 Tracciabilità" />
          <Tab label="❓ FAQ" />
        </Tabs>

        {/* Tab 1: Panoramica */}
        <TabPanel value={activeTab} index={0}>
          <Box sx={{ px: 3 }}>
            {/* Quando usare */}
            {helpData.quando_usare && (
              <Box mb={4}>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Quando usare questo tipo
                </Typography>
                <List>
                  {helpData.quando_usare.casi_uso.map((caso, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckIcon color="success" />
                      </ListItemIcon>
                      <ListItemText primary={caso} />
                    </ListItem>
                  ))}
                </List>
                {helpData.quando_usare.non_usare_per && helpData.quando_usare.non_usare_per.length > 0 && (
                  <>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                      Non usare per:
                    </Typography>
                    <List dense>
                      {helpData.quando_usare.non_usare_per.map((caso, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={`• ${caso}`} />
                        </ListItem>
                      ))}
                    </List>
                  </>
                )}
              </Box>
            )}

            {/* Campi obbligatori */}
            {helpData.campi_obbligatori && (
              <Box mb={4}>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Campi richiesti
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Campo</strong></TableCell>
                        <TableCell><strong>Condizione</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {helpData.campi_obbligatori.sempre.map((campo) => (
                        <TableRow key={campo}>
                          <TableCell><Chip label={campo} size="small" /></TableCell>
                          <TableCell>Sempre obbligatorio</TableCell>
                        </TableRow>
                      ))}
                      {Object.entries(helpData.campi_obbligatori.condizionali || {}).map(([campo, condizione]) => (
                        <TableRow key={campo}>
                          <TableCell><Chip label={campo} size="small" color="warning" /></TableCell>
                          <TableCell>{condizione}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* Note speciali */}
            {helpData.note_speciali && (
              <Box mb={4}>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Note Importanti
                </Typography>
                
                {helpData.note_speciali.attenzioni && helpData.note_speciali.attenzioni.length > 0 && (
                  <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                      Attenzioni
                    </Typography>
                    {helpData.note_speciali.attenzioni.map((nota, index) => (
                      <Typography key={index} variant="body2" paragraph>
                        {nota}
                      </Typography>
                    ))}
                  </Alert>
                )}

                {helpData.note_speciali.suggerimenti && helpData.note_speciali.suggerimenti.length > 0 && (
                  <Alert severity="info" icon={<LightbulbIcon />} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                      Suggerimenti
                    </Typography>
                    {helpData.note_speciali.suggerimenti.map((sug, index) => (
                      <Typography key={index} variant="body2" paragraph>
                        {sug}
                      </Typography>
                    ))}
                  </Alert>
                )}
              </Box>
            )}
          </Box>
        </TabPanel>

        {/* Tab 2: Guida Compilazione */}
        <TabPanel value={activeTab} index={1}>
          <Box sx={{ px: 3 }}>
            {helpData.guida_compilazione && helpData.guida_compilazione.step && (
              <Stepper orientation="vertical">
                {helpData.guida_compilazione.step.map((step, index) => (
                  <Step key={index} active>
                    <StepLabel>
                      <Typography variant="h6">{step.titolo}</Typography>
                    </StepLabel>
                    <StepContent>
                      <Typography paragraph>{step.descrizione}</Typography>
                      {step.esempio && (
                        <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 2 }}>
                          <Typography variant="body2" color="text.secondary">
                            <strong>Esempio:</strong> {step.esempio}
                          </Typography>
                        </Box>
                      )}
                      {step.attenzione && (
                        <Alert severity="info" sx={{ mt: 2 }}>
                          {step.attenzione}
                        </Alert>
                      )}
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            )}

            {helpData.guida_compilazione?.shortcut && (
              <Box mt={4}>
                <Alert severity="success" icon={<InfoIcon />}>
                  <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                    {helpData.guida_compilazione.shortcut.titolo}
                  </Typography>
                  <Typography variant="body2" paragraph>
                    {helpData.guida_compilazione.shortcut.descrizione}
                  </Typography>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => navigate(helpData.guida_compilazione!.shortcut!.link)}
                  >
                    Vai alla funzione
                  </Button>
                </Alert>
              </Box>
            )}
          </Box>
        </TabPanel>

        {/* Tab 3: Attributi */}
        <TabPanel value={activeTab} index={2}>
          <Box sx={{ px: 3 }}>
            {helpData.attributi_dinamici && helpData.attributi_dinamici.disponibili && (
              <>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Attributi Disponibili
                </Typography>
                {helpData.attributi_dinamici.disponibili.map((attr, index) => (
                  <Accordion key={index}>
                    <AccordionSummary expandIcon={<ExpandIcon />}>
                      <Stack direction="row" spacing={2} alignItems="center">
                        <Typography fontWeight={600}>{attr.nome}</Typography>
                        <Chip label={attr.tipo} size="small" variant="outlined" />
                        {attr.obbligatorio && <Chip label="Obbligatorio" size="small" color="error" />}
                      </Stack>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography paragraph>{attr.descrizione}</Typography>
                      {attr.esempio && (
                        <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1 }}>
                          <Typography variant="body2">
                            <strong>Esempio:</strong> {attr.esempio}
                          </Typography>
                        </Box>
                      )}
                    </AccordionDetails>
                  </Accordion>
                ))}
              </>
            )}
          </Box>
        </TabPanel>

        {/* Tab 4: Pattern Codice */}
        <TabPanel value={activeTab} index={3}>
          <Box sx={{ px: 3 }}>
            {helpData.pattern_codice ? (
              <>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Generazione Codice Documento
                </Typography>
                
                <Paper variant="outlined" sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Pattern configurato:
                  </Typography>
                  <Typography variant="h5" fontFamily="monospace" gutterBottom>
                    {helpData.pattern_codice.default}
                  </Typography>
                </Paper>

                <Typography paragraph>{helpData.pattern_codice.spiegazione}</Typography>

                {/* Esempi */}
                {helpData.pattern_codice.esempi && helpData.pattern_codice.esempi.length > 0 && (
                  <Box mb={4}>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Esempi
                    </Typography>
                    {helpData.pattern_codice.esempi.map((esempio, index) => (
                      <Paper key={index} variant="outlined" sx={{ p: 2, mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Input:
                        </Typography>
                        <Box sx={{ bgcolor: 'grey.100', p: 1.5, borderRadius: 1, mb: 1.5 }}>
                          {Object.entries(esempio.input).map(([key, value]) => (
                            <Typography key={key} variant="body2" fontFamily="monospace">
                              {key}: {String(value)}
                            </Typography>
                          ))}
                        </Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Output:
                        </Typography>
                        <Typography variant="h6" fontFamily="monospace" color="primary" gutterBottom>
                          {esempio.output}
                        </Typography>
                        {esempio.descrizione && (
                          <Typography variant="body2" color="text.secondary">
                            {esempio.descrizione}
                          </Typography>
                        )}
                      </Paper>
                    ))}
                  </Box>
                )}

                {/* Placeholder disponibili */}
                {helpData.pattern_codice.placeholder_disponibili && (
                  <Box mb={4}>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Placeholder Disponibili
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell><strong>Placeholder</strong></TableCell>
                            <TableCell><strong>Descrizione</strong></TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {Object.entries(helpData.pattern_codice.placeholder_disponibili).map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell>
                                <Typography fontFamily="monospace" fontSize="0.875rem">
                                  {key}
                                </Typography>
                              </TableCell>
                              <TableCell>{value}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}

                {helpData.pattern_codice.personalizzazione && (
                  <Alert severity="info">
                    {helpData.pattern_codice.personalizzazione}
                  </Alert>
                )}
              </>
            ) : (
              <Alert severity="info">
                Nessuna informazione disponibile sul pattern codice.
              </Alert>
            )}
          </Box>
        </TabPanel>

        {/* Tab 5: Archiviazione */}
        <TabPanel value={activeTab} index={4}>
          <Box sx={{ px: 3 }}>
            {helpData.archiviazione ? (
              <>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Archiviazione File
                </Typography>

                <Box mb={4}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Struttura Percorso:
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
                    <Typography fontFamily="monospace" fontSize="0.9rem">
                      {helpData.archiviazione.percorso_tipo}
                    </Typography>
                  </Paper>
                  
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Esempio Completo:
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.main' }}>
                    <Typography fontFamily="monospace" fontSize="0.85rem" sx={{ wordBreak: 'break-all' }}>
                      {helpData.archiviazione.esempio_completo}
                    </Typography>
                  </Paper>
                </Box>

                {helpData.archiviazione.nome_file_pattern && (
                  <Box mb={4}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Pattern Nome File:
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50', mb: 1 }}>
                      <Typography fontFamily="monospace">
                        {helpData.archiviazione.nome_file_pattern}
                      </Typography>
                    </Paper>
                    {helpData.archiviazione.esempio_file && (
                      <>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Esempio: <code>{helpData.archiviazione.esempio_file}</code>
                        </Typography>
                      </>
                    )}
                  </Box>
                )}

                {helpData.archiviazione.organizzazione && (
                  <Alert severity="info" sx={{ mb: 3 }}>
                    <Typography variant="body2">{helpData.archiviazione.organizzazione}</Typography>
                  </Alert>
                )}

                {helpData.archiviazione.note && helpData.archiviazione.note.length > 0 && (
                  <Box>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Note Importanti
                    </Typography>
                    <List>
                      {helpData.archiviazione.note.map((nota, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={nota} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </>
            ) : (
              <Alert severity="info">
                Nessuna informazione disponibile sull'archiviazione.
              </Alert>
            )}
          </Box>
        </TabPanel>

        {/* Tab 6: Fascicoli */}
        <TabPanel value={activeTab} index={5}>
          <Box sx={{ px: 3 }}>
            {helpData.relazione_fascicoli ? (
              <>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Relazione con i Fascicoli
                </Typography>
                <Typography paragraph>{helpData.relazione_fascicoli.descrizione}</Typography>

                {/* Vantaggi collegamento */}
                {helpData.relazione_fascicoli.vantaggi_collegamento && helpData.relazione_fascicoli.vantaggi_collegamento.length > 0 && (
                  <Box mb={4}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Vantaggi del Collegamento
                    </Typography>
                    <List dense>
                      {helpData.relazione_fascicoli.vantaggi_collegamento.map((vantaggio, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={vantaggio} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Come collegare */}
                {helpData.relazione_fascicoli.come_collegare && (
                  <Box mb={4}>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Come Collegare a un Fascicolo
                    </Typography>
                    {Object.entries(helpData.relazione_fascicoli.come_collegare).map(([key, metodo]) => (
                      metodo && (
                        <Accordion key={key}>
                          <AccordionSummary expandIcon={<ExpandIcon />}>
                            <Typography fontWeight={600}>{metodo.titolo}</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Typography paragraph>{metodo.descrizione}</Typography>
                            {metodo.passaggi && metodo.passaggi.length > 0 && (
                              <Box mb={2}>
                                <Typography variant="subtitle2" gutterBottom>Passaggi:</Typography>
                                {metodo.passaggi.map((passo, idx) => (
                                  <Typography key={idx} variant="body2" paragraph>
                                    {passo}
                                  </Typography>
                                ))}
                              </Box>
                            )}
                            {metodo.benefici && metodo.benefici.length > 0 && (
                              <Alert severity="success" sx={{ mt: 2 }}>
                                {metodo.benefici.map((beneficio, idx) => (
                                  <Typography key={idx} variant="body2">
                                    {beneficio}
                                  </Typography>
                                ))}
                              </Alert>
                            )}
                            {metodo.attenzioni && metodo.attenzioni.length > 0 && (
                              <Alert severity="warning" sx={{ mt: 2 }}>
                                {metodo.attenzioni.map((attenzione, idx) => (
                                  <Typography key={idx} variant="body2">
                                    {attenzione}
                                  </Typography>
                                ))}
                              </Alert>
                            )}
                          </AccordionDetails>
                        </Accordion>
                      )
                    ))}
                  </Box>
                )}

                {/* Regole Business */}
                {helpData.relazione_fascicoli.regole_business && (
                  <Box mb={4}>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      {helpData.relazione_fascicoli.regole_business.titolo}
                    </Typography>
                    {helpData.relazione_fascicoli.regole_business.regole.map((regola, index) => (
                      <Accordion key={index}>
                        <AccordionSummary expandIcon={<ExpandIcon />}>
                          <Typography fontWeight={600}>{regola.regola}</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography paragraph>{regola.spiegazione}</Typography>
                          {regola.esempio && (
                            <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 1, fontFamily: 'monospace' }}>
                              <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                                {regola.esempio}
                              </Typography>
                            </Box>
                          )}
                          {(regola.esempio_ok || regola.esempio_ko) && (
                            <Stack spacing={1} mt={1}>
                              {regola.esempio_ok && (
                                <Chip label={regola.esempio_ok} size="small" color="success" />
                              )}
                              {regola.esempio_ko && (
                                <Chip label={regola.esempio_ko} size="small" color="error" />
                              )}
                            </Stack>
                          )}
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </Box>
                )}

                {/* Casi d'uso */}
                {helpData.relazione_fascicoli.casi_uso_tipici && (
                  <Box mb={4}>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Casi d'Uso Tipici
                    </Typography>
                    {Object.entries(helpData.relazione_fascicoli.casi_uso_tipici).map(([key, caso]) => (
                      caso && (
                        <Accordion key={key}>
                          <AccordionSummary expandIcon={<ExpandIcon />}>
                            <Typography fontWeight={600}>{caso.scenario}</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Typography paragraph>{caso.descrizione}</Typography>
                            {caso.vantaggi && (
                              <Alert severity="info" sx={{ mb: 2 }}>
                                <Typography variant="body2"><strong>Vantaggi:</strong> {caso.vantaggi}</Typography>
                              </Alert>
                            )}
                            {caso.esempio_struttura && (
                              <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, fontFamily: 'monospace' }}>
                                <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                                  {caso.esempio_struttura}
                                </Typography>
                              </Box>
                            )}
                          </AccordionDetails>
                        </Accordion>
                      )
                    ))}
                  </Box>
                )}

                {/* Best Practices */}
                {helpData.relazione_fascicoli.best_practices && helpData.relazione_fascicoli.best_practices.length > 0 && (
                  <Box mb={4}>
                    <Alert severity="success" icon={<LightbulbIcon />}>
                      <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                        Best Practices
                      </Typography>
                      {helpData.relazione_fascicoli.best_practices.map((pratica, index) => (
                        <Typography key={index} variant="body2" paragraph>
                          {pratica}
                        </Typography>
                      ))}
                    </Alert>
                  </Box>
                )}

                {/* FAQ Fascicoli */}
                {helpData.relazione_fascicoli.domande_frequenti && helpData.relazione_fascicoli.domande_frequenti.length > 0 && (
                  <Box>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Domande Frequenti sui Fascicoli
                    </Typography>
                    {helpData.relazione_fascicoli.domande_frequenti.map((faq, index) => (
                      <Accordion key={index}>
                        <AccordionSummary expandIcon={<ExpandIcon />}>
                          <Typography fontWeight={600}>{faq.domanda}</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography>{faq.risposta}</Typography>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </Box>
                )}
              </>
            ) : (
              <Alert severity="info">
                Nessuna informazione disponibile sulla relazione con i fascicoli.
              </Alert>
            )}
          </Box>
        </TabPanel>

        {/* Tab 7: Workflow */}
        <TabPanel value={activeTab} index={6}>
          <Box sx={{ px: 3 }}>
            {helpData.workflow ? (
              <>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Workflow e Stati Documento
                </Typography>

                {/* Stati possibili */}
                {helpData.workflow.stati_possibili && helpData.workflow.stati_possibili.length > 0 && (
                  <Box mb={4}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Stati Possibili
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                      {helpData.workflow.stati_possibili.map((stato, index) => (
                        <Chip 
                          key={index} 
                          label={stato} 
                          color={stato === helpData.workflow.stato_iniziale ? 'primary' : 'default'}
                          variant={stato === helpData.workflow.stato_iniziale ? 'filled' : 'outlined'}
                        />
                      ))}
                    </Box>
                    {helpData.workflow.stato_iniziale && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        Stato iniziale: <strong>{helpData.workflow.stato_iniziale}</strong>
                      </Alert>
                    )}
                  </Box>
                )}

                {/* Azioni disponibili */}
                {helpData.workflow.azioni_disponibili && helpData.workflow.azioni_disponibili.length > 0 && (
                  <Box mb={4}>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Azioni Disponibili
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell><strong>Azione</strong></TableCell>
                            <TableCell><strong>Quando</strong></TableCell>
                            <TableCell><strong>Effetto</strong></TableCell>
                            <TableCell><strong>Permessi</strong></TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {helpData.workflow.azioni_disponibili.map((azione, index) => (
                            <TableRow key={index}>
                              <TableCell>
                                <Chip label={azione.azione} size="small" color="primary" />
                              </TableCell>
                              <TableCell>{azione.quando}</TableCell>
                              <TableCell>{azione.effetto}</TableCell>
                              <TableCell>
                                {azione.permessi || 'Tutti gli utenti'}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}

                {/* Transizioni */}
                {helpData.workflow.transizioni && Object.keys(helpData.workflow.transizioni).length > 0 && (
                  <Box>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      Transizioni di Stato
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell><strong>Da Stato</strong></TableCell>
                            <TableCell><strong>A Stato</strong></TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {Object.entries(helpData.workflow.transizioni).map(([from, to], index) => (
                            <TableRow key={index}>
                              <TableCell>
                                <Chip label={from} size="small" variant="outlined" />
                              </TableCell>
                              <TableCell>
                                <Chip label={to} size="small" color="primary" />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}
              </>
            ) : (
              <Alert severity="info">
                Nessuna informazione disponibile sul workflow.
              </Alert>
            )}
          </Box>
        </TabPanel>

        {/* Tab 8: Protocollazione */}
        <TabPanel value={activeTab} index={7}>
          <Box sx={{ px: 3 }}>
            {helpData.protocollazione ? (
              <>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Protocollazione
                </Typography>
                
                {helpData.protocollazione.descrizione && (
                  <Alert severity="info" sx={{ mb: 3 }}>
                    {helpData.protocollazione.descrizione}
                  </Alert>
                )}

                {/* Quando Protocollare */}
                {helpData.protocollazione.quando_protocollare && helpData.protocollazione.quando_protocollare.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Quando Protocollare
                    </Typography>
                    <List>
                      {helpData.protocollazione.quando_protocollare.map((item, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <CheckIcon color="success" />
                          </ListItemIcon>
                          <ListItemText primary={item} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Processo */}
                {helpData.protocollazione.processo?.step && helpData.protocollazione.processo.step.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Processo di Protocollazione
                    </Typography>
                    <Stepper orientation="vertical">
                      {helpData.protocollazione.processo.step.map((step, idx) => (
                        <Step key={idx} active>
                          <StepLabel>{step}</StepLabel>
                        </Step>
                      ))}
                    </Stepper>
                  </Box>
                )}

                {/* Numero Protocollo */}
                {helpData.protocollazione.numero_protocollo && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Numero di Protocollo
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Formato:</strong> {helpData.protocollazione.numero_protocollo.formato}
                      </Typography>
                      <Typography variant="body2" color="primary" sx={{ my: 1 }}>
                        <strong>Esempio:</strong> {helpData.protocollazione.numero_protocollo.esempio}
                      </Typography>
                      <Typography variant="body2">
                        {helpData.protocollazione.numero_protocollo.spiegazione}
                      </Typography>
                    </Paper>
                  </Box>
                )}

                {/* Registro */}
                {helpData.protocollazione.registro && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Registro di Protocollo
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {helpData.protocollazione.registro.descrizione}
                    </Typography>
                    {helpData.protocollazione.registro.informazioni_registrate && helpData.protocollazione.registro.informazioni_registrate.length > 0 && (
                      <>
                        <Typography variant="body2" fontWeight={600} gutterBottom>
                          Informazioni registrate:
                        </Typography>
                        <List dense>
                          {helpData.protocollazione.registro.informazioni_registrate.map((info, idx) => (
                            <ListItem key={idx}>
                              <ListItemText primary={`• ${info}`} />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}
                  </Box>
                )}

                {/* Vincoli */}
                {helpData.protocollazione.vincoli && helpData.protocollazione.vincoli.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Vincoli
                    </Typography>
                    <List>
                      {helpData.protocollazione.vincoli.map((vincolo, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <WarningIcon color="warning" />
                          </ListItemIcon>
                          <ListItemText primary={vincolo} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Note */}
                {helpData.protocollazione.note && helpData.protocollazione.note.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Note Importanti
                    </Typography>
                    <List>
                      {helpData.protocollazione.note.map((nota, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <InfoIcon color="info" />
                          </ListItemIcon>
                          <ListItemText primary={nota} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </>
            ) : (
              <Alert severity="info">
                Nessuna informazione disponibile sulla protocollazione.
              </Alert>
            )}
          </Box>
        </TabPanel>

        {/* Tab 9: Tracciabilità */}
        <TabPanel value={activeTab} index={8}>
          <Box sx={{ px: 3 }}>
            {helpData.tracciabilita ? (
              <>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Tracciabilità
                </Typography>
                
                {helpData.tracciabilita.descrizione && (
                  <Alert severity="info" sx={{ mb: 3 }}>
                    {helpData.tracciabilita.descrizione}
                  </Alert>
                )}

                {/* Cosa Viene Tracciato */}
                {helpData.tracciabilita.cosa_viene_tracciato && helpData.tracciabilita.cosa_viene_tracciato.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Cosa Viene Tracciato
                    </Typography>
                    <List>
                      {helpData.tracciabilita.cosa_viene_tracciato.map((item, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <CheckIcon color="success" />
                          </ListItemIcon>
                          <ListItemText primary={item} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Eventi Tracciati */}
                {helpData.tracciabilita.eventi_tracciati && helpData.tracciabilita.eventi_tracciati.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Eventi Tracciati
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell><strong>Evento</strong></TableCell>
                            <TableCell><strong>Descrizione</strong></TableCell>
                            <TableCell><strong>Informazioni Registrate</strong></TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {helpData.tracciabilita.eventi_tracciati.map((evento, idx) => (
                            <TableRow key={idx}>
                              <TableCell><Chip label={evento.evento} size="small" color="primary" /></TableCell>
                              <TableCell>{evento.descrizione}</TableCell>
                              <TableCell>
                                <List dense disablePadding>
                                  {evento.informazioni_registrate.map((info, i) => (
                                    <ListItem key={i} disableGutters>
                                      <ListItemText primary={`• ${info}`} />
                                    </ListItem>
                                  ))}
                                </List>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}

                {/* Consultazione Storico */}
                {helpData.tracciabilita.consultazione_storico && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Consultazione Storico
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="body2" gutterBottom>
                        <strong>Dove:</strong> {helpData.tracciabilita.consultazione_storico.dove}
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Come:</strong> {helpData.tracciabilita.consultazione_storico.come}
                      </Typography>
                      {helpData.tracciabilita.consultazione_storico.informazioni_visualizzate && helpData.tracciabilita.consultazione_storico.informazioni_visualizzate.length > 0 && (
                        <>
                          <Typography variant="body2" fontWeight={600} gutterBottom>
                            Informazioni visualizzate:
                          </Typography>
                          <List dense>
                            {helpData.tracciabilita.consultazione_storico.informazioni_visualizzate.map((info, idx) => (
                              <ListItem key={idx}>
                                <ListItemText primary={`• ${info}`} />
                              </ListItem>
                            ))}
                          </List>
                        </>
                      )}
                    </Paper>
                  </Box>
                )}

                {/* Utilità */}
                {helpData.tracciabilita.utilita && helpData.tracciabilita.utilita.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Utilità
                    </Typography>
                    <List>
                      {helpData.tracciabilita.utilita.map((item, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <LightbulbIcon color="warning" />
                          </ListItemIcon>
                          <ListItemText primary={item} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Vincoli */}
                {helpData.tracciabilita.vincoli && helpData.tracciabilita.vincoli.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Vincoli
                    </Typography>
                    <List>
                      {helpData.tracciabilita.vincoli.map((vincolo, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <WarningIcon color="warning" />
                          </ListItemIcon>
                          <ListItemText primary={vincolo} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </>
            ) : (
              <Alert severity="info">
                Nessuna informazione disponibile sulla tracciabilità.
              </Alert>
            )}
          </Box>
        </TabPanel>

        {/* Tab 10: FAQ */}
        <TabPanel value={activeTab} index={9}>
          <Box sx={{ px: 3 }}>
            {helpData.faq && helpData.faq.length > 0 ? (
              <>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Domande Frequenti
                </Typography>
                {helpData.faq.map((faq, index) => (
                  <Accordion key={index}>
                    <AccordionSummary expandIcon={<ExpandIcon />}>
                      <Typography fontWeight={600}>{faq.domanda}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography>{faq.risposta}</Typography>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </>
            ) : (
              <Alert severity="info">
                Nessuna FAQ disponibile per questo tipo di documento.
              </Alert>
            )}
          </Box>
        </TabPanel>
      </Paper>
    </Container>
  );
};
