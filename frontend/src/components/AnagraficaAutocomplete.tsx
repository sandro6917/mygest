import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '@/api/client';
import type { AnagraficaList } from '@/types/anagrafiche';

export type AnagraficaOption = Pick<
  AnagraficaList,
  'id' | 'display_name' | 'codice_fiscale' | 'partita_iva' | 'email' | 'pec' | 'telefono' | 'tipo'
>;

interface AnagraficaAutocompleteProps {
  value: AnagraficaOption | null;
  onChange: (value: AnagraficaOption | null) => void;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
  helperText?: string;
}

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 250;

export function AnagraficaAutocomplete({
  value,
  onChange,
  disabled = false,
  required = false,
  placeholder = 'Cerca anagrafica per nome, CF o P.IVA...',
  helperText,
}: AnagraficaAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<AnagraficaOption[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const mapResults = useCallback((data: unknown): AnagraficaOption[] => {
    if (Array.isArray(data)) {
      return data as AnagraficaOption[];
    }
    if (
      data &&
      typeof data === 'object' &&
      Array.isArray((data as { results?: unknown }).results)
    ) {
      return (data as { results: AnagraficaOption[] }).results;
    }
    return [];
  }, []);

  const performSearch = useCallback(
    async (term: string) => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get('/anagrafiche/', {
          params: {
            search: term || undefined,
            page_size: PAGE_SIZE,
            ordering: 'nominativo',
          },
        });
        setResults(mapResults(response.data));
      } catch (err) {
        console.error('Errore caricamento anagrafiche:', err);
        setError('Errore nel caricamento delle anagrafiche');
      } finally {
        setLoading(false);
      }
    },
    [mapResults]
  );

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const handler = setTimeout(() => {
      void performSearch(searchTerm);
    }, DEBOUNCE_MS);

    return () => clearTimeout(handler);
  }, [isOpen, performSearch, searchTerm]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputFocus = () => {
    if (disabled) {
      return;
    }
    setIsOpen(true);
    if (results.length === 0) {
      void performSearch('');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setIsOpen(true);
  };

  const handleSelect = (option: AnagraficaOption) => {
    onChange(option);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setSearchTerm('');
  };

  const renderOption = (option: AnagraficaOption) => (
    <div style={{ padding: '0.75rem' }}>
      <div style={{ fontWeight: 600, color: '#111827' }}>{option.display_name}</div>
      <div style={{ fontSize: '0.85rem', color: '#6b7280', marginTop: '0.25rem' }}>
        {option.tipo === 'PG' ? 'Persona Giuridica' : 'Persona Fisica'}
        {option.codice_fiscale && ` • CF ${option.codice_fiscale}`}
        {option.partita_iva && ` • P.IVA ${option.partita_iva}`}
      </div>
      {(option.email || option.pec || option.telefono) && (
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.15rem' }}>
          {option.email && `✉️ ${option.email}`}
          {option.pec && ` • PEC ${option.pec}`}
          {option.telefono && ` • ☎️ ${option.telefono}`}
        </div>
      )}
    </div>
  );

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        {value ? (
          <div
            style={{
              flex: 1,
              padding: '0.5rem',
              backgroundColor: '#ecfccb',
              border: '1px solid #84cc16',
              borderRadius: '4px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, color: '#365314' }}>{value.display_name}</div>
              <div style={{ fontSize: '0.85rem', color: '#4b5563', marginTop: '0.15rem' }}>
                {value.codice_fiscale && `CF ${value.codice_fiscale}`}
                {value.partita_iva && ` • P.IVA ${value.partita_iva}`}
              </div>
            </div>
            {!disabled && (
              <button
                type="button"
                onClick={handleClear}
                className="btn btn-sm btn-danger"
                style={{ padding: '0.25rem 0.5rem', marginLeft: '0.5rem' }}
              >
                ✕
              </button>
            )}
          </div>
        ) : (
          <input
            type="text"
            className="form-control"
            value={searchTerm}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            placeholder={placeholder}
            disabled={disabled}
            required={required}
          />
        )}
      </div>

      {helperText && (
        <small className="form-help" style={{ display: 'block', marginTop: '0.25rem' }}>
          {helperText}
        </small>
      )}

      {isOpen && !value && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: 'white',
            border: '1px solid #ddd',
            borderRadius: '4px',
            marginTop: '0.25rem',
            maxHeight: '360px',
            overflowY: 'auto',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            zIndex: 1000,
          }}
        >
          {loading && (
            <div style={{ padding: '0.75rem', textAlign: 'center', color: '#6b7280' }}>
              Caricamento...
            </div>
          )}

          {!loading && error && (
            <div style={{ padding: '0.75rem', textAlign: 'center', color: '#dc2626' }}>
              {error}
            </div>
          )}

          {!loading && !error && results.length === 0 && (
            <div style={{ padding: '0.75rem', textAlign: 'center', color: '#9ca3af' }}>
              Nessuna anagrafica trovata
            </div>
          )}

          {!loading && !error && results.length > 0 &&
            results.map((option) => (
              <div
                key={option.id}
                onClick={() => handleSelect(option)}
                style={{ borderBottom: '1px solid #f0f0f0', cursor: 'pointer' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f9fafb';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'white';
                }}
              >
                {renderOption(option)}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
