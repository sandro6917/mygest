import { useState, useEffect, useRef } from 'react';

interface TitolarioVoce {
  id: number;
  codice: string;
  titolo: string;
  pattern_codice?: string;
  anagrafica_nome?: string;
  is_voce_intestata?: boolean;
}

interface TitolarioAutocompleteProps {
  value: number | null;
  voci: TitolarioVoce[];
  onChange: (voceId: number | null) => void;
  disabled?: boolean;
  placeholder?: string;
  required?: boolean;
}

export function TitolarioAutocomplete({ 
  value, 
  voci,
  onChange, 
  disabled = false,
  placeholder = "Cerca voce di titolario...",
  required = false
}: TitolarioAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const selectedVoce = voci.find(v => v.id === value);

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

  // Filter results based on search term
  const filteredVoci = searchTerm.length > 0
    ? voci.filter(voce => 
        voce.codice.toLowerCase().includes(searchTerm.toLowerCase()) ||
        voce.titolo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (voce.anagrafica_nome && voce.anagrafica_nome.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    : voci;

  const handleSelect = (voce: TitolarioVoce) => {
    onChange(voce.id);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setSearchTerm('');
  };

  const handleChange = () => {
    setSearchTerm('');
    setIsOpen(true);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setIsOpen(true);
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        {selectedVoce ? (
          <div style={{ 
            flex: 1, 
            padding: '0.5rem',
            backgroundColor: '#e3f2fd',
            border: '1px solid #2196f3',
            borderRadius: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <strong>{selectedVoce.codice}</strong> - {selectedVoce.titolo}
              {selectedVoce.anagrafica_nome && (
                <span style={{ marginLeft: '0.5rem', color: '#1976d2', fontStyle: 'italic' }}>
                  ({selectedVoce.anagrafica_nome})
                </span>
              )}
            </div>
            {!disabled && (
              <div style={{ display: 'flex', gap: '0.25rem' }}>
                <button
                  type="button"
                  onClick={handleChange}
                  className="btn btn-sm btn-primary"
                  style={{ padding: '0.25rem 0.5rem' }}
                  title="Cambia titolario"
                >
                  Cambia
                </button>
                {!required && (
                  <button
                    type="button"
                    onClick={handleClear}
                    className="btn btn-sm btn-danger"
                    style={{ padding: '0.25rem 0.5rem' }}
                    title="Rimuovi titolario"
                  >
                    ✕
                  </button>
                )}
              </div>
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

      {isOpen && filteredVoci.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: 'white',
          border: '1px solid #ddd',
          borderRadius: '4px',
          marginTop: '0.25rem',
          maxHeight: '400px',
          overflowY: 'auto',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 1000
        }}>
          {filteredVoci.length > 0 ? (
            filteredVoci.map((voce) => (
              <div
                key={voce.id}
                onClick={() => handleSelect(voce)}
                style={{
                  padding: '0.75rem',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f0f0f0'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
              >
                <div style={{ fontWeight: 'bold', color: '#2563eb' }}>
                  {voce.codice}
                  {voce.anagrafica_nome && (
                    <span style={{ marginLeft: '0.5rem', fontWeight: 'normal', color: '#1976d2', fontStyle: 'italic' }}>
                      ({voce.anagrafica_nome})
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '0.9em', color: '#374151', marginTop: '0.25rem' }}>
                  {voce.titolo}
                </div>
              </div>
            ))
          ) : (
            <div style={{ padding: '0.75rem', textAlign: 'center', color: '#9ca3af' }}>
              Nessuna voce trovata
            </div>
          )}
        </div>
      )}

      {isOpen && searchTerm.length > 0 && filteredVoci.length === 0 && (
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
          color: '#9ca3af',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 1000
        }}>
          Nessuna voce trovata per "{searchTerm}"
        </div>
      )}
    </div>
  );
}
