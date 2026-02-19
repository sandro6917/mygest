/**
 * Directory Browser Component - File Explorer UI
 */
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Breadcrumbs,
  Link,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  Home as HomeIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  FolderSpecial as FolderSpecialIcon,
  ArrowUpward as UpIcon,
  Refresh as RefreshIcon,
  NavigateNext as NavigateNextIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { apiClient } from '@/api/client';

interface FileSystemItem {
  name: string;
  path: string;
  is_dir: boolean;
  is_file: boolean;
  size: number;
  modified: number;
  readable: boolean;
  writable: boolean;
  item_count?: number;
}

interface BrowseResponse {
  current_path: string;
  parent_path: string | null;
  items: FileSystemItem[];
  total_items: number;
}

interface QuickAccessItem {
  name: string;
  path: string;
  icon: string;
  type: string;
}

interface DirectoryBrowserProps {
  open: boolean;
  onClose: () => void;
  onSelect: (path: string) => void;
  initialPath?: string;
  title?: string;
}

export const DirectoryBrowser: React.FC<DirectoryBrowserProps> = ({
  open,
  onClose,
  onSelect,
  initialPath = '',
  title = 'Seleziona Directory',
}) => {
  const [currentPath, setCurrentPath] = useState(initialPath || '');
  const [items, setItems] = useState<FileSystemItem[]>([]);
  const [quickAccess, setQuickAccess] = useState<QuickAccessItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPath, setSelectedPath] = useState(initialPath || '');

  // Carica quick access al mount
  useEffect(() => {
    if (open) {
      loadQuickAccess();
      if (currentPath) {
        browse(currentPath);
      } else {
        loadQuickAccess().then((paths) => {
          if (paths.length > 0) {
            browse(paths[0].path);
          }
        });
      }
    }
  }, [open]);

  const loadQuickAccess = async () => {
    try {
      const { data } = await apiClient.get<QuickAccessItem[]>(
        '/ai-classifier/filesystem/quick_access/'
      );
      setQuickAccess(data);
      return data;
    } catch (err: any) {
      console.error('Error loading quick access:', err);
      return [];
    }
  };

  const browse = async (path: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const { data } = await apiClient.get<BrowseResponse>(
        '/ai-classifier/filesystem/browse/',
        { params: { path } }
      );
      
      setCurrentPath(data.current_path);
      setItems(data.items);
      setSelectedPath(data.current_path);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Errore durante caricamento directory');
      console.error('Browse error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (item: FileSystemItem) => {
    if (item.is_dir && item.readable) {
      browse(item.path);
    }
  };

  const handleItemSelect = (item: FileSystemItem) => {
    setSelectedPath(item.path);
  };

  const handleGoUp = () => {
    const parts = currentPath.split('/').filter(p => p);
    if (parts.length > 0) {
      parts.pop();
      const parentPath = '/' + parts.join('/');
      browse(parentPath || '/');
    }
  };

  const handleBreadcrumbClick = (index: number) => {
    const parts = currentPath.split('/').filter(p => p);
    const newPath = '/' + parts.slice(0, index + 1).join('/');
    browse(newPath || '/');
  };

  const handleSelect = () => {
    onSelect(selectedPath);
    onClose();
  };

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'home': return <HomeIcon />;
      case 'storage': return <StorageIcon />;
      case 'folder_special': return <FolderSpecialIcon />;
      case 'computer': return <ComputerIcon />;
      default: return <FolderIcon />;
    }
  };

  const formatSize = (bytes: number): string => {
    if (bytes === 0) return '-';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const pathParts = currentPath.split('/').filter(p => p);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">{title}</Typography>
          <Box display="flex" gap={1}>
            <IconButton size="small" onClick={handleGoUp} disabled={currentPath === '/'}>
              <UpIcon />
            </IconButton>
            <IconButton size="small" onClick={() => browse(currentPath)}>
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Box display="flex" height="500px">
          {/* Sidebar - Quick Access */}
          <Paper
            variant="outlined"
            sx={{ width: 200, mr: 2, p: 1, overflowY: 'auto' }}
          >
            <Typography variant="subtitle2" sx={{ mb: 1, px: 1 }}>
              Accesso Rapido
            </Typography>
            <List dense>
              {quickAccess.map((item, index) => (
                <ListItem key={index} disablePadding>
                  <ListItemButton onClick={() => browse(item.path)}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {getIcon(item.icon)}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.name}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* Main Content */}
          <Box flex={1} display="flex" flexDirection="column">
            {/* Breadcrumbs */}
            <Paper variant="outlined" sx={{ p: 1, mb: 1 }}>
              <Breadcrumbs
                separator={<NavigateNextIcon fontSize="small" />}
                maxItems={4}
                itemsBeforeCollapse={1}
                itemsAfterCollapse={2}
              >
                <Link
                  component="button"
                  variant="body2"
                  onClick={() => browse('/')}
                  sx={{ display: 'flex', alignItems: 'center' }}
                >
                  <HomeIcon sx={{ mr: 0.5 }} fontSize="small" />
                  Root
                </Link>
                {pathParts.map((part, index) => (
                  <Link
                    key={index}
                    component="button"
                    variant="body2"
                    onClick={() => handleBreadcrumbClick(index)}
                    color={index === pathParts.length - 1 ? 'text.primary' : 'inherit'}
                    sx={{
                      fontWeight: index === pathParts.length - 1 ? 600 : 400,
                    }}
                  >
                    {part}
                  </Link>
                ))}
              </Breadcrumbs>
            </Paper>

            {/* Search */}
            <TextField
              size="small"
              placeholder="Cerca..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              sx={{ mb: 1 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
            />

            {/* Error */}
            {error && (
              <Alert severity="error" sx={{ mb: 1 }}>
                {error}
              </Alert>
            )}

            {/* File List */}
            <Paper
              variant="outlined"
              sx={{
                flex: 1,
                overflowY: 'auto',
                position: 'relative',
              }}
            >
              {loading ? (
                <Box
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  height="100%"
                >
                  <CircularProgress />
                </Box>
              ) : (
                <List dense>
                  {filteredItems.map((item, index) => (
                    <ListItem
                      key={index}
                      disablePadding
                      secondaryAction={
                        item.is_dir ? (
                          <Chip
                            label={`${item.item_count || 0} elementi`}
                            size="small"
                            variant="outlined"
                          />
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            {formatSize(item.size)}
                          </Typography>
                        )
                      }
                    >
                      <ListItemButton
                        selected={selectedPath === item.path}
                        onClick={() => handleItemSelect(item)}
                        onDoubleClick={() => handleItemClick(item)}
                        disabled={!item.readable}
                      >
                        <ListItemIcon sx={{ minWidth: 40 }}>
                          {item.is_dir ? (
                            <FolderIcon color="primary" />
                          ) : (
                            <FileIcon color="action" />
                          )}
                        </ListItemIcon>
                        <ListItemText
                          primary={item.name}
                          primaryTypographyProps={{
                            variant: 'body2',
                            fontWeight: item.is_dir ? 500 : 400,
                          }}
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                  {filteredItems.length === 0 && !loading && (
                    <Box p={3} textAlign="center">
                      <Typography variant="body2" color="text.secondary">
                        {searchQuery
                          ? 'Nessun elemento trovato'
                          : 'Directory vuota'}
                      </Typography>
                    </Box>
                  )}
                </List>
              )}
            </Paper>

            {/* Selected Path */}
            <Box mt={1} p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="caption" color="text.secondary">
                Selezionato:
              </Typography>
              <Typography variant="body2" fontFamily="monospace">
                {selectedPath}
              </Typography>
            </Box>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Annulla</Button>
        <Button
          variant="contained"
          onClick={handleSelect}
          disabled={!selectedPath}
        >
          Seleziona
        </Button>
      </DialogActions>
    </Dialog>
  );
};
