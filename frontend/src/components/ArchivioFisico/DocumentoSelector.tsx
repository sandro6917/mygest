/**
 * Componente per selezionare un documento tracciabile
 */
import React, { useState, useEffect } from 'react';
import { Autocomplete, TextField, CircularProgress, Box, Typography, Chip } from '@mui/material';
import { debounce } from 'lodash';

import { getDocumentiTracciabili } from '../../api/archivioFisico';
import type { DocumentoTracciabile } from '../../types/archivioFisico';

interface DocumentoSelectorProps {
  value: DocumentoTracciabile | null;
  onChange: (documento: DocumentoTracciabile | null) => void;
  label?: string;
  required?: boolean;
  disabled?: boolean;
}

const DocumentoSelector: React.FC<DocumentoSelectorProps> = ({
  value,
  onChange,
  label = 'Documento',
  required = false,
  disabled = false,
}) => {
  const [options, setOptions] = useState<DocumentoTracciabile[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const searchDocumenti = async (searchTerm: string) => {
    if (!searchTerm || searchTerm.length < 2) {
      setOptions([]);
      return;
    }

    try {
      setLoading(true);
      const results = await getDocumentiTracciabili(searchTerm);
      setOptions(results);
    } catch (err) {
      console.error('Errore ricerca documenti:', err);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  const debouncedSearch = debounce(searchDocumenti, 300);

  useEffect(() => {
    debouncedSearch(inputValue);
  }, [inputValue]);

  return (
    <Autocomplete
      value={value}
      onChange={(_, newValue) => onChange(newValue)}
      inputValue={inputValue}
      onInputChange={(_, newInputValue) => setInputValue(newInputValue)}
      options={options}
      loading={loading}
      disabled={disabled}
      getOptionLabel={(option) => `${option.codice} - ${option.descrizione}`}
      isOptionEqualToValue={(option, value) => option.id === value.id}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          required={required}
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={20} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
          helperText="Digita almeno 2 caratteri per cercare"
        />
      )}
      renderOption={(props, option) => (
        <Box component="li" {...props}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body1">
              <strong>{option.codice}</strong> - {option.tipo_nome}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {option.descrizione}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Chip label={option.stato_display} size="small" />
              {option.tracciabile && <Chip label="Tracciabile" size="small" color="success" />}
            </Box>
          </Box>
        </Box>
      )}
      noOptionsText={
        inputValue.length < 2
          ? 'Digita almeno 2 caratteri'
          : 'Nessun documento trovato'
      }
    />
  );
};

export default DocumentoSelector;
