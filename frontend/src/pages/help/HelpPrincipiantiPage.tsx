import React from 'react';
import { Typography, Box, Alert } from '@mui/material';
import { HelpTopicPage } from './HelpTopicPage';

export const HelpPrincipiantiPage: React.FC = () => {
  return (
    <HelpTopicPage
      title="Guida Principianti"
      summary="Setup completo e workflow per backend e frontend."
    >
      <Box sx={{ '& section': { mb: 4 } }}>
        <Alert severity="info" sx={{ mb: 3 }}>
          Questa guida è destinata agli sviluppatori che devono configurare
          l'ambiente di sviluppo per la prima volta.
        </Alert>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Requisiti di sistema
          </Typography>
          <Box component="ul" sx={{ pl: 3 }}>
            <li><Typography>Python 3.10+</Typography></li>
            <li><Typography>Node.js 18+ e npm</Typography></li>
            <li><Typography>PostgreSQL 14+</Typography></li>
            <li><Typography>Redis (per cache)</Typography></li>
            <li><Typography>Git</Typography></li>
          </Box>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Setup Backend Django
          </Typography>
          <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, fontFamily: 'monospace', mb: 2 }}>
            <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap' }}>
{`# Clone repository
git clone https://github.com/sandro6917/mygest.git
cd mygest

# Crea virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt

# Configura database
# Crea settings_local.py con credenziali DB

# Esegui migrations
python manage.py migrate

# Crea superuser
python manage.py createsuperuser

# Avvia server
python manage.py runserver`}
            </Typography>
          </Box>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Setup Frontend React
          </Typography>
          <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, fontFamily: 'monospace', mb: 2 }}>
            <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap' }}>
{`# Entra nella cartella frontend
cd frontend

# Installa dipendenze
npm install

# Avvia dev server
npm run dev

# Build per produzione
npm run build`}
            </Typography>
          </Box>
        </section>

        <section>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Workflow di sviluppo
          </Typography>
          <Box component="ol" sx={{ pl: 3 }}>
            <li><Typography paragraph>Backend Django su http://localhost:8000</Typography></li>
            <li><Typography paragraph>Frontend Vite su http://localhost:5173</Typography></li>
            <li><Typography paragraph>API REST disponibili su /api/v1/</Typography></li>
            <li><Typography paragraph>Admin Django su /admin/</Typography></li>
          </Box>
        </section>
      </Box>
    </HelpTopicPage>
  );
};
