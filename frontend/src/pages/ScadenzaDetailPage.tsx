/**
 * Scadenza Detail Page
 */
import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { scadenzeApi } from '@/api/scadenze';
import type { Scadenza, ScadenzaOccorrenza } from '@/types/scadenza';
import {
  ArrowBackIcon,
  EditIcon,
  DeleteIcon,
  CheckIcon,
  CloseIcon,
  CalendarIcon,
  AddIcon,
} from '@/components/icons/Icons';
import OccorrenzaModal from '@/components/scadenze/OccorrenzaModal';
import AlertManager from '@/components/scadenze/AlertManager';

export default function ScadenzaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const scadenzaId = id ? Number(id) : null;
  const navigate = useNavigate();
  const [scadenza, setScadenza] = useState<Scadenza | null>(null);
  const [occorrenze, setOccorrenze] = useState<ScadenzaOccorrenza[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingOccorrenze, setLoadingOccorrenze] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorOccorrenze, setErrorOccorrenze] = useState<string | null>(null);
  const [showOccorrenzaModal, setShowOccorrenzaModal] = useState(false);
  const [selectedOccorrenza, setSelectedOccorrenza] = useState<ScadenzaOccorrenza | null>(null);
  const [showAlertManager, setShowAlertManager] = useState(false);
  const [alertOccorrenza, setAlertOccorrenza] = useState<ScadenzaOccorrenza | null>(null);

  const getErrorMessage = useCallback((err: unknown, fallback: string) => {
    if (isAxiosError(err)) {
      return (
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        fallback
      );
    }
    if (err instanceof Error) {
      return err.message;
    }
    return fallback;
  }, []);

  const loadScadenza = useCallback(async () => {
    if (!scadenzaId) return;

    try {
      setLoading(true);
      const data = await scadenzeApi.get(scadenzaId);
      setScadenza(data);
    } catch (err) {
      setError(getErrorMessage(err, 'Errore nel caricamento della scadenza'));
    } finally {
      setLoading(false);
    }
  }, [getErrorMessage, scadenzaId]);

  const loadOccorrenze = useCallback(async () => {
    if (!scadenzaId) return;

    try {
      setLoadingOccorrenze(true);
      setErrorOccorrenze(null);
      console.log('Caricamento occorrenze per scadenza ID:', scadenzaId);
      const data = await scadenzeApi.listOccorrenze({
        scadenza: scadenzaId,
        ordering: 'inizio',
        page_size: 100,
      });
      console.log('Occorrenze caricate:', data.count, 'risultati:', data.results.length);
      setOccorrenze(data.results);
    } catch (err) {
      const errorMsg = getErrorMessage(err, 'Errore nel caricamento delle occorrenze');
      console.error('Errore nel caricamento delle occorrenze:', err);
      setErrorOccorrenze(errorMsg);
    } finally {
      setLoadingOccorrenze(false);
    }
  }, [getErrorMessage, scadenzaId]);

  useEffect(() => {
    loadScadenza();
    loadOccorrenze();
  }, [loadScadenza, loadOccorrenze]);

  const handleDelete = async () => {
    if (!scadenzaId || !window.confirm('Sei sicuro di voler eliminare questa scadenza?')) return;

    try {
      await scadenzeApi.delete(scadenzaId);
      navigate(-1); // Torna alla pagina precedente
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante l\'eliminazione'));
    }
  };

  const handleCompletaOccorrenza = async (occorrenzaId: number) => {
    try {
      await scadenzeApi.completaOccorrenza(occorrenzaId);
      loadOccorrenze(); // Ricarica la lista
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante il completamento'));
    }
  };

  const handleAnnullaOccorrenza = async (occorrenzaId: number) => {
    if (!window.confirm('Sei sicuro di voler annullare questa occorrenza?')) return;

    try {
      await scadenzeApi.annullaOccorrenza(occorrenzaId);
      loadOccorrenze(); // Ricarica la lista
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante l\'annullamento'));
    }
  };

  const handleGeneraOccorrenze = async () => {
    if (!scadenzaId) return;

    const count = window.prompt('Quante occorrenze vuoi generare?', '10');
    if (!count) return;

    try {
      const result = await scadenzeApi.generaOccorrenze(scadenzaId, { count: Number(count) });
      loadOccorrenze(); // Ricarica la lista
      
      // Mostra messaggio più informativo
      if (!Array.isArray(result) && 'messaggio' in result) {
        alert(result.messaggio);
      } else if (Array.isArray(result)) {
        // Fallback per vecchio formato
        alert(`${result.length} occorrenze gestite con successo`);
      } else {
        alert('Occorrenze generate con successo');
      }
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante la generazione delle occorrenze'));
    }
  };

  const handleAddOccorrenza = () => {
    setSelectedOccorrenza(null);
    setShowOccorrenzaModal(true);
  };

  const handleEditOccorrenza = (occorrenza: ScadenzaOccorrenza) => {
    setSelectedOccorrenza(occorrenza);
    setShowOccorrenzaModal(true);
  };

  const handleDeleteOccorrenza = async (occorrenzaId: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questa occorrenza?')) return;

    try {
      await scadenzeApi.deleteOccorrenza(occorrenzaId);
      loadOccorrenze();
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante l\'eliminazione'));
    }
  };

  const handleSaveOccorrenza = async (data: Partial<ScadenzaOccorrenza>) => {
    if (selectedOccorrenza) {
      // Update
      await scadenzeApi.updateOccorrenza(selectedOccorrenza.id, data);
    } else {
      // Create
      await scadenzeApi.createOccorrenza(data);
    }
    loadOccorrenze();
  };

  const handleManageAlerts = (occorrenza: ScadenzaOccorrenza) => {
    setAlertOccorrenza(occorrenza);
    setShowAlertManager(true);
  };

  const getStatoBadgeClass = (stato: string) => {
    switch (stato) {
      case 'bozza':
        return 'badge-secondary';
      case 'attiva':
        return 'badge-success';
      case 'in_scadenza':
        return 'badge-warning';
      case 'scaduta':
        return 'badge-danger';
      case 'completata':
        return 'badge-info';
      case 'archiviata':
        return 'badge-secondary';
      default:
        return 'badge-secondary';
    }
  };

  const getPrioritaBadgeClass = (priorita: string) => {
    switch (priorita) {
      case 'low':
        return 'badge-secondary';
      case 'medium':
        return 'badge-info';
      case 'high':
        return 'badge-warning';
      case 'critical':
        return 'badge-danger';
      default:
        return 'badge-secondary';
    }
  };

  const getOccorrenzaStatoBadgeClass = (stato: string) => {
    switch (stato) {
      case 'pending':
        return 'badge-secondary';
      case 'scheduled':
        return 'badge-info';
      case 'alerted':
        return 'badge-warning';
      case 'completed':
        return 'badge-success';
      case 'cancelled':
        return 'badge-danger';
      default:
        return 'badge-secondary';
    }
  };

  const formatDateTime = (dateString: string) => {
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

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('it-IT', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(date);
  };

  const getPeriodicityIcon = (periodicita: string) => {
    switch (periodicita) {
      case 'daily': return '⚡';
      case 'weekly': return '📅';
      case 'monthly': return '📆';
      case 'yearly': return '🗓️';
      case 'custom': return '⚙️';
      default: return '⏱️';
    }
  };

  const getGiorniRimanenti = () => {
    if (!scadenza?.data_scadenza) return null;
    const oggi = new Date();
    oggi.setHours(0, 0, 0, 0);
    const dataScad = new Date(scadenza.data_scadenza);
    dataScad.setHours(0, 0, 0, 0);
    const diff = Math.floor((dataScad.getTime() - oggi.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const getStatoInfo = () => {
    const giorni = getGiorniRimanenti();
    
    if (giorni === null) return null;
    
    if (giorni < 0) {
      return {
        text: `Scaduta da ${Math.abs(giorni)} ${Math.abs(giorni) === 1 ? 'giorno' : 'giorni'}`,
        color: '#dc2626',
        icon: '❌',
      };
    } else if (giorni === 0) {
      return {
        text: 'Scade oggi',
        color: '#dc2626',
        icon: '⚠️',
      };
    } else if (giorni <= 3) {
      return {
        text: `Scade tra ${giorni} ${giorni === 1 ? 'giorno' : 'giorni'}`,
        color: '#f59e0b',
        icon: '⏰',
      };
    } else if (giorni <= 7) {
      return {
        text: `Scade tra ${giorni} giorni`,
        color: '#3b82f6',
        icon: '📅',
      };
    } else {
      return {
        text: `${giorni} giorni rimanenti`,
        color: '#10b981',
        icon: '✓',
      };
    }
  };

  const statoInfo = getStatoInfo();

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Caricamento...</div>
      </div>
    );
  }

  if (error || !scadenza) {
    return (
      <div className="container">
        <div className="error">{error || 'Scadenza non trovata'}</div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Alert Banner per scadenze critiche */}
      {statoInfo && (scadenza.stato === 'scaduta' || scadenza.stato === 'in_scadenza') && (
        <div 
          style={{
            padding: '1rem 1.5rem',
            marginBottom: '1.5rem',
            backgroundColor: scadenza.stato === 'scaduta' ? '#fee2e2' : '#fef3c7',
            border: `2px solid ${scadenza.stato === 'scaduta' ? '#dc2626' : '#f59e0b'}`,
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          <span style={{ fontSize: '2rem' }}>{statoInfo.icon}</span>
          <div style={{ flex: 1 }}>
            <div style={{ 
              fontWeight: '700', 
              fontSize: '1.125rem',
              color: statoInfo.color,
              marginBottom: '0.25rem'
            }}>
              {scadenza.stato === 'scaduta' ? 'Scadenza Superata!' : 'Attenzione: Scadenza Imminente'}
            </div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
              {statoInfo.text}
              {scadenza.data_scadenza && ` - Data: ${formatDate(scadenza.data_scadenza)}`}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <button
            onClick={() => navigate(-1)}
            className="btn btn-icon"
            title="Torna alla pagina precedente"
          >
            <ArrowBackIcon size={20} />
          </button>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: '600' }}>
            {scadenza.titolo}
          </h1>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => navigate(`/scadenze/${id}/modifica`)}
              className="btn btn-secondary"
            >
              <EditIcon size={16} />
              <span>Modifica</span>
            </button>
            <button onClick={handleDelete} className="btn btn-danger">
              <DeleteIcon size={16} />
              <span>Elimina</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content - 2 columns */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Informazioni Principali */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CalendarIcon size={20} />
            Informazioni Principali
          </h2>
          <div className="detail-row">
            <span className="detail-label">Titolo:</span>
            <span className="detail-value">{scadenza.titolo}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Descrizione:</span>
            <span className="detail-value">{scadenza.descrizione || '-'}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Stato:</span>
            <span className="detail-value">
              <span className={`badge ${getStatoBadgeClass(scadenza.stato)}`}>
                {scadenza.stato === 'in_scadenza' && '⏰ '}
                {scadenza.stato === 'scaduta' && '❌ '}
                {scadenza.stato_display}
              </span>
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Priorità:</span>
            <span className="detail-value">
              <span className={`badge ${getPrioritaBadgeClass(scadenza.priorita)}`}>
                {scadenza.priorita_display}
              </span>
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Categoria:</span>
            <span className="detail-value">
              {scadenza.categoria ? (
                <span className="badge" style={{ backgroundColor: 'var(--primary)', color: 'white' }}>
                  🏷️ {scadenza.categoria}
                </span>
              ) : '-'}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Periodicità:</span>
            <span className="detail-value">
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>{getPeriodicityIcon(scadenza.periodicita)}</span>
                <span>
                  {scadenza.periodicita_display}
                  {scadenza.periodicita !== 'none' && scadenza.periodicita_intervallo > 1 && 
                    ` (ogni ${scadenza.periodicita_intervallo})`
                  }
                </span>
              </span>
            </span>
          </div>
          {scadenza.data_scadenza && (
            <div className="detail-row">
              <span className="detail-label">Data Scadenza:</span>
              <span className="detail-value">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <span style={{ fontWeight: '600' }}>{formatDate(scadenza.data_scadenza)}</span>
                  {statoInfo && (
                    <span style={{ 
                      fontSize: 'var(--font-size-sm)', 
                      color: statoInfo.color,
                      fontWeight: '600',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem'
                    }}>
                      <span>{statoInfo.icon}</span>
                      <span>{statoInfo.text}</span>
                    </span>
                  )}
                </div>
              </span>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
            Metadata
          </h2>
          <div className="detail-row">
            <span className="detail-label">Creato da:</span>
            <span className="detail-value">
              {scadenza.creato_da_detail 
                ? `${scadenza.creato_da_detail.first_name} ${scadenza.creato_da_detail.last_name}`.trim() || scadenza.creato_da_detail.username
                : '-'
              }
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Creato il:</span>
            <span className="detail-value">{formatDateTime(scadenza.creato_il)}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Aggiornato il:</span>
            <span className="detail-value">{formatDateTime(scadenza.aggiornato_il)}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Assegnatari:</span>
            <span className="detail-value">
              {scadenza.assegnatari_detail.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {scadenza.assegnatari_detail.map(user => (
                    <span key={user.id}>
                      {`${user.first_name} ${user.last_name}`.trim() || user.username}
                    </span>
                  ))}
                </div>
              ) : '-'}
            </span>
          </div>
          {scadenza.google_calendar_calendar_id && (
            <>
              <div className="detail-row">
                <span className="detail-label">Google Calendar:</span>
                <span className="detail-value">{scadenza.google_calendar_calendar_id}</span>
              </div>
              {scadenza.google_calendar_synced_at && (
                <div className="detail-row">
                  <span className="detail-label">Ultima sincronizzazione:</span>
                  <span className="detail-value">{formatDateTime(scadenza.google_calendar_synced_at)}</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Note Interne */}
      {scadenza.note_interne && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
            Note Interne
          </h2>
          <div style={{ whiteSpace: 'pre-wrap' }}>{scadenza.note_interne}</div>
        </div>
      )}

      {/* Collegamenti */}
      {(scadenza.pratiche_detail.length > 0 || scadenza.fascicoli_detail.length > 0 || scadenza.documenti_detail.length > 0) && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
            Collegamenti
          </h2>
          
          {scadenza.pratiche_detail.length > 0 && (
            <div className="detail-row" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
              <span className="detail-label" style={{ marginBottom: '0.5rem' }}>Pratiche:</span>
              <div className="detail-value" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', width: '100%' }}>
                {scadenza.pratiche_detail.map(pratica => (
                  <div 
                    key={pratica.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.75rem',
                      backgroundColor: 'var(--background)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border)',
                      transition: 'all var(--transition-fast)',
                      cursor: 'pointer'
                    }}
                    onClick={() => navigate(`/pratiche/${pratica.id}`)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                      e.currentTarget.style.borderColor = 'var(--primary)';
                      e.currentTarget.style.transform = 'translateX(4px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--background)';
                      e.currentTarget.style.borderColor = 'var(--border)';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', color: 'var(--primary)', marginBottom: '0.25rem' }}>
                        {pratica.numero}
                      </div>
                      <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                        {pratica.oggetto}
                      </div>
                    </div>
                    <span style={{ color: 'var(--primary)', fontSize: '1.25rem' }}>→</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {scadenza.fascicoli_detail.length > 0 && (
            <div className="detail-row" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
              <span className="detail-label" style={{ marginBottom: '0.5rem' }}>Fascicoli:</span>
              <div className="detail-value" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', width: '100%' }}>
                {scadenza.fascicoli_detail.map(fascicolo => (
                  <div 
                    key={fascicolo.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.75rem',
                      backgroundColor: 'var(--background)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border)',
                      transition: 'all var(--transition-fast)',
                      cursor: 'pointer'
                    }}
                    onClick={() => navigate(`/fascicoli/${fascicolo.id}`)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                      e.currentTarget.style.borderColor = 'var(--primary)';
                      e.currentTarget.style.transform = 'translateX(4px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--background)';
                      e.currentTarget.style.borderColor = 'var(--border)';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', color: 'var(--primary)', marginBottom: '0.25rem' }}>
                        {fascicolo.numero}
                      </div>
                      <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                        {fascicolo.oggetto}
                      </div>
                    </div>
                    <span style={{ color: 'var(--primary)', fontSize: '1.25rem' }}>→</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {scadenza.documenti_detail.length > 0 && (
            <div className="detail-row" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
              <span className="detail-label" style={{ marginBottom: '0.5rem' }}>Documenti:</span>
              <div className="detail-value" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', width: '100%' }}>
                {scadenza.documenti_detail.map(documento => (
                  <div 
                    key={documento.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.75rem',
                      backgroundColor: 'var(--background)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border)',
                      transition: 'all var(--transition-fast)',
                      cursor: 'pointer'
                    }}
                    onClick={() => navigate(`/documenti/${documento.id}`)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                      e.currentTarget.style.borderColor = 'var(--primary)';
                      e.currentTarget.style.transform = 'translateX(4px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--background)';
                      e.currentTarget.style.borderColor = 'var(--border)';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', color: 'var(--primary)', marginBottom: '0.25rem' }}>
                        {documento.numero_protocollo || `Doc #${documento.id}`}
                      </div>
                      <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                        {documento.oggetto}
                      </div>
                    </div>
                    <span style={{ color: 'var(--primary)', fontSize: '1.25rem' }}>→</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Occorrenze */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', margin: 0 }}>
            Occorrenze ({occorrenze.length})
          </h2>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleAddOccorrenza}
              className="btn btn-secondary btn-sm"
              title="Aggiungi occorrenza manualmente"
            >
              <AddIcon size={16} />
              <span>Nuova Occorrenza</span>
            </button>
            <button
              onClick={handleGeneraOccorrenze}
              className="btn btn-primary btn-sm"
              disabled={scadenza.periodicita === 'none'}
              title={scadenza.periodicita === 'none' ? 'Imposta una periodicità per generare occorrenze' : 'Genera nuove occorrenze'}
            >
              <CalendarIcon size={16} />
              <span>Genera Occorrenze</span>
            </button>
          </div>
        </div>

        {/* Statistiche occorrenze */}
        {occorrenze.length > 0 && (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(5, 1fr)', 
            gap: '1rem',
            marginBottom: '1.5rem',
            padding: '1rem',
            backgroundColor: 'var(--background)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border)'
          }}>
            {[
              { label: 'Pendenti', count: occorrenze.filter(o => o.stato === 'pending').length, color: '#6b7280', icon: '⏳' },
              { label: 'Programmate', count: occorrenze.filter(o => o.stato === 'scheduled').length, color: '#3b82f6', icon: '📅' },
              { label: 'Allertate', count: occorrenze.filter(o => o.stato === 'alerted').length, color: '#f59e0b', icon: '🔔' },
              { label: 'Completate', count: occorrenze.filter(o => o.stato === 'completed').length, color: '#10b981', icon: '✅' },
              { label: 'Annullate', count: occorrenze.filter(o => o.stato === 'cancelled').length, color: '#ef4444', icon: '❌' },
            ].map((stat) => (
              <div key={stat.label} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>{stat.icon}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: '700', color: stat.color, marginBottom: '0.25rem' }}>
                  {stat.count}
                </div>
                <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        )}

        {loadingOccorrenze ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Caricamento occorrenze...</div>
        ) : errorOccorrenze ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#dc3545' }}>
            <p style={{ marginBottom: '1rem' }}>❌ {errorOccorrenze}</p>
            <button onClick={loadOccorrenze} className="btn btn-secondary btn-sm">
              Riprova
            </button>
          </div>
        ) : occorrenze.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
            Nessuna occorrenza presente.
            {scadenza.periodicita !== 'none' && (
              <div style={{ marginTop: '0.5rem' }}>
                Clicca su "Genera Occorrenze" per creare le occorrenze.
              </div>
            )}
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Titolo</th>
                  <th>Inizio</th>
                  <th>Fine</th>
                  <th>Stato</th>
                  <th>Alert</th>
                  <th style={{ textAlign: 'center' }}>Gestione</th>
                  <th style={{ textAlign: 'center' }}>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {occorrenze.map((occorrenza) => {
                  const getStatoIcon = (stato: string) => {
                    switch (stato) {
                      case 'pending': return '⏳';
                      case 'scheduled': return '📅';
                      case 'alerted': return '🔔';
                      case 'completed': return '✅';
                      case 'cancelled': return '❌';
                      default: return '•';
                    }
                  };

                  return (
                    <tr key={occorrenza.id}>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                          <span style={{ fontWeight: '500' }}>
                            {occorrenza.titolo || scadenza.titolo}
                          </span>
                          {occorrenza.giornaliera && (
                            <span className="badge badge-secondary" style={{ fontSize: '0.7rem', width: 'fit-content' }}>
                              📅 Giornaliera
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span style={{ fontSize: 'var(--font-size-sm)' }}>
                          {formatDateTime(occorrenza.inizio)}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: 'var(--font-size-sm)' }}>
                          {occorrenza.fine ? formatDateTime(occorrenza.fine) : '-'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${getOccorrenzaStatoBadgeClass(occorrenza.stato)}`}>
                          {getStatoIcon(occorrenza.stato)} {occorrenza.stato_display}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: 'var(--font-size-sm)' }}>
                          <span>{occorrenza.metodo_alert_display}</span>
                          {occorrenza.alert_inviata_il ? (
                            <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              ✓ {formatDateTime(occorrenza.alert_inviata_il)}
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-secondary)' }}>-</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <button
                            onClick={() => handleManageAlerts(occorrenza)}
                            className="btn btn-sm"
                            title="Gestisci alert multipli"
                            style={{ 
                              backgroundColor: 'var(--info)', 
                              color: 'white',
                              border: 'none',
                              fontSize: 'var(--font-size-sm)',
                              padding: '0.25rem 0.75rem'
                            }}
                          >
                            🔔 Alert ({occorrenza.num_alerts || 0})
                          </button>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                          {occorrenza.stato !== 'completed' && occorrenza.stato !== 'cancelled' && (
                            <>
                              <button
                                onClick={() => handleEditOccorrenza(occorrenza)}
                                className="btn btn-icon btn-sm"
                                title="Modifica occorrenza"
                                style={{ 
                                  backgroundColor: 'var(--primary)', 
                                  color: 'white',
                                  border: 'none'
                                }}
                              >
                                <EditIcon size={16} />
                              </button>
                              <button
                                onClick={() => handleCompletaOccorrenza(occorrenza.id)}
                                className="btn btn-icon btn-sm"
                                title="Completa occorrenza"
                                style={{ 
                                  backgroundColor: 'var(--success)', 
                                  color: 'white',
                                  border: 'none'
                                }}
                              >
                                <CheckIcon size={16} />
                              </button>
                              <button
                                onClick={() => handleAnnullaOccorrenza(occorrenza.id)}
                                className="btn btn-icon btn-sm"
                                title="Annulla occorrenza"
                                style={{ 
                                  backgroundColor: 'var(--warning)', 
                                  color: 'white',
                                  border: 'none'
                                }}
                              >
                                <CloseIcon size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteOccorrenza(occorrenza.id)}
                                className="btn btn-icon btn-sm"
                                title="Elimina occorrenza"
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
                          {(occorrenza.stato === 'completed' || occorrenza.stato === 'cancelled') && (
                            <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                              {occorrenza.stato === 'completed' ? '✓ Completata' : '✗ Annullata'}
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal per gestione occorrenza */}
      {showOccorrenzaModal && (
        <OccorrenzaModal
          scadenzaId={Number(id)}
          occorrenza={selectedOccorrenza}
          onClose={() => {
            setShowOccorrenzaModal(false);
            setSelectedOccorrenza(null);
          }}
          onSave={handleSaveOccorrenza}
        />
      )}

      {/* Modal per gestione alert */}
      {showAlertManager && alertOccorrenza && (
        <AlertManager
          occorrenzaId={alertOccorrenza.id}
          occorrenzaTitolo={alertOccorrenza.titolo || scadenza.titolo}
          onClose={() => {
            setShowAlertManager(false);
            setAlertOccorrenza(null);
            loadOccorrenze(); // Ricarica per aggiornare num_alerts
          }}
        />
      )}
    </div>
  );
}
