import { useState, useEffect, useRef } from 'react';

export interface UbicazioneOption {
  id: number;
  tipo: string;
  codice: string;
  nome?: string;
  descrizione?: string;
  full_path?: string;
}

interface UbicazioneAutocompleteProps {
  value: number | null;
  unitaFisiche: UbicazioneOption[];
  onChange: (unitaId: number | null) => void;
  disabled?: boolean;
  placeholder?: string;
  required?: boolean;
}

export function UbicazioneAutocomplete({ 
  value, 
  unitaFisiche,
  onChange, 
  disabled = false,
  placeholder = "Cerca ubicazione...",
  required = false
}: UbicazioneAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  console.log('🔍 UbicazioneAutocomplete render:', { 
    unitaFisicheCount: unitaFisiche.length, 
    value, 
    searchTerm,
    isOpen 
  });

  const selectedUnita = unitaFisiche.find(u => u.id === value);

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
  const filteredUnita = searchTerm.length > 0
    ? unitaFisiche.filter(unita => 
        unita.codice.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (unita.nome && unita.nome.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (unita.descrizione && unita.descrizione.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (unita.full_path && unita.full_path.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    : unitaFisiche;

  console.log('🔍 Filtered results:', { 
    searchTerm, 
    totalUnita: unitaFisiche.length,
    filteredCount: filteredUnita.length,
    firstFew: filteredUnita.slice(0, 3)
  });

  const handleSelect = (unita: UbicazioneOption) => {
    onChange(unita.id);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setSearchTerm('');
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
        {selectedUnita ? (
          <div style={{ 
            flex: 1, 
            padding: '0.5rem',
            backgroundColor: '#fef3c7',
            border: '1px solid #f59e0b',
            borderRadius: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <div>
                <strong>{selectedUnita.codice}</strong>
                {selectedUnita.nome && ` - ${selectedUnita.nome}`}
              </div>
              {selectedUnita.full_path && (
                <div style={{ fontSize: '0.85em', color: '#78716c', marginTop: '0.15rem' }}>
                  {selectedUnita.full_path}
                </div>
              )}
            </div>
            {!disabled && !required && (
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

      {isOpen && filteredUnita.length > 0 && (
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
          {filteredUnita.length > 0 ? (
            filteredUnita.map((unita) => (
              <div
                key={unita.id}
                onClick={() => handleSelect(unita)}
                style={{
                  padding: '0.75rem',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f0f0f0'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
              >
                <div style={{ fontWeight: 'bold', color: '#f59e0b' }}>
                  {unita.codice}
                  {unita.nome && ` - ${unita.nome}`}
                </div>
                {unita.descrizione && unita.descrizione !== unita.nome && (
                  <div style={{ fontSize: '0.85em', color: '#6b7280', marginTop: '0.15rem' }}>
                    {unita.descrizione}
                  </div>
                )}
                {unita.full_path && (
                  <div style={{ fontSize: '0.75em', color: '#9ca3af', marginTop: '0.15rem' }}>
                    📍 {unita.full_path}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div style={{ padding: '0.75rem', textAlign: 'center', color: '#9ca3af' }}>
              Nessuna ubicazione trovata
            </div>
          )}
        </div>
      )}

      {isOpen && searchTerm.length > 0 && filteredUnita.length === 0 && (
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
          Nessuna ubicazione trovata per "{searchTerm}"
        </div>
      )}
    </div>
  );
}
