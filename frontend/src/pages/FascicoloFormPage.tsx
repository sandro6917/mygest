/**
 * Fascicolo Form Page - Create/Edit
 */
import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { fascicoliApi } from '@/api/fascicoli';
import { praticheApi } from '@/api/pratiche';
import { apiClient } from '@/api/client';
import type { FascicoloFormData, TitolarioVoce, UnitaFisica } from '@/types/fascicolo';
import type { Pratica } from '@/types/pratica';
import { ArrowBackIcon } from '@/components/icons/Icons';
import { TitolarioAutocomplete } from '@/components/TitolarioAutocomplete';
import { UbicazioneAutocomplete } from '@/components/UbicazioneAutocomplete';
import { ClienteAutocomplete } from '@/components/ClienteAutocomplete';

interface Cliente {
  id: number;
  anagrafica: {
    display_name?: string;
    ragione_sociale?: string;
    cognome?: string;
  };
}

type ClientiApiResponse = Cliente[] | { results?: Cliente[] };

export default function FascicoloFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const parentId = searchParams.get('parent');
  const praticaId = searchParams.get('pratica_id');
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [titolarioVoci, setTitolarioVoci] = useState<TitolarioVoce[]>([]);
  const [unitaFisiche, setUnitaFisiche] = useState<UnitaFisica[]>([]);
  const [clienti, setClienti] = useState<Cliente[]>([]);
  const [pratica, setPratica] = useState<Pratica | null>(null);

  const [formData, setFormData] = useState<FascicoloFormData>({
    titolo: '',
    anno: new Date().getFullYear(),
    stato: 'corrente',
    cliente: null,
    titolario_voce: 0,
    parent: parentId ? Number(parentId) : null,
    ubicazione: null,
    retention_anni: 10,
    note: '',
    pratiche: praticaId ? [Number(praticaId)] : [],
  });

  const getErrorMessage = (err: unknown, fallback: string) => {
    if (isAxiosError(err)) {
      return (
        err.response?.data?.detail || err.response?.data?.message || err.message || fallback
      );
    }
    if (err instanceof Error) {
      return err.message;
    }
    return fallback;
  };

  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Carica titolario, unità fisiche e clienti
      const [titolarioData, unitaData, clientiResponse] = await Promise.all([
        fascicoliApi.listTitolarioVoci(),
        fascicoliApi.listUnitaFisiche(),
        apiClient.get<ClientiApiResponse>('/clienti/')
      ]);
      
      setTitolarioVoci(titolarioData);
      setUnitaFisiche(unitaData);
      const clientiArray = Array.isArray(clientiResponse.data)
        ? clientiResponse.data
        : clientiResponse.data.results || [];
      setClienti(clientiArray);

      // Se c'è pratica_id, carica la pratica e imposta il cliente
      if (praticaId && !isEdit) {
        const praticaData = await praticheApi.get(Number(praticaId));
        setPratica(praticaData);
        
        // Imposta il cliente dalla pratica
        setFormData(prev => ({
          ...prev,
          cliente: praticaData.cliente
        }));
      }

      // Se modalità edit, carica il fascicolo
      if (isEdit && id) {
        const fascicolo = await fascicoliApi.get(Number(id));
        setFormData({
          titolo: fascicolo.titolo,
          anno: fascicolo.anno,
          stato: fascicolo.stato,
          cliente: fascicolo.cliente,
          titolario_voce: fascicolo.titolario_voce,
          parent: fascicolo.parent,
          ubicazione: fascicolo.ubicazione,
          retention_anni: fascicolo.retention_anni,
          note: fascicolo.note || '',
        });
      }
    } catch (err) {
      console.error('Errore caricamento dati:', err);
      if (isAxiosError(err)) {
        console.error('Response:', err.response);
      }
      setError(getErrorMessage(err, 'Errore nel caricamento dei dati'));
    } finally {
      setLoading(false);
    }
  }, [id, isEdit, praticaId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.titolo.trim()) {
      alert('Inserisci il titolo del fascicolo');
      return;
    }
    if (!formData.titolario_voce) {
      alert('Seleziona una voce del titolario');
      return;
    }

    try {
      setLoading(true);
      
      let fascicoloSalvato;
      if (isEdit && id) {
        fascicoloSalvato = await fascicoliApi.update(Number(id), formData);
      } else {
        fascicoloSalvato = await fascicoliApi.create(formData);
      }
      
      // Se c'è pratica_id, torna alla pratica, altrimenti vai al dettaglio del fascicolo
      if (praticaId) {
        navigate(`/pratiche/${praticaId}`);
      } else {
        navigate(`/fascicoli/${fascicoloSalvato.id}`);
      }
    } catch (err) {
      console.error('Errore salvataggio:', err);
      alert(getErrorMessage(err, 'Errore durante il salvataggio'));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;

    let finalValue: string | number | null = value === '' ? null : value;
    if (['anno', 'cliente', 'titolario_voce', 'parent', 'ubicazione', 'retention_anni'].includes(name)) {
      finalValue = value === '' ? null : Number(value);
    }

    setFormData((prev) => ({
      ...prev,
      [name]: finalValue,
    }));
  };

  if (loading && !formData.titolo) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="alert alert-error">{error}</div>
        <button onClick={() => navigate('/fascicoli')} className="btn-secondary">
          Torna all'elenco
        </button>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={() => navigate(parentId ? `/fascicoli/${parentId}` : '/fascicoli')}
            className="btn-icon"
            title="Torna indietro"
          >
            <ArrowBackIcon size={24} />
          </button>
          <div>
            <h1 className="page-title">
              {isEdit ? 'Modifica Fascicolo' : (parentId ? 'Nuovo Sottofascicolo' : 'Nuovo Fascicolo')}
            </h1>
            <p className="page-subtitle">
              {isEdit ? 'Aggiorna i dati del fascicolo' : 'Inserisci i dati del nuovo fascicolo'}
            </p>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit}>
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Informazioni Principali
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Titolo */}
            <div className="form-group">
              <label>
                Titolo <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="text"
                name="titolo"
                value={formData.titolo}
                onChange={handleChange}
                className="form-control"
                placeholder="Titolo del fascicolo"
                required
              />
            </div>

            {/* Anno */}
            <div className="form-group">
              <label>
                Anno <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="number"
                name="anno"
                value={formData.anno}
                onChange={handleChange}
                className="form-control"
                min="1900"
                max="2100"
                required
              />
            </div>

            {/* Stato */}
            <div className="form-group">
              <label>Stato</label>
              <select
                name="stato"
                value={formData.stato}
                onChange={handleChange}
                className="form-control"
              >
                <option value="corrente">Archivio corrente</option>
                <option value="deposito">Archivio deposito</option>
                <option value="storico">Archivio storico</option>
                <option value="scartato">Scartato</option>
              </select>
            </div>
          </div>
        </div>

        {/* Classificazione */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Classificazione
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Cliente */}
            <div className="form-group">
              <label>Cliente</label>
              <ClienteAutocomplete
                value={formData.cliente || null}
                clienti={clienti}
                onChange={(clienteId) => setFormData(prev => ({ ...prev, cliente: clienteId }))}
                disabled={Boolean(praticaId && !isEdit) || loading}
                placeholder="Cerca cliente..."
              />
              {praticaId && !isEdit && pratica && (
                <small style={{ color: '#6b7280', marginTop: '0.25rem', display: 'block' }}>
                  Cliente ereditato dalla pratica {pratica.codice}
                </small>
              )}
            </div>

            {/* Titolario Voce */}
            <div className="form-group">
              <label>
                Voce Titolario <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <TitolarioAutocomplete
                value={formData.titolario_voce || null}
                voci={titolarioVoci}
                onChange={(voceId) => setFormData(prev => ({ ...prev, titolario_voce: voceId || 0 }))}
                disabled={loading}
                required
                placeholder="Cerca per codice o titolo..."
              />
            </div>

            {/* Ubicazione */}
            <div className="form-group">
              <label>Ubicazione Fisica</label>
              <UbicazioneAutocomplete
                value={formData.ubicazione || null}
                unitaFisiche={unitaFisiche}
                onChange={(unitaId) => setFormData(prev => ({ ...prev, ubicazione: unitaId }))}
                disabled={loading}
                placeholder="Cerca per codice, nome o percorso..."
              />
            </div>

            {/* Retention */}
            <div className="form-group">
              <label>
                Conservazione (anni) <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="number"
                name="retention_anni"
                value={formData.retention_anni}
                onChange={handleChange}
                className="form-control"
                min="0"
                max="100"
                required
              />
              <small style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                Periodo di conservazione obbligatorio
              </small>
            </div>
          </div>
        </div>

        {/* Note */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Note Aggiuntive
          </h2>

          <div className="form-group">
            <label>Note</label>
            <textarea
              name="note"
              value={formData.note}
              onChange={handleChange}
              className="form-control"
              rows={5}
              placeholder="Eventuali note o informazioni aggiuntive sul fascicolo"
            />
          </div>
        </div>

        {/* Azioni */}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
          <button
            type="button"
            onClick={() => navigate(parentId ? `/fascicoli/${parentId}` : '/fascicoli')}
            className="btn-secondary"
            disabled={loading}
          >
            Annulla
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Salvataggio...' : (isEdit ? 'Aggiorna' : 'Crea Fascicolo')}
          </button>
        </div>
      </form>
    </div>
  );
}
