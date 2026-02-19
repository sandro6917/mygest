/**
 * Autocomplete per selezionare fascicoli con documenti allegati
 */
import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fascicoliApi } from '@/api/fascicoli';

interface FascicoloAutocompleteProps {
  value: number | null;
  onChange: (fascicoloId: number | null) => void;
  disabled?: boolean;
}

export const FascicoloAutocomplete = ({ value, onChange, disabled = false }: FascicoloAutocompleteProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Query per cercare fascicoli con documenti con file
  const { data: fascicoliResponse, isLoading } = useQuery({
    queryKey: ['fascicoli-search', searchTerm],
    queryFn: () => fascicoliApi.list({ search: searchTerm, page: 1, page_size: 20, con_file: 'true' }),
    enabled: searchTerm.length > 2,
  });

  const fascicoli = fascicoliResponse?.results || [];

  // Query per fascicolo selezionato (per mostrare il valore corrente)
  const { data: selectedFascicolo } = useQuery({
    queryKey: ['fascicolo', value],
    queryFn: () => fascicoliApi.get(value!),
    enabled: !!value,
  });

  // Chiudi dropdown quando si clicca fuori
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (fascicolo: any) => {
    onChange(fascicolo.id);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setSearchTerm('');
  };

  const displayValue = selectedFascicolo 
    ? `${selectedFascicolo.codice} - ${selectedFascicolo.titolo} (ID: ${selectedFascicolo.id})`
    : '';

  return (
    <div ref={wrapperRef} className="autocomplete-wrapper" style={{ position: 'relative' }}>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          className="form-control"
          value={isOpen ? searchTerm : displayValue}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder="Cerca fascicolo per codice o titolo..."
          disabled={disabled}
        />
        {value && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleClear}
            disabled={disabled}
          >
            ×
          </button>
        )}
      </div>

      {isOpen && searchTerm.length > 2 && (
        <div
          className="autocomplete-dropdown"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: 'white',
            border: '1px solid #ccc',
            borderRadius: '4px',
            maxHeight: '200px',
            overflowY: 'auto',
            zIndex: 1000,
            marginTop: '4px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          {isLoading && (
            <div className="autocomplete-item" style={{ padding: '8px' }}>
              Caricamento...
            </div>
          )}
          {!isLoading && fascicoli.length === 0 && (
            <div className="autocomplete-item" style={{ padding: '8px', color: '#666' }}>
              Nessun fascicolo trovato
            </div>
          )}
          {!isLoading &&
            fascicoli.map((fasc) => (
              <div
                key={fasc.id}
                className="autocomplete-item"
                style={{
                  padding: '8px',
                  cursor: 'pointer',
                  borderBottom: '1px solid #eee',
                }}
                onClick={() => handleSelect(fasc)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f0f0f0';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'white';
                }}
              >
                <div style={{ fontWeight: 'bold' }}>
                  {fasc.codice} - {fasc.titolo}
                </div>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  ID: {fasc.id} | Anno: {fasc.anno}
                  {fasc.num_pratiche !== undefined && ` | ${fasc.num_pratiche} pratiche`}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
};
