import React, { useState } from 'react';
import { ClienteAutocomplete } from './ClienteAutocomplete';
import { apiClient } from '@/api/client';

interface Cliente {
  id: number;
  anagrafica_display?: string;
  email?: string;
}

interface DestinatariEmailInputProps {
  value: string; // Email separate da virgola
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  helperText?: string;
}

export const DestinatariEmailInput: React.FC<DestinatariEmailInputProps> = ({
  value,
  onChange,
  disabled = false,
  placeholder = "email1@example.com, email2@example.com",
  helperText = "Inserisci email separate da virgola oppure seleziona un cliente"
}) => {
  const [showClienteAutocomplete, setShowClienteAutocomplete] = useState(false);
  const [clienteSelezionato, setClienteSelezionato] = useState<number | null>(null);
  const [loadingCliente, setLoadingCliente] = useState(false);

  // Parse email da stringa
  const emailList = value
    .split(',')
    .map(email => email.trim())
    .filter(email => email.length > 0);

  // Rimuovi email
  const handleRemove = (emailToRemove: string) => {
    const newEmails = emailList.filter(email => email !== emailToRemove);
    onChange(newEmails.join(', '));
  };

  // Aggiungi email da cliente
  const handleClienteSelect = async (clienteId: number | null) => {
    if (!clienteId) {
      setClienteSelezionato(null);
      return;
    }

    setClienteSelezionato(clienteId);
    setLoadingCliente(true);

    try {
      // Carica dettagli cliente per ottenere email
      const response = await apiClient.get<Cliente>(`/clienti/${clienteId}/`);
      const cliente = response.data;

      if (cliente.email) {
        // Aggiungi email del cliente se non già presente
        if (!emailList.includes(cliente.email)) {
          const newEmails = [...emailList, cliente.email];
          onChange(newEmails.join(', '));
        }
      } else {
        alert('Il cliente selezionato non ha un indirizzo email configurato.');
      }

      // Reset autocomplete
      setClienteSelezionato(null);
      setShowClienteAutocomplete(false);
    } catch (err) {
      console.error('Errore nel caricamento del cliente:', err);
      alert('Errore nel caricamento dell\'email del cliente');
    } finally {
      setLoadingCliente(false);
    }
  };

  return (
    <div className="destinatari-email-input">
      <label className="form-label">
        Destinatari Email Alert
        {helperText && <small className="form-text text-muted d-block">{helperText}</small>}
      </label>

      {/* Campo di testo principale */}
      <textarea
        className="form-control"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        rows={2}
        style={{ marginBottom: '10px' }}
      />

      {/* Visualizza email come chip */}
      {emailList.length > 0 && (
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: '8px', 
          marginBottom: '10px',
          padding: '8px',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px'
        }}>
          {emailList.map((email, index) => (
            <span
              key={index}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                backgroundColor: '#e3f2fd',
                border: '1px solid #2196f3',
                borderRadius: '16px',
                fontSize: '14px',
                color: '#1976d2'
              }}
            >
              <span>{email}</span>
              {!disabled && (
                <button
                  type="button"
                  onClick={() => handleRemove(email)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#1976d2',
                    cursor: 'pointer',
                    padding: '0',
                    fontSize: '16px',
                    lineHeight: '1',
                    fontWeight: 'bold'
                  }}
                  title="Rimuovi"
                >
                  ×
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      {/* Pulsante per aggiungere da cliente */}
      {!disabled && (
        <div style={{ marginTop: '10px' }}>
          {!showClienteAutocomplete ? (
            <button
              type="button"
              className="btn btn-sm btn-outline-primary"
              onClick={() => setShowClienteAutocomplete(true)}
            >
              <i className="bi bi-person-plus me-1"></i>
              Aggiungi da Cliente
            </button>
          ) : (
            <div style={{ 
              border: '1px solid #dee2e6', 
              borderRadius: '4px', 
              padding: '15px',
              backgroundColor: '#f8f9fa'
            }}>
              <div style={{ marginBottom: '10px', fontWeight: 'bold' }}>
                Seleziona Cliente
              </div>
              <ClienteAutocomplete
                value={clienteSelezionato}
                onChange={handleClienteSelect}
                disabled={loadingCliente}
                placeholder="Cerca cliente..."
              />
              <div style={{ marginTop: '10px', display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => {
                    setShowClienteAutocomplete(false);
                    setClienteSelezionato(null);
                  }}
                  disabled={loadingCliente}
                >
                  Annulla
                </button>
              </div>
              {loadingCliente && (
                <div style={{ marginTop: '10px', color: '#6c757d' }}>
                  <i className="bi bi-hourglass-split me-1"></i>
                  Caricamento email cliente...
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <style>{`
        .destinatari-email-input .form-label {
          font-weight: 500;
          margin-bottom: 8px;
          display: block;
        }
      `}</style>
    </div>
  );
};
