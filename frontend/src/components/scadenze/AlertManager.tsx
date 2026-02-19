/**
 * Modal per la gestione degli alert di un'occorrenza
 */
import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { apiClient } from '@/api/client';
import { CloseIcon, AddIcon, DeleteIcon, EditIcon } from '../icons/Icons';
import type { ScadenzaAlert } from '@/types/scadenza';

interface AlertManagerProps {
  occorrenzaId: number;
  occorrenzaTitolo: string;
  onClose: () => void;
}

export default function AlertManager({ occorrenzaId, occorrenzaTitolo, onClose }: AlertManagerProps) {
  const [alerts, setAlerts] = useState<ScadenzaAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingAlert, setEditingAlert] = useState<ScadenzaAlert | null>(null);
  
  // Form state
  type AlertFormData = {
    offset_minuti: number;
    periodo_offset: 'before' | 'after';
    metodo: 'email' | 'webhook';
    config: Record<string, unknown>;
  };

  const initialFormData: AlertFormData = {
    offset_minuti: 60,
    periodo_offset: 'before',
    metodo: 'email',
    config: {},
  };

  const [formData, setFormData] = useState<AlertFormData>(initialFormData);

  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      // Usa il filtro occorrenza invece di nested route
      const response = await apiClient.get<ScadenzaAlert[] | { results: ScadenzaAlert[] }>(
        `/scadenze/alerts/?occorrenza=${occorrenzaId}`
      );
      
      // Gestisce sia risposta paginata che lista diretta
      const alertsData = Array.isArray(response.data) 
        ? response.data 
        : response.data.results;
      
      setAlerts(alertsData);
    } catch (err: unknown) {
      setError(extractErrorDetail(err, 'Errore nel caricamento degli alert'));
    } finally {
      setLoading(false);
    }
  }, [occorrenzaId]);

  useEffect(() => {
    void loadAlerts();
  }, [loadAlerts]);

  const handleAddAlert = () => {
    setEditingAlert(null);
    setFormData({ ...initialFormData });
    setShowForm(true);
  };

  const handleEditAlert = (alert: ScadenzaAlert) => {
    setEditingAlert(alert);
    setFormData({
      offset_minuti: alert.offset_alert,
      periodo_offset: 'before', // Non più salvato nel backend
      metodo: alert.metodo_alert,
      config: alert.alert_config,
    });
    setShowForm(true);
  };

  const handleDeleteAlert = async (alertId: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo alert?')) return;

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

    try {
      // Mappa i campi frontend → backend
      const alertData = {
        occorrenza: occorrenzaId,
        offset_alert: formData.offset_minuti,
        offset_alert_periodo: 'minutes', // Sempre in minuti dal form
        metodo_alert: formData.metodo,
        alert_config: formData.config,
      };

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

  const getStatoBadgeClass = (stato: string) => {
    switch (stato) {
      case 'pending': return 'badge-secondary';
      case 'sent': return 'badge-success';
      case 'failed': return 'badge-danger';
      case 'cancelled': return 'badge-secondary';
      default: return 'badge-secondary';
    }
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('it-IT', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const extractErrorDetail = (err: unknown, fallback: string): string => {
    if (isAxiosError(err)) {
      const detail = err.response?.data as { detail?: string } | undefined;
      if (detail?.detail) {
        return detail.detail;
      }
      return err.message;
    }
    if (err instanceof Error) {
      return err.message;
    }
    return fallback;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%' }}>
        <div className="modal-header">
          <div>
            <h2>Gestione Alert</h2>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', margin: '0.5rem 0 0 0' }}>
              {occorrenzaTitolo}
            </p>
          </div>
          <button onClick={onClose} className="btn btn-icon" style={{ border: 'none', background: 'transparent' }}>
            <CloseIcon />
          </button>
        </div>

        <div style={{ padding: '1.5rem' }}>
          {error && (
            <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
              {error}
            </div>
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
            <form onSubmit={handleSubmit} style={{ 
              padding: '1.5rem', 
              backgroundColor: 'var(--background)', 
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              marginBottom: '1rem'
            }}>
              <h4 style={{ marginBottom: '1rem' }}>{editingAlert ? 'Modifica Alert' : 'Nuovo Alert'}</h4>
              
              <div className="form-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <div className="form-group">
                  <label htmlFor="offset_minuti">
                    Offset (minuti) <span style={{ color: 'red' }}>*</span>
                  </label>
                  <input
                    type="number"
                    id="offset_minuti"
                    name="offset_minuti"
                    min="1"
                    value={formData.offset_minuti}
                    onChange={(e) => setFormData({ ...formData, offset_minuti: Number(e.target.value) })}
                    className="form-control"
                    required
                  />
                  <small className="form-text">
                    Es: 60 = 1 ora, 1440 = 1 giorno
                  </small>
                </div>

                <div className="form-group">
                  <label htmlFor="periodo_offset">Quando</label>
                  <select
                    id="periodo_offset"
                    name="periodo_offset"
                    value={formData.periodo_offset}
                    onChange={(e) => setFormData({ ...formData, periodo_offset: e.target.value as 'before' | 'after' })}
                    className="form-control"
                  >
                    <option value="before">Prima dell'occorrenza</option>
                    <option value="after">Dopo l'occorrenza</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="metodo">Metodo di Notifica</label>
                <select
                  id="metodo"
                  name="metodo"
                  value={formData.metodo}
                  onChange={(e) => setFormData({ ...formData, metodo: e.target.value as 'email' | 'webhook' })}
                  className="form-control"
                >
                  <option value="email">Email</option>
                  <option value="webhook">Webhook</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">
                  Annulla
                </button>
                <button type="submit" className="btn btn-primary">
                  Salva Alert
                </button>
              </div>
            </form>
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
                    <th>Offset</th>
                    <th>Metodo</th>
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
                        <span className={`badge ${getStatoBadgeClass(alert.stato)}`}>
                          {alert.stato_display}
                        </span>
                      </td>
                      <td style={{ fontSize: 'var(--font-size-sm)' }}>
                        {formatDateTime(alert.alert_programmata_il)}
                      </td>
                      <td style={{ fontSize: 'var(--font-size-sm)' }}>
                        {alert.alert_inviata_il ? (
                          <span style={{ color: 'var(--success)' }}>
                            ✓ {formatDateTime(alert.alert_inviata_il)}
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          {alert.stato === 'pending' && (
                            <>
                              <button
                                onClick={() => handleEditAlert(alert)}
                                className="btn btn-icon btn-sm"
                                title="Modifica alert"
                                style={{ 
                                  backgroundColor: 'var(--primary)', 
                                  color: 'white',
                                  border: 'none'
                                }}
                              >
                                <EditIcon size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteAlert(alert.id)}
                                className="btn btn-icon btn-sm"
                                title="Elimina alert"
                                style={{ 
                                  backgroundColor: 'var(--danger)', 
                                  color: 'white',
                                  border: 'none'
                                }}
                              >
                                <DeleteIcon size={16} />
                              </button>
                            </>
                          )}
                          {alert.stato !== 'pending' && (
                            <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                              {alert.stato === 'sent' ? '✓ Inviata' : alert.stato === 'failed' ? '✗ Fallita' : '• ' + alert.stato}
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
          <button onClick={onClose} className="btn btn-secondary">
            Chiudi
          </button>
        </div>
      </div>
    </div>
  );
}
