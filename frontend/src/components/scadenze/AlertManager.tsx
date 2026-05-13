/**
 * Modal per la gestione degli alert di un'occorrenza.
 * Supporta: Email, Webhook, Telegram, WhatsApp.
 */
import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { apiClient } from '@/api/client';
import { CloseIcon, AddIcon, DeleteIcon, EditIcon } from '../icons/Icons';
import { DestinatariEmailInput } from '../DestinatariEmailInput';
import { ClienteAutocomplete } from '../ClienteAutocomplete';
import type { ScadenzaAlert } from '@/types/scadenza';

interface AlertManagerProps {
  occorrenzaId: number;
  occorrenzaTitolo: string;
  onClose: () => void;
}

type MetodoAlert = 'email' | 'webhook' | 'telegram' | 'whatsapp';
type PeriodoOffset = 'minutes' | 'hours' | 'days' | 'weeks';

interface AlertFormData {
  offset_alert: number;
  offset_alert_periodo: PeriodoOffset;
  metodo_alert: MetodoAlert;
  // email
  destinatari: string;
  oggetto_custom: string;
  corpo_custom: string;
  // webhook
  webhook_url: string;
  webhook_payload: string;
  // telegram
  telegram_chat_ids: string;
  // whatsapp
  whatsapp_numeri: string;
}

const initialFormData: AlertFormData = {
  offset_alert: 1,
  offset_alert_periodo: 'days',
  metodo_alert: 'email',
  destinatari: '',
  oggetto_custom: '',
  corpo_custom: '',
  webhook_url: '',
  webhook_payload: '',
  telegram_chat_ids: '',
  whatsapp_numeri: '',
};

function buildAlertConfig(form: AlertFormData): Record<string, unknown> {
  switch (form.metodo_alert) {
    case 'email': {
      const cfg: Record<string, unknown> = {};
      if (form.destinatari.trim()) cfg.destinatari = form.destinatari.trim();
      if (form.oggetto_custom.trim()) cfg.oggetto_custom = form.oggetto_custom.trim();
      if (form.corpo_custom.trim()) cfg.corpo_custom = form.corpo_custom.trim();
      return cfg;
    }
    case 'webhook': {
      const cfg: Record<string, unknown> = { url: form.webhook_url.trim() };
      if (form.webhook_payload.trim()) {
        try {
          cfg.payload = JSON.parse(form.webhook_payload);
        } catch {
          // lascia senza payload se JSON non valido
        }
      }
      if (form.corpo_custom.trim()) cfg.corpo_custom = form.corpo_custom.trim();
      return cfg;
    }
    case 'telegram': {
      const cfg: Record<string, unknown> = {};
      if (form.telegram_chat_ids.trim()) {
        cfg.chat_ids = form.telegram_chat_ids.split(',').map(s => s.trim()).filter(Boolean);
      }
      if (form.corpo_custom.trim()) cfg.corpo_custom = form.corpo_custom.trim();
      return cfg;
    }
    case 'whatsapp': {
      const cfg: Record<string, unknown> = {};
      if (form.whatsapp_numeri.trim()) {
        cfg.numeri_telefono = form.whatsapp_numeri.split(',').map(s => s.trim()).filter(Boolean);
      }
      if (form.corpo_custom.trim()) cfg.corpo_custom = form.corpo_custom.trim();
      return cfg;
    }
    default:
      return {};
  }
}

function parseAlertConfig(alert: ScadenzaAlert): Partial<AlertFormData> {
  const cfg = (alert.alert_config as Record<string, unknown>) || {};
  const result: Partial<AlertFormData> = {
    metodo_alert: alert.metodo_alert as MetodoAlert,
    offset_alert: alert.offset_alert,
    offset_alert_periodo: (alert.offset_alert_periodo as PeriodoOffset) || 'days',
    corpo_custom: typeof cfg.corpo_custom === 'string' ? cfg.corpo_custom : '',
  };
  if (alert.metodo_alert === 'email') {
    result.destinatari = typeof cfg.destinatari === 'string' ? cfg.destinatari : '';
    result.oggetto_custom = typeof cfg.oggetto_custom === 'string' ? cfg.oggetto_custom : '';
  }
  if (alert.metodo_alert === 'webhook') {
    result.webhook_url = typeof cfg.url === 'string' ? cfg.url : '';
    result.webhook_payload = cfg.payload ? JSON.stringify(cfg.payload, null, 2) : '';
  }
  if (alert.metodo_alert === 'telegram') {
    const ids = Array.isArray(cfg.chat_ids) ? cfg.chat_ids.join(', ') : '';
    result.telegram_chat_ids = ids;
  }
  if (alert.metodo_alert === 'whatsapp') {
    const numeri = Array.isArray(cfg.numeri_telefono) ? cfg.numeri_telefono.join(', ') : '';
    result.whatsapp_numeri = numeri;
  }
  return result;
}

function extractErrorDetail(err: unknown, fallback: string): string {
  if (isAxiosError(err)) {
    const data = err.response?.data as Record<string, unknown> | undefined;
    if (data?.detail) return String(data.detail);
    if (data) {
      const msgs = Object.entries(data)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : String(v)}`)
        .join(' | ');
      if (msgs) return msgs;
    }
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}

// ─── Componente principale ───────────────────────────────────────────────────

export default function AlertManager({ occorrenzaId, occorrenzaTitolo, onClose }: AlertManagerProps) {
  const [alerts, setAlerts] = useState<ScadenzaAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingAlert, setEditingAlert] = useState<ScadenzaAlert | null>(null);
  const [formData, setFormData] = useState<AlertFormData>(initialFormData);

  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<ScadenzaAlert[] | { results: ScadenzaAlert[] }>(
        `/scadenze/alerts/?occorrenza=${occorrenzaId}`
      );
      const alertsData = Array.isArray(response.data) ? response.data : response.data.results;
      setAlerts(alertsData);
    } catch (err: unknown) {
      setError(extractErrorDetail(err, 'Errore nel caricamento degli alert'));
    } finally {
      setLoading(false);
    }
  }, [occorrenzaId]);

  useEffect(() => { void loadAlerts(); }, [loadAlerts]);

  const handleAddAlert = () => {
    setEditingAlert(null);
    setFormData({ ...initialFormData });
    setShowForm(true);
  };

  const handleEditAlert = (alert: ScadenzaAlert) => {
    setEditingAlert(alert);
    setFormData({ ...initialFormData, ...parseAlertConfig(alert) });
    setShowForm(true);
  };

  const handleDeleteAlert = async (alertId: number) => {
    if (!window.confirm('Eliminare questo alert?')) return;
    try {
      await apiClient.delete(`/scadenze/alerts/${alertId}/`);
      void loadAlerts();
    } catch (err: unknown) {
      alert(extractErrorDetail(err, 'Errore durante l\'eliminazione'));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.metodo_alert === 'webhook' && !formData.webhook_url.trim()) {
      setError('URL webhook obbligatorio');
      return;
    }

    const alertData = {
      occorrenza: occorrenzaId,
      offset_alert: formData.offset_alert,
      offset_alert_periodo: formData.offset_alert_periodo,
      metodo_alert: formData.metodo_alert,
      alert_config: buildAlertConfig(formData),
    };

    try {
      if (editingAlert) {
        await apiClient.patch(`/scadenze/alerts/${editingAlert.id}/`, alertData);
      } else {
        await apiClient.post(`/scadenze/alerts/`, alertData);
      }
      setShowForm(false);
      void loadAlerts();
    } catch (err: unknown) {
      setError(extractErrorDetail(err, 'Errore durante il salvataggio'));
    }
  };

  const set = (field: keyof AlertFormData) => (value: string | number) =>
    setFormData(prev => ({ ...prev, [field]: value }));

  const getStatoBadge = (stato: string) => {
    if (stato === 'sent') return 'badge-success';
    if (stato === 'failed') return 'badge-danger';
    return 'badge-secondary';
  };

  const formatDT = (s: string | null) => {
    if (!s) return '-';
    return new Intl.DateTimeFormat('it-IT', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    }).format(new Date(s));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '800px', width: '90%' }}
      >
        <div className="modal-header">
          <div>
            <h2>Gestione Alert</h2>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', margin: '0.5rem 0 0' }}>
              {occorrenzaTitolo}
            </p>
          </div>
          <button onClick={onClose} className="btn btn-icon" style={{ border: 'none', background: 'transparent' }}>
            <CloseIcon />
          </button>
        </div>

        <div style={{ padding: '1.5rem' }}>
          {error && (
            <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{error}</div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: '600', margin: 0 }}>
              Alert Configurati ({alerts.length})
            </h3>
            {!showForm && (
              <button onClick={handleAddAlert} className="btn btn-primary btn-sm">
                <AddIcon size={16} />
                <span>Nuovo Alert</span>
              </button>
            )}
          </div>

          {showForm ? (
            <AlertForm
              formData={formData}
              setFormData={setFormData}
              set={set}
              editingAlert={editingAlert}
              onSubmit={handleSubmit}
              onCancel={() => setShowForm(false)}
              error={error}
            />
          ) : loading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>Caricamento...</div>
          ) : alerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
              Nessun alert configurato. Clicca su "Nuovo Alert" per aggiungerne uno.
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Anticipo</th>
                    <th>Canale</th>
                    <th>Stato</th>
                    <th>Programmata</th>
                    <th>Inviata</th>
                    <th style={{ textAlign: 'center' }}>Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <span style={{ fontWeight: '500' }}>
                          {alert.offset_alert} {alert.offset_alert_periodo_display}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-secondary">
                          {alert.metodo_alert_display}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${getStatoBadge(alert.stato)}`}>
                          {alert.stato_display}
                        </span>
                      </td>
                      <td style={{ fontSize: 'var(--font-size-sm)' }}>{formatDT(alert.alert_programmata_il)}</td>
                      <td style={{ fontSize: 'var(--font-size-sm)' }}>
                        {alert.alert_inviata_il
                          ? <span style={{ color: 'var(--success)' }}>✓ {formatDT(alert.alert_inviata_il)}</span>
                          : '-'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          {alert.stato === 'pending' ? (
                            <>
                              <button
                                onClick={() => handleEditAlert(alert)}
                                className="btn btn-icon btn-sm"
                                title="Modifica"
                                style={{ backgroundColor: 'var(--primary)', color: 'white', border: 'none' }}
                              >
                                <EditIcon size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteAlert(alert.id)}
                                className="btn btn-icon btn-sm"
                                title="Elimina"
                                style={{ backgroundColor: 'var(--danger)', color: 'white', border: 'none' }}
                              >
                                <DeleteIcon size={16} />
                              </button>
                            </>
                          ) : (
                            <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                              {alert.stato === 'sent' ? '✓ Inviata' : alert.stato === 'failed' ? '✗ Fallita' : alert.stato}
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn btn-secondary">Chiudi</button>
        </div>
      </div>
    </div>
  );
}

// ─── Sotto-componente form ────────────────────────────────────────────────────

interface AlertFormProps {
  formData: AlertFormData;
  setFormData: React.Dispatch<React.SetStateAction<AlertFormData>>;
  set: (field: keyof AlertFormData) => (value: string | number) => void;
  editingAlert: ScadenzaAlert | null;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  onCancel: () => void;
  error: string | null;
}

function AlertForm({ formData, setFormData, set, editingAlert, onSubmit, onCancel }: AlertFormProps) {
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

  const labelStyle: React.CSSProperties = { fontWeight: 500, marginBottom: '0.25rem', display: 'block' };
  const hintStyle: React.CSSProperties = { fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginTop: '0.25rem' };

  return (
    <form
      onSubmit={onSubmit}
      style={{
        padding: '1.5rem',
        backgroundColor: 'var(--background)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border)',
        marginBottom: '1rem',
      }}
    >
      <h4 style={{ marginBottom: '1.25rem' }}>{editingAlert ? 'Modifica Alert' : 'Nuovo Alert'}</h4>

      {/* ── Timing ── */}
      <div className="form-grid" style={{ gridTemplateColumns: '1fr 1fr', marginBottom: '1rem' }}>
        <div className="form-group">
          <label style={labelStyle}>Anticipo <span style={{ color: 'red' }}>*</span></label>
          <input
            type="number"
            min="1"
            value={formData.offset_alert}
            onChange={(e) => set('offset_alert')(Number(e.target.value))}
            className="form-control"
            required
          />
        </div>
        <div className="form-group">
          <label style={labelStyle}>Unità di tempo</label>
          <select
            value={formData.offset_alert_periodo}
            onChange={(e) => set('offset_alert_periodo')(e.target.value)}
            className="form-control"
          >
            <option value="minutes">Minuti</option>
            <option value="hours">Ore</option>
            <option value="days">Giorni</option>
            <option value="weeks">Settimane</option>
          </select>
        </div>
      </div>

      {/* ── Canale ── */}
      <div className="form-group" style={{ marginBottom: '1.25rem' }}>
        <label style={labelStyle}>Canale di notifica</label>
        <select
          value={formData.metodo_alert}
          onChange={(e) =>
            setFormData(prev => ({ ...initialFormData, offset_alert: prev.offset_alert, offset_alert_periodo: prev.offset_alert_periodo, metodo_alert: e.target.value as MetodoAlert }))
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

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
        <button type="button" onClick={onCancel} className="btn btn-secondary">Annulla</button>
        <button type="submit" className="btn btn-primary">Salva Alert</button>
      </div>
    </form>
  );
}
