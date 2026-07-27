/**
 * Modal per la gestione degli alert di un'occorrenza.
 * Supporta: Email, Webhook, Telegram, WhatsApp.
 */
import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { apiClient } from '@/api/client';
import { CloseIcon, AddIcon, DeleteIcon, EditIcon } from '../icons/Icons';
import AlertChannelFields from './AlertChannelFields';
import {
  initialAlertFormData as initialFormData,
  buildAlertConfig,
  parseAlertConfig,
  type AlertFormData,
} from '@/utils/scadenzaAlertConfig';
import type { ScadenzaAlert } from '@/types/scadenza';

interface AlertManagerProps {
  occorrenzaId: number;
  occorrenzaTitolo: string;
  onClose: () => void;
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
                                style={{ backgroundColor: '#dc3545', color: 'white', border: 'none' }}
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
  const labelStyle: React.CSSProperties = { fontWeight: 500, marginBottom: '0.25rem', display: 'block' };

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

      <AlertChannelFields formData={formData} setFormData={setFormData} set={set} />

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
        <button type="button" onClick={onCancel} className="btn btn-secondary">Annulla</button>
        <button type="submit" className="btn btn-primary">Salva Alert</button>
      </div>
    </form>
  );
}
