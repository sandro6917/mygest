/**
 * Componente per selezionare un fascicolo
 */
import React, { useState, useEffect } from 'react';
import { Autocomplete, TextField, CircularProgress, Box, Typography, Chip } from '@mui/material';
import { debounce } from 'lodash';

import { getFascicoliTracciabili } from '../../api/archivioFisico';
import type { FascicoloTracciabile } from '../../types/archivioFisico';

interface FascicoloSelectorProps {
  value: FascicoloTracciabile | null;
  onChange: (fascicolo: FascicoloTracciabile | null) => void;
  label?: string;
  required?: boolean;
  disabled?: boolean;
}

const FascicoloSelector: React.FC<FascicoloSelectorProps> = ({
  value,
  onChange,
  label = 'Fascicolo',
  required = false,
  disabled = false,
}) => {
  const [options, setOptions] = useState<FascicoloTracciabile[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const searchFascicoli = async (searchTerm: string) => {
    if (!searchTerm || searchTerm.length < 2) {
      setOptions([]);
      return;
    }

    try {
      setLoading(true);
      const results = await getFascicoliTracciabili(searchTerm);
      setOptions(results);
    } catch (err) {
      console.error('Errore ricerca fascicoli:', err);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  const debouncedSearch = debounce(searchFascicoli, 300);

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
      getOptionLabel={(option) => `${option.codice} - ${option.titolo}`}
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
              <strong>{option.codice}</strong> - Anno {option.anno}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {option.titolo}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Chip label={option.stato_display} size="small" />
              {option.cliente_nome && (
                <Chip label={option.cliente_nome} size="small" variant="outlined" />
              )}
            </Box>
          </Box>
        </Box>
      )}
      noOptionsText={
        inputValue.length < 2
          ? 'Digita almeno 2 caratteri'
          : 'Nessun fascicolo trovato'
      }
    />
  );
};

export default FascicoloSelector;
