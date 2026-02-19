/**
 * Selettore Autocomplete per Unità Fisiche
 */
import React, { useState, useEffect } from 'react';
import {
  TextField,
  Autocomplete,
  Box,
  Typography,
} from '@mui/material';
import { getUnitaFisiche, getUnitaFisica } from '../../api/archivioFisico';
import type { UnitaFisica } from '../../types/archivioFisico';

interface UnitaFisicaSelectorProps {
  value?: number | null;
  onChange: (id: number | null) => void;
  disabled?: boolean;
  label?: string;
  helperText?: string;
  error?: boolean;
}

const UnitaFisicaSelector: React.FC<UnitaFisicaSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  label = 'Unità Fisica',
  helperText,
  error = false,
}) => {
  const [options, setOptions] = useState<UnitaFisica[]>([]);
  const [loading, setLoading] = useState(false);

  // Carica tutte le unità fisiche attive all'avvio
  useEffect(() => {
    const fetchOptions = async () => {
      setLoading(true);
      try {
        const data = await getUnitaFisiche({ attivo: true });
        // Gestisce sia array diretto che risposta paginata
        const results = Array.isArray(data) ? data : ((data as any)?.results || []);
        setOptions(results);
      } catch (error) {
        console.error('Errore caricamento unità fisiche:', error);
        setOptions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchOptions();
  }, []); // Carica una sola volta all'avvio

  // Se c'è un value ma non è nelle opzioni, caricalo separatamente
  useEffect(() => {
    if (value && options.length > 0 && !options.find(opt => opt.id === value)) {
      const fetchSingleOption = async () => {
        try {
          const unita = await getUnitaFisica(value);
          setOptions(prev => [...prev, unita]);
        } catch (error) {
          console.error('Errore caricamento unità singola:', error);
        }
      };
      fetchSingleOption();
    }
  }, [value, options]);

  const getOptionLabel = (option: UnitaFisica) => {
    return `${option.codice} - ${option.nome} (${option.tipo_display})`;
  };

  const selectedOption = options.find(opt => opt.id === value) || null;

  return (
    <Autocomplete
      options={options}
      getOptionLabel={getOptionLabel}
      value={selectedOption}
      onChange={(_, newValue) => {
        onChange(newValue?.id || null);
      }}
      loading={loading}
      disabled={disabled}
      // Abilita il filtro lato client invece di usare onInputChange
      filterOptions={(options, state) => {
        const inputValue = state.inputValue.toLowerCase();
        if (!inputValue) return options;
        
        return options.filter(option => {
          const label = getOptionLabel(option).toLowerCase();
          const fullPath = option.full_path.toLowerCase();
          return label.includes(inputValue) || fullPath.includes(inputValue);
        });
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          size="small"
          fullWidth
          helperText={helperText}
          error={error}
        />
      )}
      renderOption={(props, option) => (
        <Box component="li" {...props}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body2">
              {option.codice} - {option.nome}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {option.full_path}
            </Typography>
          </Box>
        </Box>
      )}
      isOptionEqualToValue={(option, value) => option.id === value.id}
      noOptionsText={loading ? "Caricamento..." : "Nessuna unità trovata"}
    />
  );
};

export default UnitaFisicaSelector;
