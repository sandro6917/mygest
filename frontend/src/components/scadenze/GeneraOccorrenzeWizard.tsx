/**
 * Wizard per la generazione automatica di occorrenze multiple ("rateizzazioni")
 * a partire da una data e dalla periodicità della scadenza, con posticipo
 * automatico dei giorni festivi/weekend e uno o più alert applicati a tutte
 * le occorrenze generate nel batch.
 */
import { useState } from 'react';
import { isAxiosError } from 'axios';
import { scadenzeApi } from '@/api/scadenze';
import { CloseIcon, AddIcon, DeleteIcon } from '../icons/Icons';
import AlertChannelFields from './AlertChannelFields';
import { initialAlertFormData, buildAlertConfig, type AlertFormData } from '@/utils/scadenzaAlertConfig';
import type { Scadenza, AlertTemplate } from '@/types/scadenza';

interface GeneraOccorrenzeWizardProps {
  scadenzaId: number;
  scadenza: Scadenza;
  onClose: () => void;
  onGenerated: (messaggio: string) => void;
}

type EndMode = 'count' | 'end';

function defaultStartValue(): string {
  const now = new Date();
  now.setHours(9, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

function extractErrorDetail(err: unknown, fallback: string): string {
  if (isAxiosError(err)) {
    const data = err.response?.data as Record<string, unknown> | undefined;
    if (data?.error) {
      return typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
    }
    if (data?.detail) return String(data.detail);
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}

const labelStyle: React.CSSProperties = { fontWeight: 500, marginBottom: '0.25rem', display: 'block' };
const hintStyle: React.CSSProperties = { fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginTop: '0.25rem' };

export default function GeneraOccorrenzeWizard({ scadenzaId, scadenza, onClose, onGenerated }: GeneraOccorrenzeWizardProps) {
  const [step, setStep] = useState<1 | 2>(1);
  const [start, setStart] = useState(defaultStartValue());
  const [endMode, setEndMode] = useState<EndMode>('count');
  const [count, setCount] = useState<number>(12);
  const [end, setEnd] = useState('');
  const [posticipaFestivi, setPosticipaFestivi] = useState(scadenza.posticipa_festivi);
  const [alertTemplates, setAlertTemplates] = useState<AlertFormData[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddAlertTemplate = () => {
    setAlertTemplates(prev => [...prev, { ...initialAlertFormData }]);
  };

  const handleRemoveAlertTemplate = (index: number) => {
    setAlertTemplates(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpdateAlertTemplate = (index: number, updater: (prev: AlertFormData) => AlertFormData) => {
    setAlertTemplates(prev => prev.map((tpl, i) => (i === index ? updater(tpl) : tpl)));
  };

  const handleNext = () => {
    setError(null);
    if (!start) {
      setError('Specificare la data di inizio');
      return;
    }
    if (endMode === 'count' && (!count || count < 1)) {
      setError('Specificare un numero di occorrenze valido');
      return;
    }
    if (endMode === 'end' && !end) {
      setError('Specificare la data di fine');
      return;
    }
    setStep(2);
  };

  const handleSubmit = async () => {
    setError(null);
    for (const tpl of alertTemplates) {
      if (tpl.metodo_alert === 'webhook' && !tpl.webhook_url.trim()) {
        setError('URL webhook obbligatorio per gli alert di tipo webhook');
        return;
      }
    }

    setSubmitting(true);
    try {
      const alerts: AlertTemplate[] = alertTemplates.map(tpl => ({
        offset_alert: tpl.offset_alert,
        offset_alert_periodo: tpl.offset_alert_periodo,
        metodo_alert: tpl.metodo_alert,
        alert_config: buildAlertConfig(tpl),
      }));
      const result = await scadenzeApi.generaOccorrenze(scadenzaId, {
        start: `${start}:00`,
        end: endMode === 'end' && end ? `${end}:00` : undefined,
        count: endMode === 'count' ? count : undefined,
        posticipa_festivi: posticipaFestivi,
        alerts,
      });
      const messaggio =
        !Array.isArray(result) && 'messaggio' in result
          ? result.messaggio
          : 'Occorrenze generate con successo';
      onGenerated(messaggio);
      onClose();
    } catch (err) {
      setError(extractErrorDetail(err, 'Errore durante la generazione delle occorrenze'));
    } finally {
      setSubmitting(false);
    }
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
            <h2>Genera Occorrenze</h2>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', margin: '0.5rem 0 0' }}>
              {scadenza.titolo} — periodicità: {scadenza.periodicita_display}
              {scadenza.periodicita_intervallo > 1 ? ` (ogni ${scadenza.periodicita_intervallo})` : ''}
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

          {step === 1 && (
            <div>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label style={labelStyle}>Data di inizio <span style={{ color: 'red' }}>*</span></label>
                <input
                  type="datetime-local"
                  className="form-control"
                  value={start}
                  onChange={(e) => setStart(e.target.value)}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label style={labelStyle}>Fino a quando generare</label>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 400 }}>
                    <input type="radio" checked={endMode === 'count'} onChange={() => setEndMode('count')} />
                    Numero di occorrenze
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 400 }}>
                    <input type="radio" checked={endMode === 'end'} onChange={() => setEndMode('end')} />
                    Data di fine
                  </label>
                </div>
                {endMode === 'count' ? (
                  <input
                    type="number"
                    min={1}
                    className="form-control"
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                  />
                ) : (
                  <input
                    type="datetime-local"
                    className="form-control"
                    value={end}
                    onChange={(e) => setEnd(e.target.value)}
                  />
                )}
              </div>

              <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 500 }}>
                  <input
                    type="checkbox"
                    checked={posticipaFestivi}
                    onChange={(e) => setPosticipaFestivi(e.target.checked)}
                  />
                  Posticipa automaticamente le occorrenze che cadono di sabato, domenica o in una festività italiana
                </label>
                <small style={hintStyle}>
                  Se attivo, ogni rata viene spostata al primo giorno feriale utile successivo.
                </small>
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, margin: 0 }}>
                  Alert da applicare a tutte le occorrenze ({alertTemplates.length})
                </h3>
                <button type="button" onClick={handleAddAlertTemplate} className="btn btn-primary btn-sm">
                  <AddIcon size={16} />
                  <span>Aggiungi Alert</span>
                </button>
              </div>

              {alertTemplates.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                  Nessun alert configurato. Le occorrenze verranno generate senza notifiche automatiche;
                  potrai comunque aggiungerli in seguito su ciascuna occorrenza.
                </div>
              ) : (
                alertTemplates.map((tpl, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '1.25rem',
                      backgroundColor: 'var(--background)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border)',
                      marginBottom: '1rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div className="form-grid" style={{ gridTemplateColumns: '1fr 1fr', flex: 1, marginRight: '1rem' }}>
                        <div className="form-group">
                          <label style={labelStyle}>Anticipo <span style={{ color: 'red' }}>*</span></label>
                          <input
                            type="number"
                            min={1}
                            className="form-control"
                            value={tpl.offset_alert}
                            onChange={(e) =>
                              handleUpdateAlertTemplate(index, prev => ({ ...prev, offset_alert: Number(e.target.value) }))
                            }
                          />
                        </div>
                        <div className="form-group">
                          <label style={labelStyle}>Unità di tempo</label>
                          <select
                            className="form-control"
                            value={tpl.offset_alert_periodo}
                            onChange={(e) =>
                              handleUpdateAlertTemplate(index, prev => ({
                                ...prev,
                                offset_alert_periodo: e.target.value as AlertFormData['offset_alert_periodo'],
                              }))
                            }
                          >
                            <option value="minutes">Minuti</option>
                            <option value="hours">Ore</option>
                            <option value="days">Giorni</option>
                            <option value="weeks">Settimane</option>
                          </select>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveAlertTemplate(index)}
                        className="btn btn-icon btn-sm"
                        title="Rimuovi"
                        style={{ backgroundColor: '#dc3545', color: 'white', border: 'none' }}
                      >
                        <DeleteIcon size={16} />
                      </button>
                    </div>

                    <AlertChannelFields
                      formData={tpl}
                      setFormData={(action) =>
                        handleUpdateAlertTemplate(index, prev =>
                          typeof action === 'function' ? (action as (p: AlertFormData) => AlertFormData)(prev) : action
                        )
                      }
                      set={(field) => (value) => handleUpdateAlertTemplate(index, prev => ({ ...prev, [field]: value }))}
                    />
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div>
            {step === 2 && (
              <button type="button" onClick={() => setStep(1)} className="btn btn-secondary" disabled={submitting}>
                Indietro
              </button>
            )}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={submitting}>
              Annulla
            </button>
            {step === 1 ? (
              <button type="button" onClick={handleNext} className="btn btn-primary">
                Avanti
              </button>
            ) : (
              <button type="button" onClick={handleSubmit} className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Generazione in corso...' : 'Genera Occorrenze'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
