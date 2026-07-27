/**
 * Selettore canale + campi di configurazione specifici per canale
 * (email/telegram/webhook/whatsapp) per un alert scadenza.
 *
 * Estratto da AlertManager per essere riusato anche da GeneraOccorrenzeWizard,
 * dove più righe di questo stesso form vengono ripetute come "template alert".
 */
import { useState } from 'react';
import { apiClient } from '@/api/client';
import { DestinatariEmailInput } from '../DestinatariEmailInput';
import { ClienteAutocomplete } from '../ClienteAutocomplete';
import { initialAlertFormData, type AlertFormData } from '@/utils/scadenzaAlertConfig';

interface AlertChannelFieldsProps {
  formData: AlertFormData;
  setFormData: React.Dispatch<React.SetStateAction<AlertFormData>>;
  set: (field: keyof AlertFormData) => (value: string | number) => void;
}

const labelStyle: React.CSSProperties = { fontWeight: 500, marginBottom: '0.25rem', display: 'block' };
const hintStyle: React.CSSProperties = { fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginTop: '0.25rem' };

export default function AlertChannelFields({ formData, setFormData, set }: AlertChannelFieldsProps) {
  // Stato per selezione cliente telefono (WhatsApp)
  const [showClienteTel, setShowClienteTel] = useState(false);
  const [loadingTel, setLoadingTel] = useState(false);
  const [clienteTelId, setClienteTelId] = useState<number | null>(null);

  const handleClienteTelSelect = async (clienteId: number | null) => {
    if (!clienteId) { setClienteTelId(null); return; }
    setClienteTelId(clienteId);
    setLoadingTel(true);
    try {
      const res = await apiClient.get<{
        email?: string;
        anagrafica?: { telefono?: string; email?: string };
      }>(`/clienti/${clienteId}/`);
      const telefono =
        (typeof res.data.anagrafica === 'object' ? res.data.anagrafica?.telefono : undefined);
      if (telefono) {
        const current = formData.whatsapp_numeri.split(',').map(s => s.trim()).filter(Boolean);
        if (!current.includes(telefono)) {
          setFormData(prev => ({
            ...prev,
            whatsapp_numeri: [...current, telefono].join(', '),
          }));
        }
      } else {
        alert('Il cliente selezionato non ha un numero di telefono configurato.');
      }
    } catch {
      alert('Errore nel recupero del contatto cliente.');
    } finally {
      setLoadingTel(false);
      setClienteTelId(null);
      setShowClienteTel(false);
    }
  };

  return (
    <>
      {/* ── Canale ── */}
      <div className="form-group" style={{ marginBottom: '1.25rem' }}>
        <label style={labelStyle}>Canale di notifica</label>
        <select
          value={formData.metodo_alert}
          onChange={(e) =>
            setFormData(prev => ({ ...initialAlertFormData, offset_alert: prev.offset_alert, offset_alert_periodo: prev.offset_alert_periodo, metodo_alert: e.target.value as AlertFormData['metodo_alert'] }))
          }
          className="form-control"
        >
          <option value="email">Email</option>
          <option value="telegram">Telegram</option>
          <option value="webhook">Webhook</option>
          <option value="whatsapp">WhatsApp (disabilitato)</option>
        </select>
      </div>

      {/* ── Config email ── */}
      {formData.metodo_alert === 'email' && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
          <DestinatariEmailInput
            value={formData.destinatari}
            onChange={set('destinatari')}
            helperText="Lascia vuoto per usare i destinatari configurati nella scadenza"
          />
          <div className="form-group" style={{ marginTop: '1rem' }}>
            <label style={labelStyle}>Oggetto email personalizzato</label>
            <input
              type="text"
              className="form-control"
              value={formData.oggetto_custom}
              onChange={(e) => set('oggetto_custom')(e.target.value)}
              placeholder="Lascia vuoto per usare il titolo della scadenza"
            />
          </div>
          <div className="form-group">
            <label style={labelStyle}>Testo email personalizzato</label>
            <textarea
              className="form-control"
              rows={4}
              value={formData.corpo_custom}
              onChange={(e) => set('corpo_custom')(e.target.value)}
              placeholder="Lascia vuoto per il testo generato automaticamente"
            />
          </div>
        </div>
      )}

      {/* ── Config Telegram ── */}
      {formData.metodo_alert === 'telegram' && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
          <div className="form-group">
            <label style={labelStyle}>Chat ID Telegram</label>
            <input
              type="text"
              className="form-control"
              value={formData.telegram_chat_ids}
              onChange={(e) => set('telegram_chat_ids')(e.target.value)}
              placeholder="Es: 123456789, 987654321"
            />
            <small style={hintStyle}>
              Separati da virgola. Se vuoto, usa i chat ID configurati di default nel sistema.
            </small>
          </div>
          <div className="form-group">
            <label style={labelStyle}>Testo messaggio personalizzato</label>
            <textarea
              className="form-control"
              rows={3}
              value={formData.corpo_custom}
              onChange={(e) => set('corpo_custom')(e.target.value)}
              placeholder="Lascia vuoto per il testo generato automaticamente"
            />
          </div>
        </div>
      )}

      {/* ── Config Webhook ── */}
      {formData.metodo_alert === 'webhook' && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
          <div className="form-group">
            <label style={labelStyle}>URL Webhook <span style={{ color: 'red' }}>*</span></label>
            <input
              type="url"
              className="form-control"
              value={formData.webhook_url}
              onChange={(e) => set('webhook_url')(e.target.value)}
              placeholder="https://hooks.zapier.com/..."
              required
            />
          </div>
          <div className="form-group">
            <label style={labelStyle}>Payload JSON personalizzato</label>
            <textarea
              className="form-control"
              rows={5}
              value={formData.webhook_payload}
              onChange={(e) => set('webhook_payload')(e.target.value)}
              placeholder={'Lascia vuoto per il payload di default:\n{\n  "id": 123,\n  "titolo": "...",\n  "inizio": "2026-07-16T09:00:00"\n}'}
              style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
            />
          </div>
        </div>
      )}

      {/* ── Config WhatsApp ── */}
      {formData.metodo_alert === 'whatsapp' && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
          <div
            style={{
              backgroundColor: '#fef9c3',
              border: '1px solid #ca8a04',
              borderRadius: 'var(--radius-sm)',
              padding: '0.75rem',
              marginBottom: '1rem',
              fontSize: 'var(--font-size-sm)',
              color: '#92400e',
            }}
          >
            WhatsApp è attualmente disabilitato (account Meta in attesa di verifica).
            Gli alert creati verranno ignorati finché non verrà abilitato.
          </div>
          <div className="form-group">
            <label style={labelStyle}>Numeri di telefono</label>
            <input
              type="text"
              className="form-control"
              value={formData.whatsapp_numeri}
              onChange={(e) => set('whatsapp_numeri')(e.target.value)}
              placeholder="Es: +39335337132, +39333000001"
            />
            <small style={hintStyle}>
              Formato internazionale, separati da virgola. Se vuoto, usa i numeri configurati di default.
            </small>
          </div>

          {/* Selezione cliente per telefono */}
          <div style={{ marginTop: '0.75rem' }}>
            {!showClienteTel ? (
              <button
                type="button"
                className="btn btn-sm btn-outline-primary"
                onClick={() => setShowClienteTel(true)}
              >
                + Aggiungi numero da Cliente
              </button>
            ) : (
              <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '1rem', backgroundColor: 'var(--surface)' }}>
                <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>Seleziona Cliente</div>
                <ClienteAutocomplete
                  value={clienteTelId}
                  onChange={handleClienteTelSelect}
                  disabled={loadingTel}
                  placeholder="Cerca cliente..."
                />
                <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => { setShowClienteTel(false); setClienteTelId(null); }}
                    disabled={loadingTel}
                  >
                    Annulla
                  </button>
                </div>
                {loadingTel && (
                  <div style={{ marginTop: '0.5rem', color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                    Recupero contatto...
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="form-group" style={{ marginTop: '1rem' }}>
            <label style={labelStyle}>Testo messaggio personalizzato</label>
            <textarea
              className="form-control"
              rows={3}
              value={formData.corpo_custom}
              onChange={(e) => set('corpo_custom')(e.target.value)}
              placeholder="Lascia vuoto per il testo generato automaticamente"
            />
          </div>
        </div>
      )}
    </>
  );
}
