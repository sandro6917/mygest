/**
 * DocumentoAutocomplete Component
 * Autocomplete per la selezione di documenti (singola o multipla)
 */
import { useState, useEffect, useRef } from 'react';
import { apiClient } from '@/api/client';

interface Documento {
  id: number;
  codice: string;
  descrizione: string;
  stato: string;
  data_documento: string;
  cliente_detail?: {
    anagrafica_display?: string;
  };
  tipo_detail?: {
    nome: string;
  };
}

interface DocumentoAutocompleteProps {
  value: number | number[] | null;
  onChange: (id: number | number[] | null) => void;
  multiple?: boolean;
  required?: boolean;
  excludeIds?: number[];
}

interface DocumentiResponse {
  results: Documento[];
}

export function DocumentoAutocomplete({ 
  value, 
  onChange, 
  multiple = false,
  required = false,
  excludeIds = []
}: DocumentoAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [documenti, setDocumenti] = useState<Documento[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Carica documenti in base al termine di ricerca
  useEffect(() => {
    if (searchTerm.length >= 2) {
      let isActive = true;
      setIsLoading(true);

      void (async () => {
        try {
          const response = await apiClient.get<DocumentiResponse>(
            `/documenti/?search=${encodeURIComponent(searchTerm)}&page_size=100`
          );
          const documentiArray = Array.isArray(response.data?.results) ? response.data.results : [];
          if (isActive) {
            setDocumenti(documentiArray);
          }
        } catch (err) {
          console.error('Error loading documenti:', err);
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
      setDocumenti([]);
    }
    return undefined;
  }, [searchTerm]);

  // Filtra documenti escludendo quelli nell'elenco excludeIds
  const availableDocumenti = documenti.filter(d => !excludeIds.includes(d.id));

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

  const handleSelect = (documento: Documento) => {
    if (multiple) {
      const currentValues = Array.isArray(value) ? value : [];
      if (currentValues.includes(documento.id)) {
        // Rimuovi se già selezionato
        onChange(currentValues.filter(id => id !== documento.id));
      } else {
        // Aggiungi
        onChange([...currentValues, documento.id]);
      }
    } else {
      onChange(documento.id);
      setSearchTerm('');
      setIsOpen(false);
    }
  };

  const handleRemove = (documentoId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (multiple && Array.isArray(value)) {
      onChange(value.filter(id => id !== documentoId));
    } else {
      onChange(null);
      setSearchTerm('');
    }
  };

  // Get selected documenti per visualizzazione
  const selectedDocumenti = multiple && Array.isArray(value)
    ? documenti.filter(d => value.includes(d.id))
    : value && typeof value === 'number'
    ? documenti.filter(d => d.id === value)
    : [];

  const isSelected = (documentoId: number) => {
    if (multiple && Array.isArray(value)) {
      return value.includes(documentoId);
    }
    return value === documentoId;
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative', width: '100%' }}>
      {/* Chips per selezioni multiple */}
      {multiple && selectedDocumenti.length > 0 && (
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: '0.5rem', 
          marginBottom: '0.5rem' 
        }}>
          {selectedDocumenti.map(documento => (
            <div
              key={documento.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.25rem 0.75rem',
                backgroundColor: '#fef3c7',
                border: '1px solid #f59e0b',
                borderRadius: '9999px',
                fontSize: '0.875rem',
              }}
            >
              <span>{documento.codice || `Doc #${documento.id}`}</span>
              <button
                type="button"
                onClick={(e) => handleRemove(documento.id, e)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#f59e0b',
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
              ? "Cerca documenti per codice o descrizione..." 
              : selectedDocumenti.length > 0
              ? `${selectedDocumenti[0].codice || `Doc #${selectedDocumenti[0].id}`} - ${selectedDocumenti[0].descrizione}`
              : "Cerca documento per codice o descrizione..."
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
          ) : availableDocumenti.length === 0 ? (
            <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
              Nessun documento trovato
            </div>
          ) : (
            availableDocumenti.map((documento) => (
              <div
                key={documento.id}
                onClick={() => handleSelect(documento)}
                style={{
                  padding: '0.75rem',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f3f4f6',
                  backgroundColor: isSelected(documento.id) ? '#fef3c7' : 'white',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = isSelected(documento.id) 
                    ? '#fde68a' 
                    : '#f9fafb';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = isSelected(documento.id) 
                    ? '#fef3c7' 
                    : 'white';
                }}
              >
                <div style={{ fontWeight: 600, color: '#111827', marginBottom: '0.25rem' }}>
                  {documento.codice || `Documento #${documento.id}`}
                  {isSelected(documento.id) && (
                    <span style={{ marginLeft: '0.5rem', color: '#f59e0b' }}>✓</span>
                  )}
                </div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  {documento.descrizione}
                </div>
                {documento.tipo_detail?.nome && (
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                    Tipo: {documento.tipo_detail.nome}
                  </div>
                )}
                {documento.cliente_detail?.anagrafica_display && (
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                    Cliente: {documento.cliente_detail.anagrafica_display}
                  </div>
                )}
                <div style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                  <span style={{ color: '#6b7280', marginRight: '0.5rem' }}>
                    {new Date(documento.data_documento).toLocaleDateString('it-IT')}
                  </span>
                  <span
                    style={{
                      padding: '0.125rem 0.5rem',
                      borderRadius: '0.25rem',
                      backgroundColor: 
                        documento.stato === 'definitivo' ? '#d1fae5' :
                        documento.stato === 'bozza' ? '#fef3c7' :
                        documento.stato === 'archiviato' ? '#e0e7ff' : '#f3f4f6',
                      color: 
                        documento.stato === 'definitivo' ? '#065f46' :
                        documento.stato === 'bozza' ? '#92400e' :
                        documento.stato === 'archiviato' ? '#3730a3' : '#6b7280',
                    }}
                  >
                    {documento.stato}
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
