/**
 * Autocomplete per selezionare documenti con file allegato
 */
import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { documentiApi } from '@/api/documenti';
import type { Documento } from '@/types/documento';

interface DocumentoAutocompleteProps {
  value: number | null;
  onChange: (documentoId: number | null) => void;
  disabled?: boolean;
}

export const DocumentoAutocomplete = ({ value, onChange, disabled = false }: DocumentoAutocompleteProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Query per cercare documenti con file
  const { data: documentiResponse, isLoading } = useQuery({
    queryKey: ['documenti-search', searchTerm],
    queryFn: () => documentiApi.list({ search: searchTerm, digitale: true }, 1, 20),
    enabled: searchTerm.length > 2,
  });

  const documenti = documentiResponse?.results || [];

  // Query per documento selezionato (per mostrare il valore corrente)
  const { data: selectedDocumento } = useQuery({
    queryKey: ['documento', value],
    queryFn: () => documentiApi.get(value!),
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

  const handleSelect = (documento: Documento) => {
    onChange(documento.id);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setSearchTerm('');
  };

  const displayValue = selectedDocumento 
    ? `${selectedDocumento.descrizione || 'Senza descrizione'} (ID: ${selectedDocumento.id})`
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
          placeholder="Cerca documento per descrizione..."
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
          {!isLoading && documenti.length === 0 && (
            <div className="autocomplete-item" style={{ padding: '8px', color: '#666' }}>
              Nessun documento trovato
            </div>
          )}
          {!isLoading &&
            documenti.map((doc) => (
              <div
                key={doc.id}
                className="autocomplete-item"
                style={{
                  padding: '8px',
                  cursor: 'pointer',
                  borderBottom: '1px solid #eee',
                }}
                onClick={() => handleSelect(doc)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f0f0f0';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'white';
                }}
              >
                <div style={{ fontWeight: 'bold' }}>
                  {doc.descrizione || 'Senza descrizione'}
                </div>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  ID: {doc.id} | Codice: {doc.codice}
                  {doc.file && ' | Con file'}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
};
