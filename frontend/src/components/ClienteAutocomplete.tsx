import { useState, useEffect, useRef } from 'react';
import { apiClient } from '@/api/client';
import { AutocompletePortal, type AutocompletePortalRef } from './AutocompletePortal';

interface Cliente {
  id: number;
  anagrafica?: number | {
    display_name?: string;
    ragione_sociale?: string;
    cognome?: string;
  };
  anagrafica_display?: string;
  codice_fiscale?: string;
  partita_iva?: string;
}

interface ClienteAutocompleteProps {
  value: number | null;
  clienti?: Cliente[]; // Ora opzionale - se non fornito, li carica internamente
  onChange: (clienteId: number | null) => void;
  disabled?: boolean;
  placeholder?: string;
  required?: boolean;
}

export function ClienteAutocomplete({ 
  value, 
  clienti: clientiProp,
  onChange, 
  disabled = false,
  placeholder = "Cerca cliente...",
  required = false
}: ClienteAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [clientiInternal, setClientiInternal] = useState<Cliente[]>([]);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const portalRef = useRef<AutocompletePortalRef>(null);

  // Usa clienti forniti come prop o quelli caricati internamente
  const clienti = clientiProp || clientiInternal;

  // Carica clienti se non forniti come prop
  useEffect(() => {
    if (!clientiProp) {
      let isActive = true;

      void (async () => {
        try {
          const response = await apiClient.get<Cliente[]>('/clienti/');
          const clientiArray = Array.isArray(response.data) ? response.data : [];
          if (isActive) {
            setClientiInternal(clientiArray);
          }
        } catch (err) {
          console.error('Error loading clienti:', err);
        }
      })();

      return () => {
        isActive = false;
      };
    }
    return undefined;
  }, [clientiProp]);

  const selectedCliente = clienti.find(c => c.id === value);

  // Close dropdown when clicking outside
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

  // Filter results based on search term
  const filteredClienti = searchTerm.length > 0
    ? clienti.filter(cliente => {
        // Supporta entrambi i formati: anagrafica come oggetto o come number con anagrafica_display
        const displayName = typeof cliente.anagrafica === 'object' 
          ? (cliente.anagrafica.display_name || cliente.anagrafica.ragione_sociale || cliente.anagrafica.cognome || '')
          : (cliente.anagrafica_display || '');
        const cf = cliente.codice_fiscale || '';
        const piva = cliente.partita_iva || '';
        const searchLower = searchTerm.toLowerCase();
        
        return displayName.toLowerCase().includes(searchLower) ||
               cf.toLowerCase().includes(searchLower) ||
               piva.toLowerCase().includes(searchLower);
      })
    : clienti;

  const handleSelect = (cliente: Cliente) => {
    onChange(cliente.id);
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

  const getClienteDisplay = (cliente: Cliente) => {
    // Supporta entrambi i formati
    if (typeof cliente.anagrafica === 'object') {
      return cliente.anagrafica.display_name ||
             cliente.anagrafica.ragione_sociale ||
             cliente.anagrafica.cognome ||
             `Cliente ${cliente.id}`;
    }
    return cliente.anagrafica_display || `Cliente ${cliente.id}`;
  };

  const getClienteSecondaryInfo = (cliente: Cliente) => {
    const parts = [];
    if (cliente.codice_fiscale) parts.push(`CF: ${cliente.codice_fiscale}`);
    if (cliente.partita_iva) parts.push(`P.IVA: ${cliente.partita_iva}`);
    return parts.join(' • ');
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        {selectedCliente ? (
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
              <strong>{getClienteDisplay(selectedCliente)}</strong>
              {getClienteSecondaryInfo(selectedCliente) && (
                <div style={{ fontSize: '0.85em', color: '#6b7280', marginTop: '0.15rem' }}>
                  {getClienteSecondaryInfo(selectedCliente)}
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

      <AutocompletePortal ref={portalRef} isOpen={isOpen && filteredClienti.length > 0} anchorRef={wrapperRef} maxHeight="400px">
        {filteredClienti.length > 0 ? (
          filteredClienti.map((cliente) => (
            <div
              key={cliente.id}
              onClick={() => handleSelect(cliente)}
              style={{
                padding: '0.75rem',
                cursor: 'pointer',
                borderBottom: '1px solid #f0f0f0'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
            >
              <div style={{ fontWeight: 'bold', color: '#1f2937' }}>
                {getClienteDisplay(cliente)}
              </div>
              {getClienteSecondaryInfo(cliente) && (
                <div style={{ fontSize: '0.85em', color: '#6b7280', marginTop: '0.25rem' }}>
                  {getClienteSecondaryInfo(cliente)}
                </div>
              )}
            </div>
          ))
        ) : (
          <div style={{ padding: '0.75rem', textAlign: 'center', color: '#9ca3af' }}>
            Nessun cliente trovato
          </div>
        )}
      </AutocompletePortal>

      <AutocompletePortal isOpen={isOpen && searchTerm.length > 0 && filteredClienti.length === 0} anchorRef={wrapperRef}>
        <div style={{
          padding: '0.75rem',
          textAlign: 'center',
          color: '#9ca3af'
        }}>
          Nessun cliente trovato per "{searchTerm}"
        </div>
      </AutocompletePortal>
    </div>
  );
}
