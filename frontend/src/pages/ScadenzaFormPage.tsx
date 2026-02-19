import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { isAxiosError } from 'axios';
import { apiClient } from '../api/client';
import type { Scadenza } from '../types/scadenza';
import { PraticaAutocomplete } from '../components/PraticaAutocomplete';
import { DocumentoAutocomplete } from '../components/DocumentoAutocomplete';
import { FascicoloAutocomplete } from '../components/FascicoloAutocomplete';
import { DestinatariEmailInput } from '../components/DestinatariEmailInput';

const ScadenzaFormPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const scadenzaId = id ? Number(id) : null;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Query params per pre-compilare collegamenti
  const praticaIdFromQuery = searchParams.get('pratica_id');
  const documentoIdFromQuery = searchParams.get('documento_id');
  const fascicoloIdFromQuery = searchParams.get('fascicolo_id');
  const returnUrl = searchParams.get('return');
  
  // Form state
  const [formData, setFormData] = useState<Partial<Scadenza>>({
    titolo: '',
    descrizione: '',
    categoria: '',
    stato: 'attiva',
    priorita: 'medium',
    periodicita: 'none',
    periodicita_intervallo: 1,
    periodicita_config: {},
    pratiche: [],
    documenti: [],
    fascicoli: [],
  });

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

  // Pre-compila collegamenti da query params
  useEffect(() => {
    if (scadenzaId) return; // Solo per nuova scadenza
    
    const pratiche: number[] = [];
    const documenti: number[] = [];
    const fascicoli: number[] = [];
    
    if (praticaIdFromQuery) pratiche.push(Number(praticaIdFromQuery));
    if (documentoIdFromQuery) documenti.push(Number(documentoIdFromQuery));
    if (fascicoloIdFromQuery) fascicoli.push(Number(fascicoloIdFromQuery));
    
    if (pratiche.length > 0 || documenti.length > 0 || fascicoli.length > 0) {
      setFormData(prev => ({
        ...prev,
        pratiche,
        documenti,
        fascicoli,
      }));
    }
  }, [scadenzaId, praticaIdFromQuery, documentoIdFromQuery, fascicoloIdFromQuery]);

  const loadScadenza = useCallback(async () => {
    if (!scadenzaId) return;

    try {
      setLoading(true);
      const response = await apiClient.get<Scadenza>(`/scadenze/${scadenzaId}/`);
      setFormData(response.data);
    } catch (err) {
      setError(getErrorMessage(err, 'Errore nel caricamento della scadenza'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [getErrorMessage, scadenzaId]);

  // Load scadenza data for edit mode
  useEffect(() => {
    loadScadenza();
  }, [loadScadenza]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (type === 'number') {
      setFormData(prev => ({ ...prev, [name]: value ? parseInt(value) : null }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value || null }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      setLoading(true);
      
      if (scadenzaId) {
        // Update existing scadenza
        await apiClient.patch(`/scadenze/${scadenzaId}/`, formData);
      } else {
        // Create new scadenza
        await apiClient.post('/scadenze/', formData);
      }
      
      // Navigate back to return URL or to scadenze list
      if (returnUrl) {
        navigate(returnUrl);
      } else {
        navigate('/scadenze');
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Errore nel salvataggio della scadenza'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (returnUrl) {
      navigate(returnUrl);
    } else {
      navigate('/scadenze');
    }
  };

  if (loading && id) {
    return <div className="loading">Caricamento...</div>;
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>{id ? 'Modifica Scadenza' : 'Nuova Scadenza'}</h1>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '20px' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="form-container">
        {/* Dati Base */}
        <section className="form-section">
          <h2>Dati Base</h2>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="titolo">
                Titolo <span style={{ color: 'red' }}>*</span>
              </label>
              <input
                type="text"
                id="titolo"
                name="titolo"
                value={formData.titolo || ''}
                onChange={handleInputChange}
                className="form-control"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="categoria">Categoria</label>
              <input
                type="text"
                id="categoria"
                name="categoria"
                value={formData.categoria || ''}
                onChange={handleInputChange}
                className="form-control"
                placeholder="Es: Fiscale, Amministrativo, Legale..."
              />
            </div>

            <div className="form-group">
              <label htmlFor="priorita">Priorità</label>
              <select
                id="priorita"
                name="priorita"
                value={formData.priorita || 'medium'}
                onChange={handleInputChange}
                className="form-control"
              >
                <option value="low">Bassa</option>
                <option value="medium">Media</option>
                <option value="high">Alta</option>
                <option value="critical">Critica</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="stato">Stato</label>
              <select
                id="stato"
                name="stato"
                value={formData.stato || 'attiva'}
                onChange={handleInputChange}
                className="form-control"
              >
                <option value="bozza">Bozza</option>
                <option value="attiva">Attiva</option>
                <option value="completata">Completata</option>
                <option value="archiviata">Archiviata</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="descrizione">Descrizione</label>
            <textarea
              id="descrizione"
              name="descrizione"
              value={formData.descrizione || ''}
              onChange={handleInputChange}
              className="form-control"
              rows={4}
            />
          </div>
        </section>

        {/* Notifiche */}
        <section className="form-section">
          <h2>Notifiche e Alert</h2>
          
          <DestinatariEmailInput
            value={formData.comunicazione_destinatari || ''}
            onChange={(value) => setFormData({ ...formData, comunicazione_destinatari: value })}
            disabled={loading}
            helperText="Email che riceveranno gli alert di questa scadenza. Puoi inserirle manualmente o selezionare un cliente."
          />

          <div className="alert alert-info" style={{ marginTop: '15px' }}>
            <strong>ℹ️ Come funzionano gli alert:</strong>
            <ul style={{ marginBottom: 0, marginTop: '8px', paddingLeft: '20px' }}>
              <li>Gli alert vengono configurati nelle occorrenze (dopo aver salvato la scadenza)</li>
              <li>Puoi impostare alert multipli con tempistiche diverse (es: 7 giorni prima, 1 giorno prima)</li>
              <li>Le email qui configurate sono i destinatari predefiniti per tutti gli alert</li>
              <li>Gli alert possono essere inviati via email o webhook</li>
            </ul>
          </div>
        </section>

        {/* Periodicità */}
        <section className="form-section">
          <h2>Periodicità</h2>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="periodicita">Tipo Periodicità</label>
              <select
                id="periodicita"
                name="periodicita"
                value={formData.periodicita || 'none'}
                onChange={handleInputChange}
                className="form-control"
              >
                <option value="none">Nessuna</option>
                <option value="daily">Giornaliera</option>
                <option value="weekly">Settimanale</option>
                <option value="monthly">Mensile</option>
                <option value="yearly">Annuale</option>
                <option value="custom">Personalizzata</option>
              </select>
            </div>

            {formData.periodicita && formData.periodicita !== 'none' && (
              <div className="form-group">
                <label htmlFor="periodicita_intervallo">Intervallo</label>
                <input
                  type="number"
                  id="periodicita_intervallo"
                  name="periodicita_intervallo"
                  min="1"
                  value={formData.periodicita_intervallo || 1}
                  onChange={handleInputChange}
                  className="form-control"
                />
                <small className="form-text">
                  {formData.periodicita === 'daily' && 'Ogni X giorni'}
                  {formData.periodicita === 'weekly' && 'Ogni X settimane'}
                  {formData.periodicita === 'monthly' && 'Ogni X mesi'}
                  {formData.periodicita === 'yearly' && 'Ogni X anni'}
                </small>
              </div>
            )}
          </div>

          <div className="alert alert-info" style={{ marginTop: '15px' }}>
            <strong>Nota:</strong> Dopo aver salvato la scadenza, potrai gestire le occorrenze 
            dalla pagina di dettaglio. Le occorrenze possono essere generate automaticamente 
            in base alla periodicità configurata oppure create manualmente.
          </div>
        </section>

        {/* Collegamenti */}
        <section className="form-section">
          <h2>Collegamenti</h2>
          <p style={{ color: '#6b7280', marginBottom: '1rem' }}>
            Collega questa scadenza a pratiche, documenti o fascicoli esistenti.
          </p>
          
          <div className="form-group">
            <label htmlFor="pratiche">Pratiche</label>
            <PraticaAutocomplete
              value={formData.pratiche || []}
              onChange={(value) => setFormData(prev => ({ ...prev, pratiche: value as number[] }))}
              multiple={true}
            />
            <small className="form-text">
              Cerca e seleziona le pratiche da collegare a questa scadenza
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="documenti">Documenti</label>
            <DocumentoAutocomplete
              value={formData.documenti || []}
              onChange={(value) => setFormData(prev => ({ ...prev, documenti: value as number[] }))}
              multiple={true}
            />
            <small className="form-text">
              Cerca e seleziona i documenti da collegare a questa scadenza
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="fascicoli">Fascicoli</label>
            <FascicoloAutocomplete
              value={null}
              onChange={(id) => {
                if (id && !formData.fascicoli?.includes(id)) {
                  setFormData(prev => ({
                    ...prev,
                    fascicoli: [...(prev.fascicoli || []), id]
                  }));
                }
              }}
              excludeIds={formData.fascicoli || []}
            />
            {formData.fascicoli && formData.fascicoli.length > 0 && (
              <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {formData.fascicoli.map((fascicoloId) => (
                  <div
                    key={fascicoloId}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.25rem 0.75rem',
                      backgroundColor: '#dbeafe',
                      border: '1px solid #60a5fa',
                      borderRadius: '9999px',
                      fontSize: '0.875rem',
                    }}
                  >
                    <span>Fascicolo #{fascicoloId}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setFormData(prev => ({
                          ...prev,
                          fascicoli: prev.fascicoli?.filter(id => id !== fascicoloId) || []
                        }));
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#60a5fa',
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
            <small className="form-text">
              Cerca e seleziona i fascicoli da collegare a questa scadenza
            </small>
          </div>
        </section>

        {/* Actions */}
        <div className="form-actions">
          <button
            type="button"
            onClick={handleCancel}
            className="btn btn-secondary"
            disabled={loading}
          >
            Annulla
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Salvataggio...' : id ? 'Salva Modifiche' : 'Crea Scadenza'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ScadenzaFormPage;
