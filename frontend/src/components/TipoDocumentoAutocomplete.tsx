import { useState, useEffect, useRef } from 'react';

interface DocumentiTipo {
  id: number;
  codice: string;
  nome: string;
  estensioni_permesse?: string;
  pattern_codice?: string;
  attivo: boolean;
}

interface TipoDocumentoAutocompleteProps {
  value: number | null;
  tipi: DocumentiTipo[];
  onChange: (tipoId: number | null) => void;
  disabled?: boolean;
  placeholder?: string;
  required?: boolean;
}

export function TipoDocumentoAutocomplete({ 
  value, 
  tipi,
  onChange, 
  disabled = false,
  placeholder = "Cerca tipo documento...",
  required = false
}: TipoDocumentoAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const selectedTipo = tipi.find(t => t.id === value);

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

  // Filter results based on search term - filtra solo tipi attivi
  const filteredTipi = searchTerm.length > 0
    ? tipi.filter(tipo => 
        tipo.attivo && (
          tipo.codice.toLowerCase().includes(searchTerm.toLowerCase()) ||
          tipo.nome.toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    : tipi.filter(tipo => tipo.attivo);

  const handleSelect = (tipo: DocumentiTipo) => {
    onChange(tipo.id);
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
        {selectedTipo ? (
          <div style={{ 
            flex: 1, 
            padding: '0.5rem',
            backgroundColor: '#ede9fe',
            border: '1px solid #8b5cf6',
            borderRadius: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <strong>{selectedTipo.codice}</strong> - {selectedTipo.nome}
              {selectedTipo.estensioni_permesse && (
                <div style={{ fontSize: '0.85em', color: '#6b7280', marginTop: '0.15rem' }}>
                  Estensioni: {selectedTipo.estensioni_permesse}
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

      {isOpen && filteredTipi.length > 0 && (
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
          {filteredTipi.length > 0 ? (
            filteredTipi.map((tipo) => (
              <div
                key={tipo.id}
                onClick={() => handleSelect(tipo)}
                style={{
                  padding: '0.75rem',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f0f0f0'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
              >
                <div style={{ fontWeight: 'bold', color: '#7c3aed' }}>
                  {tipo.codice} - {tipo.nome}
                </div>
                {tipo.estensioni_permesse && (
                  <div style={{ fontSize: '0.85em', color: '#6b7280', marginTop: '0.25rem' }}>
                    📄 Estensioni: {tipo.estensioni_permesse}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div style={{ padding: '0.75rem', textAlign: 'center', color: '#9ca3af' }}>
              Nessun tipo documento trovato
            </div>
          )}
        </div>
      )}

      {isOpen && searchTerm.length > 0 && filteredTipi.length === 0 && (
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
          Nessun tipo documento trovato per "{searchTerm}"
        </div>
      )}
    </div>
  );
}
