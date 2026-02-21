import React from 'react';
import { Typography, Box, Button } from '@mui/material';
import { Download as DownloadIcon, OpenInNew as OpenInNewIcon } from '@mui/icons-material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpDeploymentPage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Guida Deployment e Sincronizzazione"
      summary="Deployment automatico/manuale, sincronizzazione DB e gestione archivio NAS."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Guida Completa
          </Typography>
          <Typography paragraph color="text.secondary">
            Questa guida completa copre tutte le procedure operative per il deployment,
            la sincronizzazione del database e la gestione dell'archivio NAS.
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 3 }}>
            <Button
              variant="contained"
              onClick={() => window.open('/guide/deployment.html', '_blank')}
              startIcon={<OpenInNewIcon />}
            >
              Visualizza Guida HTML
            </Button>
            <Button
              variant="outlined"
              onClick={() => window.open('/guide/deployment.pdf', '_blank')}
              startIcon={<DownloadIcon />}
            >
              Scarica PDF
            </Button>
          </Box>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Contenuti principali
          </Typography>
          <Box component="ul" sx={{ pl: 3 }}>
            <li>
              <Typography paragraph>
                <strong>Deployment automatico via GitHub Actions:</strong> Push su branch main attiva workflow automatico.
              </Typography>
            </li>
            <li>
              <Typography paragraph>
                <strong>Deployment manuale via SSH:</strong> Procedure passo-passo per deploy manuale sul VPS.
              </Typography>
            </li>
            <li>
              <Typography paragraph>
                <strong>Sincronizzazione database:</strong> Procedure per sincronizzare database tra sviluppo e produzione (bidirezionale).
              </Typography>
            </li>
            <li>
              <Typography paragraph>
                <strong>Gestione archivio NAS:</strong> Mount, permessi, backup con rclone e procedure di recovery.
              </Typography>
            </li>
            <li>
              <Typography paragraph>
                <strong>Troubleshooting:</strong> Soluzioni ai problemi comuni di deployment, sync e NAS.
              </Typography>
            </li>
            <li>
              <Typography paragraph>
                <strong>FAQ:</strong> Domande frequenti organizzate per categoria.
              </Typography>
            </li>
          </Box>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
