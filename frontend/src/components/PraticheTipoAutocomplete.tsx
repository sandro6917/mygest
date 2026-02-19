/**
 * PraticheTipoAutocomplete Component
 * Autocomplete per la selezione del tipo pratica
 */
import { useState, useEffect, useRef } from 'react';
import { praticheApi } from '@/api/pratiche';
import type { PraticheTipo } from '@/types/pratica';
import { AutocompletePortal, type AutocompletePortalRef } from './AutocompletePortal';

interface PraticheTipoAutocompleteProps {
  value: number | null;
  onChange: (tipoId: number | null) => void;
  disabled?: boolean;
  placeholder?: string;
  required?: boolean;
}

export function PraticheTipoAutocomplete({ 
  value, 
  onChange, 
  disabled = false,
  placeholder = "Cerca tipo pratica...",
  required = false
}: PraticheTipoAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [tipi, setTipi] = useState<PraticheTipo[]>([]);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const portalRef = useRef<AutocompletePortalRef>(null);

  // Carica i tipi pratica
  useEffect(() => {
    let isActive = true;

    void (async () => {
      try {
        setLoading(true);
        const tipiData = await praticheApi.listTipi();
        if (isActive) {
          setTipi(tipiData);
        }
      } catch (err) {
        console.error('Errore caricamento tipi pratica:', err);
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    })();

    return () => {
      isActive = false;
    };
  }, []);

  const selectedTipo = tipi.find(t => t.id === value);

  // Chiudi dropdown quando si clicca fuori
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      
      // Non chiudere se il click è sul wrapper o sul portal
      if (wrapperRef.current && wrapperRef.current.contains(target)) {
        return;
      }
      
      if (portalRef.current?.portalElement?.contains(target)) {
        return;
      }
      
      setIsOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filtra risultati in base al termine di ricerca
  const filteredTipi = searchTerm.length > 0
    ? tipi.filter(tipo => {
        const searchLower = searchTerm.toLowerCase();
        return tipo.nome.toLowerCase().includes(searchLower) ||
               tipo.codice.toLowerCase().includes(searchLower);
      })
    : tipi;

  const handleSelect = (tipo: PraticheTipo) => {
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
            backgroundColor: '#f0f9ff',
            border: '1px solid #3b82f6',
            borderRadius: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <strong>{selectedTipo.nome}</strong>
              <div style={{ fontSize: '0.85em', color: '#6b7280', marginTop: '0.15rem' }}>
                Codice: {selectedTipo.codice}
              </div>
            </div>
            {!disabled && (
              <button 
                type="button"
                onClick={handleClear}
                style={{ 
                  padding: '0.25rem 0.5rem',
                  fontSize: '0.875rem',
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#6b7280'
                }}
              >
                ✕
              </button>
            )}
          </div>
        ) : (
          <input
            type="text"
            value={searchTerm}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            disabled={disabled || loading}
            placeholder={loading ? 'Caricamento...' : placeholder}
            required={required}
            className="form-control"
            style={{ flex: 1 }}
          />
        )}
      </div>

      {/* Dropdown */}
      <AutocompletePortal ref={portalRef} isOpen={isOpen && !disabled} anchorRef={wrapperRef}>
        {loading ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
            Caricamento...
          </div>
        ) : filteredTipi.length > 0 ? (
          filteredTipi.map(tipo => (
            <div
              key={tipo.id}
              onClick={() => handleSelect(tipo)}
              style={{
                padding: '0.75rem',
                cursor: 'pointer',
                borderBottom: '1px solid #f3f4f6'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f9fafb';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div style={{ fontWeight: 500 }}>{tipo.nome}</div>
              <div style={{ fontSize: '0.85em', color: '#6b7280', marginTop: '0.15rem' }}>
                Codice: {tipo.codice}
              </div>
            </div>
          ))
        ) : (
          <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
            Nessun tipo pratica trovato
          </div>
        )}
      </AutocompletePortal>
    </div>
  );
}
