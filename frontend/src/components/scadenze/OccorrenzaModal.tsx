/**
 * Modal per la creazione/modifica di una occorrenza
 */
import { useState, useEffect } from 'react';
import { isAxiosError } from 'axios';
import type { ScadenzaOccorrenza } from '@/types/scadenza';
import { CloseIcon } from '../icons/Icons';
import { DestinatariEmailInput } from '../DestinatariEmailInput';
import { MessaggioAlertCustomInput } from '../MessaggioAlertCustomInput';

interface OccorrenzaModalProps {
  scadenzaId: number;
  occorrenza?: ScadenzaOccorrenza | null;
  onClose: () => void;
  onSave: (data: Partial<ScadenzaOccorrenza>) => Promise<void>;
}

export default function OccorrenzaModal({ scadenzaId, occorrenza, onClose, onSave }: OccorrenzaModalProps) {
  const [formData, setFormData] = useState<Partial<ScadenzaOccorrenza>>({
    scadenza: scadenzaId,
    titolo: '',
    descrizione: '',
    inizio: '',
    fine: '',
    giornaliera: false,
    stato: 'pending',
    alert_config: {},
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (occorrenza) {
      setFormData({
        scadenza: occorrenza.scadenza,
        titolo: occorrenza.titolo,
        descrizione: occorrenza.descrizione,
        inizio: occorrenza.inizio,
        fine: occorrenza.fine || '',
        giornaliera: occorrenza.giornaliera,
        stato: occorrenza.stato,
        alert_config: occorrenza.alert_config || {},
      });
    }
  }, [occorrenza]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Prepara i dati per l'invio
      const submitData: Partial<ScadenzaOccorrenza> = {
        ...formData,
        // Converte datetime-local in ISO8601 con secondi
        inizio: formData.inizio ? `${formData.inizio}:00` : '',
        // Converte stringa vuota in null per campi opzionali
        fine: formData.fine ? `${formData.fine}:00` : null,
      };

      await onSave(submitData);
      onClose();
    } catch (err: unknown) {
      setError(extractOccorrenzaError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleDestinatariChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      alert_config: {
        ...prev.alert_config,
        destinatari: value,
      },
    }));
  };

  const handleOggettoCustomChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      alert_config: {
        ...prev.alert_config,
        oggetto_custom: value,
      },
    }));
  };

  const handleCorpoCustomChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      alert_config: {
        ...prev.alert_config,
        corpo_custom: value,
      },
    }));
  };

  const handlePayloadCustomChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      alert_config: {
        ...prev.alert_config,
        payload: value ? JSON.parse(value) : undefined,
      },
    }));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px', width: '90%' }}>
        <div className="modal-header">
          <h2>{occorrenza ? 'Modifica Occorrenza' : 'Nuova Occorrenza'}</h2>
          <button onClick={onClose} className="btn btn-icon" style={{ border: 'none', background: 'transparent' }}>
            <CloseIcon />
          </button>
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="titolo">Titolo</label>
            <input
              type="text"
              id="titolo"
              name="titolo"
              value={formData.titolo || ''}
              onChange={handleChange}
              className="form-control"
              placeholder="Lascia vuoto per usare il titolo della scadenza"
            />
          </div>

          <div className="form-group">
            <label htmlFor="descrizione">Descrizione</label>
            <textarea
              id="descrizione"
              name="descrizione"
              value={formData.descrizione || ''}
              onChange={handleChange}
              className="form-control"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="destinatari">
              Destinatari Email Alert
              <small style={{ display: 'block', color: '#666', fontWeight: 'normal' }}>
                Lascia vuoto per usare i destinatari della scadenza
              </small>
            </label>
            <DestinatariEmailInput
              value={formData.alert_config?.destinatari || ''}
              onChange={handleDestinatariChange}
            />
          </div>

          <div className="form-group">
            <MessaggioAlertCustomInput
              metodoAlert={formData.metodo_alert || 'email'}
              oggettoCustom={formData.alert_config?.oggetto_custom || ''}
              corpoCustom={formData.alert_config?.corpo_custom || ''}
              payloadCustom={
                formData.alert_config?.payload 
                  ? JSON.stringify(formData.alert_config.payload, null, 2) 
                  : ''
              }
              onOggettoChange={handleOggettoCustomChange}
              onCorpoChange={handleCorpoCustomChange}
              onPayloadChange={handlePayloadCustomChange}
            />
          </div>

          <div className="form-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div className="form-group">
              <label htmlFor="inizio">
                Inizio <span style={{ color: 'red' }}>*</span>
              </label>
              <input
                type="datetime-local"
                id="inizio"
                name="inizio"
                value={formData.inizio ? formData.inizio.slice(0, 16) : ''}
                onChange={handleChange}
                className="form-control"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="fine">Fine</label>
              <input
                type="datetime-local"
                id="fine"
                name="fine"
                value={formData.fine ? formData.fine.slice(0, 16) : ''}
                onChange={handleChange}
                className="form-control"
              />
            </div>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                name="giornaliera"
                checked={formData.giornaliera || false}
                onChange={handleChange}
              />
              {' '}Occorrenza Giornaliera (senza orario specifico)
            </label>
          </div>

          {occorrenza && (
            <div className="form-group">
              <label htmlFor="stato">Stato</label>
              <select
                id="stato"
                name="stato"
                value={formData.stato || 'pending'}
                onChange={handleChange}
                className="form-control"
              >
                <option value="pending">Pendente</option>
                <option value="scheduled">Programmata</option>
                <option value="alerted">Allertata</option>
                <option value="completed">Completata</option>
                <option value="cancelled">Annullata</option>
              </select>
            </div>
          )}

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={loading}>
              Annulla
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Salvataggio...' : 'Salva'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const extractOccorrenzaError = (error: unknown): string => {
  if (isAxiosError(error)) {
    const detail = error.response?.data as { detail?: string } | undefined;
    return detail?.detail || error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Errore durante il salvataggio';
};
