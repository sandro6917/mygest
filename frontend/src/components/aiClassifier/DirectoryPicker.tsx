/**
 * Directory Picker con supporto NAS, SMB e percorsi Windows
 */
import React, { useState } from 'react';
import {
  TextField,
  Autocomplete,
  Box,
  Chip,
  Typography,
  InputAdornment,
  IconButton,
  Tooltip,
  Button,
} from '@mui/material';
import {
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Info as InfoIcon,
  FolderCopy as BrowseIcon,
} from '@mui/icons-material';
import { DirectoryBrowser } from './DirectoryBrowser';

interface DirectoryPickerProps {
  value: string;
  onChange: (value: string) => void;
  error?: boolean;
  helperText?: string;
  label?: string;
  required?: boolean;
}

// Percorsi suggeriti comuni
const SUGGESTED_PATHS = [
  {
    path: '/tmp/test_docs_pdf',
    label: 'Test PDF (locale)',
    type: 'local',
    description: 'Directory di test locale',
  },
  {
    path: '/mnt/archivio/documenti',
    label: 'Archivio Documenti',
    type: 'mounted',
    description: 'Archivio principale MyGest',
  },
  {
    path: '/mnt/mycloud',
    label: 'My Cloud',
    type: 'mounted',
    description: 'Cloud storage montato',
  },
  {
    path: '/home/sandro/mygest/media',
    label: 'Media MyGest',
    type: 'local',
    description: 'Directory media applicazione',
  },
  {
    path: '//192.168.1.100/documenti',
    label: 'NAS Documenti',
    type: 'nas',
    description: 'Server NAS - Share documenti',
  },
  {
    path: '//nas.ufficio.local/archivio',
    label: 'NAS Archivio',
    type: 'nas',
    description: 'Archivio aziendale NAS',
  },
  {
    path: '\\\\SERVER-01\\Condivisa\\Documenti',
    label: 'Server Windows',
    type: 'windows',
    description: 'Server Windows condiviso',
  },
  {
    path: '/mnt/c/Users/Documenti',
    label: 'Windows C: (WSL)',
    type: 'mounted',
    description: 'Disco C: Windows via WSL',
  },
];

/**
 * Determina il tipo di percorso
 */
const getPathType = (path: string): 'local' | 'nas' | 'windows' | 'mounted' | 'unknown' => {
  if (!path) return 'unknown';
  
  // Windows UNC path: \\SERVER\share
  if (path.startsWith('\\\\')) return 'windows';
  
  // NAS/SMB Unix-style: //server/share
  if (path.startsWith('//')) return 'nas';
  
  // Mounted NAS
  if (path.startsWith('/mnt/')) return 'mounted';
  
  // Local Linux path
  if (path.startsWith('/')) return 'local';
  
  return 'unknown';
};

/**
 * Icona in base al tipo di percorso
 */
const getPathIcon = (type: string) => {
  switch (type) {
    case 'nas':
      return <StorageIcon fontSize="small" color="primary" />;
    case 'windows':
      return <ComputerIcon fontSize="small" color="secondary" />;
    case 'mounted':
      return <StorageIcon fontSize="small" color="success" />;
    case 'local':
      return <FolderIcon fontSize="small" color="action" />;
    default:
      return <FolderOpenIcon fontSize="small" color="disabled" />;
  }
};

/**
 * Validazione percorso
 */
const validatePath = (path: string): { valid: boolean; message?: string } => {
  if (!path || path.trim() === '') {
    return { valid: false, message: 'Percorso richiesto' };
  }

  const trimmed = path.trim();
  const type = getPathType(trimmed);

  // Windows UNC: deve avere almeno \\SERVER\share
  if (type === 'windows') {
    const parts = trimmed.split('\\').filter(p => p);
    if (parts.length < 2) {
      return { valid: false, message: 'Formato Windows invalido. Esempio: \\\\SERVER\\share\\folder' };
    }
  }

  // NAS Unix: deve avere almeno //server/share
  if (type === 'nas') {
    const parts = trimmed.replace('//', '').split('/').filter(p => p);
    if (parts.length < 2) {
      return { valid: false, message: 'Formato NAS invalido. Esempio: //192.168.1.100/share/folder' };
    }
  }

  // Local path: deve iniziare con /
  if (type === 'local' && !trimmed.startsWith('/')) {
    return { valid: false, message: 'Percorso locale deve iniziare con /' };
  }

  // Caratteri non validi (minimo controllo)
  if (trimmed.includes('..') || trimmed.includes('//./')) {
    return { valid: false, message: 'Percorso contiene sequenze non valide (.., //./)' };
  }

  return { valid: true };
};

export const DirectoryPicker: React.FC<DirectoryPickerProps> = ({
  value,
  onChange,
  error,
  helperText,
  label = 'Percorso Directory',
  required = true,
}) => {
  const [inputValue, setInputValue] = useState(value);
  const [browserOpen, setBrowserOpen] = useState(false);
  const pathType = getPathType(value);
  const validation = validatePath(value);

  const handleChange = (newValue: string) => {
    setInputValue(newValue);
    onChange(newValue);
  };

  const handleBrowseSelect = (path: string) => {
    handleChange(path);
  };

  return (
    <Box>
      <Box display="flex" gap={1} alignItems="flex-start">
        <Box flex={1}>
          <Autocomplete
            freeSolo
            value={value}
            inputValue={inputValue}
            onInputChange={(_, newInputValue) => {
              setInputValue(newInputValue);
            }}
            onChange={(_, newValue) => {
              if (typeof newValue === 'string') {
                handleChange(newValue);
              } else if (newValue) {
                handleChange(newValue.path);
              }
            }}
            options={SUGGESTED_PATHS}
            getOptionLabel={(option) =>
              typeof option === 'string' ? option : option.path
            }
            renderOption={(props, option) => (
              <Box component="li" {...props}>
                <Box display="flex" alignItems="center" gap={1} width="100%">
                  {getPathIcon(option.type)}
                  <Box flex={1}>
                    <Typography variant="body2">{option.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.path}
                    </Typography>
                  </Box>
                  <Chip
                    label={option.type.toUpperCase()}
                    size="small"
                    variant="outlined"
                    color={
                      option.type === 'nas' ? 'primary' :
                      option.type === 'windows' ? 'secondary' :
                      option.type === 'mounted' ? 'success' :
                      'default'
                    }
                  />
                </Box>
              </Box>
            )}
            renderInput={(params) => (
              <TextField
                {...params}
                label={label}
                required={required}
                error={error || !validation.valid}
                helperText={
                  helperText ||
                  validation.message ||
                  (value && `Tipo: ${pathType.toUpperCase()}`)
                }
                InputProps={{
                  ...params.InputProps,
                  startAdornment: (
                    <InputAdornment position="start">
                      {getPathIcon(pathType)}
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <>
                      {params.InputProps.endAdornment}
                      <Tooltip
                        title={
                          <Box>
                            <Typography variant="caption" display="block" gutterBottom>
                              <strong>Formati supportati:</strong>
                            </Typography>
                            <Typography variant="caption" display="block">
                              • Linux locale: <code>/home/user/documenti</code>
                            </Typography>
                            <Typography variant="caption" display="block">
                              • NAS/SMB Unix: <code>//192.168.1.100/share/folder</code>
                            </Typography>
                            <Typography variant="caption" display="block">
                              • Windows UNC: <code>\\SERVER\share\folder</code>
                            </Typography>
                            <Typography variant="caption" display="block">
                              • NAS montato: <code>/mnt/nas/documenti</code>
                            </Typography>
                          </Box>
                        }
                        arrow
                        placement="left"
                      >
                        <IconButton size="small" edge="end">
                          <InfoIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </>
                  ),
                }}
              />
            )}
          />
        </Box>
        
        {/* Pulsante Sfoglia */}
        <Button
          variant="outlined"
          startIcon={<BrowseIcon />}
          onClick={() => setBrowserOpen(true)}
          sx={{ mt: 0, height: '56px' }}
        >
          Sfoglia
        </Button>
      </Box>

      {/* Info chip per tipo percorso corrente */}
      {value && validation.valid && (
        <Box mt={1}>
          <Chip
            icon={getPathIcon(pathType)}
            label={`Percorso ${pathType.toUpperCase()} valido`}
            size="small"
            color={
              pathType === 'nas' ? 'primary' :
              pathType === 'windows' ? 'secondary' :
              pathType === 'mounted' ? 'success' :
              'default'
            }
            variant="outlined"
          />
        </Box>
      )}

      {/* Directory Browser Dialog */}
      <DirectoryBrowser
        open={browserOpen}
        onClose={() => setBrowserOpen(false)}
        onSelect={handleBrowseSelect}
        initialPath={value}
        title="Seleziona Directory da Classificare"
      />
    </Box>
  );
};
