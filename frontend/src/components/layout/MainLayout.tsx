import { Outlet } from 'react-router-dom';
import { Box, Container } from '@mui/material';
import { Navbar } from './Navbar';

export function MainLayout() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
      }}
    >
      <Navbar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          py: { xs: 2, sm: 3, md: 4 },
          px: { xs: 2, sm: 3 },
          backgroundColor: 'background.default',
        }}
      >
        <Container maxWidth="xl" disableGutters>
          <Outlet />
        </Container>
      </Box>
      <Box
        component="footer"
        sx={{
          py: 2,
          px: 2,
          mt: 'auto',
          backgroundColor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider',
          textAlign: 'center',
        }}
      >
        <Box component="p" sx={{ m: 0, color: 'text.secondary', fontSize: '0.875rem' }}>
          © 2025 MyGest - v1.5.0
        </Box>
      </Box>
    </Box>
  );
}

