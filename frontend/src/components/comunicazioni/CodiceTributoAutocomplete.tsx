import React, { useState, useEffect, useRef } from 'react';
import { codiciTributoApi } from '../../api/comunicazioni';
import type { CodiceTributoF24 } from '../../types/comunicazioni';
import './CodiceTributoAutocomplete.css';

interface CodiceTributoAutocompleteProps {
  value: string; // ID del codice tributo selezionato
  onChange: (value: string, display?: string) => void; // Passa anche il valore display
  sezione?: string; // Opzionale: filtra per sezione
  required?: boolean;
}

const CodiceTributoAutocomplete: React.FC<CodiceTributoAutocompleteProps> = ({
  value,
  onChange,
  sezione,
  required = false,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [options, setOptions] = useState<CodiceTributoF24[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedCodice, setSelectedCodice] = useState<CodiceTributoF24 | null>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Carica il codice tributo selezionato all'avvio (solo una volta)
  useEffect(() => {
    const loadSelected = async () => {
      if (value && value !== '' && isInitialLoad) {
        try {
          const codice = await codiciTributoApi.get(parseInt(value));
          setSelectedCodice(codice);
          setInputValue(codice.display);
          setIsInitialLoad(false);
        } catch (error) {
          console.error('Errore caricamento codice tributo:', error);
          setIsInitialLoad(false);
        }
      }
    };
    loadSelected();
  }, [value, isInitialLoad]);

  // Ricerca codici tributo mentre l'utente digita
  useEffect(() => {
    const search = async () => {
      // Non cercare se l'input è vuoto o troppo corto
      if (inputValue.length < 2) {
        setOptions([]);
        setShowDropdown(false);
        return;
      }

      // Non cercare se l'input corrisponde esattamente a un codice già selezionato
      if (selectedCodice && inputValue === selectedCodice.display) {
        setShowDropdown(false);
        return;
      }

      setLoading(true);
      try {
        const results = await codiciTributoApi.search(inputValue, sezione);
        setOptions(results);
        setShowDropdown(results.length > 0);
      } catch (error) {
        console.error('Errore ricerca codici tributo:', error);
        setOptions([]);
        setShowDropdown(false);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(search, 300);
    return () => clearTimeout(debounceTimer);
  }, [inputValue, sezione, selectedCodice]);

  // Chiudi dropdown quando si clicca fuori
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (codice: CodiceTributoF24) => {
    setSelectedCodice(codice);
    setInputValue(codice.display);
    onChange(codice.id.toString(), codice.display); // Passa anche il display
    setShowDropdown(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    
    // Se l'utente modifica l'input e c'era una selezione, resettala
    if (selectedCodice && newValue !== selectedCodice.display) {
      setSelectedCodice(null);
      onChange(''); // Resetta senza display
    }
    
    // Se l'utente cancella l'input, resetta tutto
    if (newValue === '') {
      setSelectedCodice(null);
      onChange('');
      setOptions([]);
      setShowDropdown(false);
    } else {
      // Mostra il dropdown quando l'utente inizia a digitare
      setShowDropdown(true);
    }
  };

  const handleClear = () => {
    setInputValue('');
    setSelectedCodice(null);
    onChange('');
    setOptions([]);
    setShowDropdown(false);
    inputRef.current?.focus();
  };

  return (
    <div className="codice-tributo-autocomplete" ref={dropdownRef}>
      <div className="autocomplete-input-wrapper">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => {
            if (options.length > 0) {
              setShowDropdown(true);
            }
          }}
          placeholder="Cerca per codice, descrizione o causale..."
          className="autocomplete-input"
          required={required}
        />
        {selectedCodice && (
          <button
            type="button"
            className="autocomplete-clear-btn"
            onClick={handleClear}
            title="Cancella selezione"
          >
            ✕
          </button>
        )}
        {loading && <span className="autocomplete-loading">🔄</span>}
      </div>

      {showDropdown && options.length > 0 && (
        <ul className="autocomplete-dropdown">
          {options.map((codice) => (
            <li
              key={codice.id}
              onClick={() => handleSelect(codice)}
              className={`autocomplete-option ${
                selectedCodice?.id === codice.id ? 'selected' : ''
              }`}
            >
              <div className="option-main">
                <span className="option-codice">{codice.codice}</span>
                <span className="option-sezione">{codice.sezione}</span>
              </div>
              <div className="option-descrizione">{codice.descrizione}</div>
              {codice.causale && (
                <div className="option-causale">Causale: {codice.causale}</div>
              )}
              {!codice.attivo && (
                <div className="option-obsoleto">⚠️ Obsoleto</div>
              )}
            </li>
          ))}
        </ul>
      )}

      {showDropdown && !loading && inputValue.length >= 2 && options.length === 0 && (
        <div className="autocomplete-no-results">
          Nessun codice tributo trovato
        </div>
      )}
    </div>
  );
};

export default CodiceTributoAutocomplete;
