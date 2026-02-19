/**
 * FascicoloAutocomplete Component
 * Autocomplete per la selezione di fascicoli
 */
import { useState, useEffect, useRef } from 'react';
import { apiClient } from '@/api/client';
import { AutocompletePortal, type AutocompletePortalRef } from './AutocompletePortal';

interface Fascicolo {
  id: number;
  codice: string;
  titolo: string;
  anno: number;
  stato: string;
  stato_display: string;
  cliente_display?: string;
}

interface FascicoloAutocompleteProps {
  value: number | null;
  onChange: (id: number | null) => void;
  required?: boolean;
  fascicoli?: Fascicolo[];
  excludeIds?: number[]; // IDs da escludere (es. fascicoli già collegati)
}

interface FascicoliResponse {
  results: Fascicolo[];
}

export function FascicoloAutocomplete({ 
  value, 
  onChange, 
  required = false,
  fascicoli: fascicoliProp,
  excludeIds = []
}: FascicoloAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [fascicoliInternal, setFascicoliInternal] = useState<Fascicolo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const portalRef = useRef<AutocompletePortalRef>(null);

  // Usa fascicoli forniti come prop o quelli caricati internamente
  const fascicoli = fascicoliProp || fascicoliInternal;

  // Carica fascicoli in base al termine di ricerca (server-side search)
  useEffect(() => {
    if (!fascicoliProp && searchTerm.length >= 2) {
      let isActive = true;
      setIsLoading(true);

      void (async () => {
        try {
          // Usa la ricerca server-side con page_size alto per ottenere più risultati
          const response = await apiClient.get<FascicoliResponse>(
            `/fascicoli/fascicoli/?search=${encodeURIComponent(searchTerm)}&page_size=100`
          );
          const fascicoliArray = Array.isArray(response.data?.results) ? response.data.results : [];
          console.log(`[FascicoloAutocomplete] Caricati ${fascicoliArray.length} fascicoli dall'API per "${searchTerm}"`);
          if (isActive) {
            setFascicoliInternal(fascicoliArray);
          }
        } catch (err) {
          console.error('Error loading fascicoli:', err);
        } finally {
          if (isActive) {
            setIsLoading(false);
          }
        }
      })();

      return () => {
        isActive = false;
      };
    } else if (!fascicoliProp && searchTerm.length === 0) {
      // Se non c'è termine di ricerca, carica i primi fascicoli
      setFascicoliInternal([]);
    }
    return undefined;
  }, [fascicoliProp, searchTerm]);

  // Filtra fascicoli escludendo quelli nell'elenco excludeIds
  const availableFascicoli = fascicoli.filter(f => !excludeIds.includes(f.id));

  // NON filtriamo più lato client perché usiamo la ricerca server-side
  // Il server ha già filtrato i risultati con il parametro 'search'
  const filteredFascicoli = availableFascicoli;

  // Debug: log quando filtriamo
  useEffect(() => {
    if (searchTerm && searchTerm.length >= 2) {
      console.log(`[FascicoloAutocomplete] Risultati per "${searchTerm}":`, {
        totale: fascicoli.length,
        disponibili: availableFascicoli.length,
        esclusi: excludeIds.length,
      });
      if (filteredFascicoli.length > 0 && filteredFascicoli.length <= 10) {
        console.log(`[FascicoloAutocomplete] Fascicoli trovati:`, filteredFascicoli.map(f => ({
          id: f.id,
          codice: f.codice,
          titolo: f.titolo
        })));
      }
    }
  }, [searchTerm, fascicoli.length, availableFascicoli.length, filteredFascicoli.length, excludeIds.length, filteredFascicoli]);

  const selectedFascicolo = fascicoli.find(f => f.id === value);

  // Chiudi dropdown quando si clicca fuori
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      
      // Non chiudere se il click è sul wrapper o sul portal
      if (wrapperRef.current && wrapperRef.current.contains(target)) {
        return;
      }
      
      if (portalRef.current?.portalElement?.contains(target)) {
        return;
      }
      
      setIsOpen(false);
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (fascicolo: Fascicolo) => {
    onChange(fascicolo.id);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setSearchTerm('');
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative', width: '100%' }}>
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={isOpen ? searchTerm : (selectedFascicolo ? `${selectedFascicolo.codice} - ${selectedFascicolo.titolo}` : '')}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder="Cerca fascicolo per codice o titolo..."
          required={required && !value}
          style={{
            width: '100%',
            padding: '0.5rem',
            paddingRight: selectedFascicolo ? '2.5rem' : '0.5rem',
            border: '1px solid #d1d5db',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
          }}
        />
        {selectedFascicolo && (
          <button
            type="button"
            onClick={handleClear}
            style={{
              position: 'absolute',
              right: '0.5rem',
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: 'none',
              color: '#6b7280',
              cursor: 'pointer',
              padding: '0.25rem',
              display: 'flex',
              alignItems: 'center',
            }}
            title="Rimuovi selezione"
          >
            ✕
          </button>
        )}
      </div>

      <AutocompletePortal ref={portalRef} isOpen={isOpen} anchorRef={wrapperRef} maxHeight="300px">
        {/* Debug info */}
        {searchTerm && searchTerm.length >= 2 && (
          <div style={{ 
            padding: '0.5rem', 
            fontSize: '0.75rem', 
            backgroundColor: '#f3f4f6',
            borderBottom: '1px solid #d1d5db',
            color: '#6b7280'
          }}>
            {isLoading ? (
              'Caricamento...'
            ) : (
              `Debug: Totali=${fascicoli.length}, Disponibili=${availableFascicoli.length}, Esclusi=${excludeIds.length}, Term="${searchTerm}"`
            )}
          </div>
        )}
        
        {isLoading ? (
          <div style={{ padding: '0.75rem', color: '#6b7280', textAlign: 'center' }}>
            Ricerca in corso...
          </div>
        ) : filteredFascicoli.length > 0 ? (
          filteredFascicoli.map((fascicolo) => (
            <div
              key={fascicolo.id}
              onClick={() => handleSelect(fascicolo)}
              style={{
                padding: '0.75rem',
                cursor: 'pointer',
                borderBottom: '1px solid #f3f4f6',
                backgroundColor: value === fascicolo.id ? '#eff6ff' : 'transparent',
              }}
              onMouseEnter={(e) => {
                if (value !== fascicolo.id) {
                  e.currentTarget.style.backgroundColor = '#f9fafb';
                }
              }}
              onMouseLeave={(e) => {
                if (value !== fascicolo.id) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              <div style={{ fontWeight: 500, fontSize: '0.875rem', marginBottom: '0.125rem' }}>
                {fascicolo.codice}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                {fascicolo.titolo}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', display: 'flex', gap: '1rem' }}>
                <span>Anno: {fascicolo.anno}</span>
                <span>Stato: {fascicolo.stato_display}</span>
                {fascicolo.cliente_display && <span>Cliente: {fascicolo.cliente_display}</span>}
              </div>
            </div>
          ))
        ) : (
          <div style={{ padding: '0.75rem', color: '#6b7280', textAlign: 'center' }}>
            {availableFascicoli.length === 0 
              ? 'Nessun fascicolo disponibile'
              : 'Nessun fascicolo trovato'
            }
          </div>
        )}
      </AutocompletePortal>
    </div>
  );
}
