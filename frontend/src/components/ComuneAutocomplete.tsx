import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';

interface ComuneItaliano {
  id: number;
  nome: string;
  provincia: string;
  cap: string;
  denominazione_completa: string;
}

interface ComuneAutocompleteProps {
  value: ComuneItaliano | null;
  onChange: (comune: ComuneItaliano | null) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ComuneAutocomplete({ 
  value, 
  onChange, 
  disabled = false,
  placeholder = "Cerca comune..." 
}: ComuneAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<ComuneItaliano[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (searchTerm.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.get('/comuni/', {
          params: { search: searchTerm }
        });
        setResults(response.data.results || response.data);
        setIsOpen(true);
      } catch (error) {
        console.error('Errore ricerca comuni:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleSelect = (comune: ComuneItaliano) => {
    onChange(comune);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setSearchTerm('');
    setResults([]);
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        {value ? (
          <div style={{ 
            flex: 1, 
            padding: '0.5rem',
            backgroundColor: '#e8f5e9',
            border: '1px solid #4caf50',
            borderRadius: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <strong>{value.nome}</strong> ({value.provincia}) - {value.cap}
            </div>
            {!disabled && (
              <button
                onClick={handleClear}
                className="btn btn-sm btn-danger"
                style={{ padding: '0.25rem 0.5rem' }}
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
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
          />
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: 'white',
          border: '1px solid #ddd',
          borderRadius: '4px',
          marginTop: '0.25rem',
          maxHeight: '300px',
          overflowY: 'auto',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 1000
        }}>
          {results.map((comune) => (
            <div
              key={comune.id}
              onClick={() => handleSelect(comune)}
              style={{
                padding: '0.75rem',
                cursor: 'pointer',
                borderBottom: '1px solid #f0f0f0'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
            >
              <div style={{ fontWeight: 'bold' }}>
                {comune.nome} ({comune.provincia})
              </div>
              <div style={{ fontSize: '0.9em', color: '#666' }}>
                CAP: {comune.cap}
              </div>
            </div>
          ))}
        </div>
      )}

      {isLoading && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: 'white',
          border: '1px solid #ddd',
          borderRadius: '4px',
          marginTop: '0.25rem',
          padding: '0.75rem',
          textAlign: 'center',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 1000
        }}>
          Caricamento...
        </div>
      )}
    </div>
  );
}
