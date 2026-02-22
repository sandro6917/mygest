import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useResponsive } from '@/hooks/useResponsive';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Button,
  Menu,
  MenuItem,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DescriptionIcon from '@mui/icons-material/Description';
import FolderIcon from '@mui/icons-material/Folder';
import PeopleIcon from '@mui/icons-material/People';
import EventIcon from '@mui/icons-material/Event';
import EmailIcon from '@mui/icons-material/Email';
import ArchiveIcon from '@mui/icons-material/Archive';
import HelpIcon from '@mui/icons-material/Help';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import WorkIcon from '@mui/icons-material/Work';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import InventoryIcon from '@mui/icons-material/Inventory';

const getInitialTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') {
    return 'light';
  }
  const savedTheme = window.localStorage.getItem('theme') as 'light' | 'dark' | null;
  const initialTheme = savedTheme ?? 'light';
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', initialTheme);
  }
  return initialTheme;
};

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
  { label: 'Pratiche', path: '/pratiche', icon: <WorkIcon /> },
  { label: 'Fascicoli', path: '/fascicoli', icon: <FolderIcon /> },
  { label: 'Documenti', path: '/documenti', icon: <DescriptionIcon /> },
  { label: 'Anagrafiche', path: '/anagrafiche', icon: <PeopleIcon /> },
  { label: 'Scadenze', path: '/scadenze', icon: <EventIcon /> },
  { label: 'Comunicazioni', path: '/comunicazioni', icon: <EmailIcon /> },
  { label: 'Archivio', path: '/archivio', icon: <ArchiveIcon /> },
  { label: 'Operazioni', path: '/archivio-fisico/operazioni', icon: <InventoryIcon /> },
  { label: 'Help', path: '/help', icon: <HelpIcon /> },
  { label: 'AI Classifier', path: '/ai-classifier/jobs', icon: <SmartToyIcon /> },
];

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();
  const { isMobile } = useResponsive();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>(getInitialTheme);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    setAnchorEl(null);
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const handleUserMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const drawer = (
    <Box sx={{ width: 280 }}>
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="h6" component="div" sx={{ fontWeight: 600, color: 'primary.main' }}>
          MyGest
        </Typography>
        <IconButton onClick={handleDrawerToggle}>
          <CloseIcon />
        </IconButton>
      </Box>
      <List>
        {navItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              onClick={handleDrawerToggle}
              sx={{
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: 'primary.main' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
      <Box sx={{ p: 2 }}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={theme === 'light' ? <Brightness4Icon /> : <Brightness7Icon />}
          onClick={toggleTheme}
          sx={{ mb: 1 }}
        >
          {theme === 'light' ? 'Modalità Scura' : 'Modalità Chiara'}
        </Button>
        <Button
          fullWidth
          variant="contained"
          color="error"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
        >
          Logout
        </Button>
      </Box>
    </Box>
  );

  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      <AppBar
        position="sticky"
        elevation={1}
        sx={{
          backgroundColor: 'background.paper',
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, color: 'text.primary' }}
            >
              <MenuIcon />
            </IconButton>
          )}

          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{
              flexGrow: isMobile ? 1 : 0,
              textDecoration: 'none',
              color: 'primary.main',
              fontWeight: 600,
              mr: 4,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <DashboardIcon />
            MyGest
          </Typography>

          {!isMobile && (
            <Box sx={{ flexGrow: 1, display: 'flex', gap: 1 }}>
              {navItems.slice(0, 8).map((item) => (
                <Button
                  key={item.path}
                  component={Link}
                  to={item.path}
                  startIcon={item.icon}
                  sx={{
                    color: 'text.primary',
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {!isMobile && (
              <IconButton onClick={toggleTheme} color="inherit" sx={{ color: 'text.primary' }}>
                {theme === 'light' ? <Brightness4Icon /> : <Brightness7Icon />}
              </IconButton>
            )}

            <IconButton
              onClick={handleUserMenuClick}
              color="inherit"
              sx={{ color: 'text.primary' }}
            >
              <AccountCircleIcon />
            </IconButton>

            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleUserMenuClose}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
            >
              <MenuItem disabled>
                <Typography variant="body2" color="text.secondary">
                  {user?.first_name || user?.username}
                </Typography>
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Logout</ListItemText>
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="temporary"
        anchor="left"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 280 },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
}
