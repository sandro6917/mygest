/**
 * PraticaAutocomplete Component
 * Autocomplete per la selezione di pratiche (singola o multipla)
 */
import { useState, useEffect, useRef } from 'react';
import { apiClient } from '@/api/client';

interface Pratica {
  id: number;
  codice: string;
  oggetto: string;
  stato: string;
  stato_display: string;
  cliente_detail?: {
    anagrafica_display?: string;
  };
}

interface PraticaAutocompleteProps {
  value: number | number[] | null;
  onChange: (id: number | number[] | null) => void;
  multiple?: boolean;
  required?: boolean;
  excludeIds?: number[];
}

interface PraticheResponse {
  results: Pratica[];
}

export function PraticaAutocomplete({ 
  value, 
  onChange, 
  multiple = false,
  required = false,
  excludeIds = []
}: PraticaAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [pratiche, setPratiche] = useState<Pratica[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Carica pratiche in base al termine di ricerca
  useEffect(() => {
    if (searchTerm.length >= 2) {
      let isActive = true;
      setIsLoading(true);

      void (async () => {
        try {
          const response = await apiClient.get<PraticheResponse>(
            `/pratiche/?search=${encodeURIComponent(searchTerm)}&page_size=100`
          );
          const praticheArray = Array.isArray(response.data?.results) ? response.data.results : [];
          if (isActive) {
            setPratiche(praticheArray);
          }
        } catch (err) {
          console.error('Error loading pratiche:', err);
        } finally {
          if (isActive) {
            setIsLoading(false);
          }
        }
      })();

      return () => {
        isActive = false;
      };
    } else if (searchTerm.length === 0) {
      setPratiche([]);
    }
    return undefined;
  }, [searchTerm]);

  // Filtra pratiche escludendo quelle nell'elenco excludeIds
  const availablePratiche = pratiche.filter(p => !excludeIds.includes(p.id));

  // Chiudi dropdown quando si clicca fuori
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (pratica: Pratica) => {
    if (multiple) {
      const currentValues = Array.isArray(value) ? value : [];
      if (currentValues.includes(pratica.id)) {
        // Rimuovi se già selezionato
        onChange(currentValues.filter(id => id !== pratica.id));
      } else {
        // Aggiungi
        onChange([...currentValues, pratica.id]);
      }
    } else {
      onChange(pratica.id);
      setSearchTerm('');
      setIsOpen(false);
    }
  };

  const handleRemove = (praticaId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (multiple && Array.isArray(value)) {
      onChange(value.filter(id => id !== praticaId));
    } else {
      onChange(null);
      setSearchTerm('');
    }
  };

  // Get selected pratiche per visualizzazione
  const selectedPratiche = multiple && Array.isArray(value)
    ? pratiche.filter(p => value.includes(p.id))
    : value && typeof value === 'number'
    ? pratiche.filter(p => p.id === value)
    : [];

  const isSelected = (praticaId: number) => {
    if (multiple && Array.isArray(value)) {
      return value.includes(praticaId);
    }
    return value === praticaId;
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative', width: '100%' }}>
      {/* Chips per selezioni multiple */}
      {multiple && selectedPratiche.length > 0 && (
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: '0.5rem', 
          marginBottom: '0.5rem' 
        }}>
          {selectedPratiche.map(pratica => (
            <div
              key={pratica.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.25rem 0.75rem',
                backgroundColor: '#e0f2fe',
                border: '1px solid #0ea5e9',
                borderRadius: '9999px',
                fontSize: '0.875rem',
              }}
            >
              <span>{pratica.codice}</span>
              <button
                type="button"
                onClick={(e) => handleRemove(pratica.id, e)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#0ea5e9',
                  cursor: 'pointer',
                  padding: '0',
                  lineHeight: '1',
                  fontSize: '1.25rem',
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input di ricerca */}
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={
            multiple 
              ? "Cerca pratiche per codice o oggetto..." 
              : selectedPratiche.length > 0
              ? `${selectedPratiche[0].codice} - ${selectedPratiche[0].oggetto}`
              : "Cerca pratica per codice o oggetto..."
          }
          required={required && !value}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid #d1d5db',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
          }}
        />
        {isLoading && (
          <div
            style={{
              position: 'absolute',
              right: '0.75rem',
              top: '50%',
              transform: 'translateY(-50%)',
            }}
          >
            ⏳
          </div>
        )}
      </div>

      {/* Dropdown results */}
      {isOpen && searchTerm.length >= 2 && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 0.25rem)',
            left: 0,
            right: 0,
            backgroundColor: 'white',
            border: '1px solid #d1d5db',
            borderRadius: '0.375rem',
            maxHeight: '300px',
            overflowY: 'auto',
            zIndex: 1000,
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
        >
          {isLoading ? (
            <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
              Caricamento...
            </div>
          ) : availablePratiche.length === 0 ? (
            <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
              Nessuna pratica trovata
            </div>
          ) : (
            availablePratiche.map((pratica) => (
              <div
                key={pratica.id}
                onClick={() => handleSelect(pratica)}
                style={{
                  padding: '0.75rem',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f3f4f6',
                  backgroundColor: isSelected(pratica.id) ? '#e0f2fe' : 'white',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = isSelected(pratica.id) 
                    ? '#bae6fd' 
                    : '#f9fafb';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = isSelected(pratica.id) 
                    ? '#e0f2fe' 
                    : 'white';
                }}
              >
                <div style={{ fontWeight: 600, color: '#111827', marginBottom: '0.25rem' }}>
                  {pratica.codice}
                  {isSelected(pratica.id) && (
                    <span style={{ marginLeft: '0.5rem', color: '#0ea5e9' }}>✓</span>
                  )}
                </div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  {pratica.oggetto}
                </div>
                {pratica.cliente_detail?.anagrafica_display && (
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                    Cliente: {pratica.cliente_detail.anagrafica_display}
                  </div>
                )}
                <div style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                  <span
                    style={{
                      padding: '0.125rem 0.5rem',
                      borderRadius: '0.25rem',
                      backgroundColor: 
                        pratica.stato === 'aperta' ? '#dbeafe' :
                        pratica.stato === 'lavorazione' ? '#fef3c7' :
                        pratica.stato === 'chiusa' ? '#d1fae5' : '#f3f4f6',
                      color: 
                        pratica.stato === 'aperta' ? '#1e40af' :
                        pratica.stato === 'lavorazione' ? '#92400e' :
                        pratica.stato === 'chiusa' ? '#065f46' : '#6b7280',
                    }}
                  >
                    {pratica.stato_display}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
