/**
 * Selettore intelligente per Documenti e Fascicoli
 * Filtra in base al tipo di operazione e referente esterno
 */
import React, { useState, useEffect } from 'react';
import {
  TextField,
  Autocomplete,
  Box,
  Typography,
} from '@mui/material';
import { getDocumentiTracciabili, getFascicoliTracciabili } from '../../api/archivioFisico';
import type { DocumentoTracciabile, FascicoloTracciabile, TipoOperazioneArchivio } from '../../types/archivioFisico';

interface DocumentoFascicoloSelectorProps {
  tipo: 'documento' | 'fascicolo';
  tipoOperazione: TipoOperazioneArchivio;
  referenteEsterno?: number | null;
  value?: number | null;
  onChange: (id: number | null, oggetto?: DocumentoTracciabile | FascicoloTracciabile) => void;
  disabled?: boolean;
}

const DocumentoFascicoloSelector: React.FC<DocumentoFascicoloSelectorProps> = ({
  tipo,
  tipoOperazione,
  referenteEsterno,
  value,
  onChange,
  disabled = false,
}) => {
  const [options, setOptions] = useState<(DocumentoTracciabile | FascicoloTracciabile)[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);

  // Determina lo stato richiesto in base al tipo di operazione
  const getStatoOperazione = (): 'latenti' | 'in_giacenza' | 'scaricati' | undefined => {
    if (tipoOperazione === 'entrata') {
      // Per entrate: oggetti latenti o scaricati
      return inputValue ? undefined : 'latenti'; // Mostra prima i latenti, poi cerca tra tutti
    } else if (tipoOperazione === 'uscita' || tipoOperazione === 'interna') {
      // Per uscite e interni: solo oggetti in giacenza
      return 'in_giacenza';
    }
    return undefined;
  };

  useEffect(() => {
    const fetchOptions = async () => {
      if (!inputValue && !referenteEsterno) {
        setOptions([]);
        return;
      }

      setLoading(true);
      try {
        const statoOp = getStatoOperazione();
        
        let data;
        if (tipo === 'documento') {
          data = await getDocumentiTracciabili(inputValue, referenteEsterno || undefined, statoOp);
        } else {
          data = await getFascicoliTracciabili(inputValue, referenteEsterno || undefined, statoOp);
        }
        
        // Gestisce sia array diretto che risposta paginata
        const results = Array.isArray(data) ? data : ((data as any)?.results || []);
        setOptions(results);
      } catch (error) {
        console.error(`Errore caricamento ${tipo}:`, error);
        setOptions([]);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(fetchOptions, 300);
    return () => clearTimeout(debounceTimer);
  }, [inputValue, tipo, tipoOperazione, referenteEsterno]);

  const getOptionLabel = (option: DocumentoTracciabile | FascicoloTracciabile) => {
    if ('descrizione' in option) {
      return `${option.codice} - ${option.descrizione}`;
    } else {
      return `${option.codice} - ${option.titolo}`;
    }
  };

  const getHelperText = () => {
    if (!referenteEsterno) {
      return 'Seleziona prima un referente esterno';
    }
    
    if (tipoOperazione === 'entrata') {
      return 'Mostra oggetti senza operazioni o scaricati';
    } else if (tipoOperazione === 'uscita') {
      return 'Mostra solo oggetti in giacenza';
    } else {
      return 'Mostra solo oggetti in giacenza (movimento interno)';
    }
  };

  const selectedOption = options.find(opt => opt.id === value) || null;

  return (
    <Autocomplete
      options={options}
      getOptionLabel={getOptionLabel}
      value={selectedOption}
      onChange={(_, newValue) => {
        onChange(newValue?.id || null, newValue || undefined);
      }}
      onInputChange={(_, newInputValue) => {
        setInputValue(newInputValue);
      }}
      loading={loading}
      disabled={disabled || !referenteEsterno}
      renderInput={(params) => (
        <TextField
          {...params}
          label={tipo === 'documento' ? 'Documento' : 'Fascicolo'}
          size="small"
          fullWidth
          helperText={getHelperText()}
          error={!referenteEsterno}
        />
      )}
      renderOption={(props, option) => (
        <Box component="li" {...props}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body2">
              {getOptionLabel(option)}
            </Typography>
            {'tipo_nome' in option && (
              <Typography variant="caption" color="text.secondary">
                Tipo: {option.tipo_nome} | Stato: {option.stato_display}
              </Typography>
            )}
            {'anno' in option && (
              <Typography variant="caption" color="text.secondary">
                Anno: {option.anno} | Stato: {option.stato_display}
              </Typography>
            )}
          </Box>
        </Box>
      )}
      isOptionEqualToValue={(option, value) => option.id === value.id}
      noOptionsText={
        !referenteEsterno 
          ? "Seleziona prima un referente esterno"
          : loading 
            ? "Caricamento..." 
            : "Nessun elemento trovato con i filtri applicati"
      }
    />
  );
};

export default DocumentoFascicoloSelector;
