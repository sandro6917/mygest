/**
 * Pratica Form Page - Create/Edit
 */
import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { praticheApi } from '@/api/pratiche';
import type { PraticaFormData } from '@/types/pratica';
import { ArrowBackIcon } from '@/components/icons/Icons';
import { ClienteAutocomplete } from '@/components/ClienteAutocomplete';
import { PraticheTipoAutocomplete } from '@/components/PraticheTipoAutocomplete';

export default function PraticaFormPage() {
  const { id } = useParams<{ id: string }>();
  const praticaId = id ? Number(id) : null;
  const navigate = useNavigate();
  const isEdit = praticaId !== null;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<PraticaFormData>({
    tipo: null,
    cliente: null,
    oggetto: '',
    stato: 'aperta',
    responsabile: null,
    periodo_riferimento: 'anno',
    data_riferimento: new Date().toISOString().split('T')[0],
    data_chiusura: null,
    note: '',
    tag: '',
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

  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true);

      // Se modalità edit, carica la pratica
      if (isEdit && praticaId) {
        const pratica = await praticheApi.get(praticaId);
        setFormData({
          tipo: pratica.tipo,
          cliente: pratica.cliente,
          oggetto: pratica.oggetto,
          stato: pratica.stato,
          responsabile: pratica.responsabile,
          periodo_riferimento: pratica.periodo_riferimento,
          data_riferimento: pratica.data_riferimento,
          data_chiusura: pratica.data_chiusura || null,
          note: pratica.note || '',
          tag: pratica.tag || '',
        });
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Errore nel caricamento dei dati'));
    } finally {
      setLoading(false);
    }
  }, [getErrorMessage, isEdit, praticaId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.tipo) {
      alert('Seleziona un tipo pratica');
      return;
    }
    if (!formData.cliente) {
      alert('Seleziona un cliente');
      return;
    }
    if (!formData.oggetto.trim()) {
      alert('Inserisci l\'oggetto della pratica');
      return;
    }

    try {
      setLoading(true);
      
      if (isEdit && praticaId) {
        await praticheApi.update(praticaId, formData);
      } else {
        await praticheApi.create(formData);
      }
      
      navigate('/pratiche');
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
    setFormData(prev => ({
      ...prev,
      [name]: value === '' ? null : value
    }));
  };

  if (loading && !formData.tipo) {
    return (
      <div className="page-container">
        <p>Caricamento...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="alert alert-error">{error}</div>
        <button onClick={() => navigate('/pratiche')} className="btn-secondary">
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
            onClick={() => navigate('/pratiche')}
            className="btn-icon"
            title="Torna all'elenco"
          >
            <ArrowBackIcon size={24} />
          </button>
          <div>
            <h1 className="page-title">
              {isEdit ? 'Modifica Pratica' : 'Nuova Pratica'}
            </h1>
            <p className="page-subtitle">
              {isEdit ? 'Aggiorna i dati della pratica' : 'Inserisci i dati della nuova pratica'}
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
            {/* Tipo Pratica */}
            <div className="form-group">
              <label>
                Tipo Pratica <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <PraticheTipoAutocomplete
                value={formData.tipo}
                onChange={(tipoId) =>
                  setFormData((prev) => ({
                    ...prev,
                    tipo: tipoId,
                  }))
                }
                required
              />
            </div>

            {/* Cliente */}
            <div className="form-group">
              <label>
                Cliente <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <ClienteAutocomplete
                value={formData.cliente}
                onChange={(clienteId) =>
                  setFormData((prev) => ({
                    ...prev,
                    cliente: clienteId,
                  }))
                }
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
                <option value="aperta">Aperta</option>
                <option value="lavorazione">In Lavorazione</option>
                <option value="attesa">In Attesa</option>
                <option value="chiusa">Chiusa</option>
              </select>
            </div>
          </div>

          {/* Oggetto */}
          <div className="form-group" style={{ marginTop: '1.5rem' }}>
            <label>
              Oggetto <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              type="text"
              name="oggetto"
              value={formData.oggetto}
              onChange={handleChange}
              className="form-control"
              placeholder="Descrizione breve della pratica"
              required
            />
          </div>
        </div>

        {/* Date e Periodo */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Date e Periodo di Riferimento
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
            {/* Periodo Riferimento */}
            <div className="form-group">
              <label>Periodo di Riferimento</label>
              <select
                name="periodo_riferimento"
                value={formData.periodo_riferimento}
                onChange={handleChange}
                className="form-control"
              >
                <option value="anno">Anno</option>
                <option value="annomese">Anno/Mese</option>
                <option value="annomesegiorno">Anno/Mese/Giorno</option>
              </select>
              <small style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                Determina il formato del codice pratica
              </small>
            </div>

            {/* Data Riferimento */}
            <div className="form-group">
              <label>
                Data Riferimento <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="date"
                name="data_riferimento"
                value={formData.data_riferimento}
                onChange={handleChange}
                className="form-control"
                required
              />
            </div>

            {/* Data Chiusura */}
            <div className="form-group">
              <label>Data Chiusura</label>
              <input
                type="date"
                name="data_chiusura"
                value={formData.data_chiusura || ''}
                onChange={handleChange}
                className="form-control"
              />
            </div>
          </div>
        </div>

        {/* Note e Tags */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Note e Tags
          </h2>

          {/* Note */}
          <div className="form-group">
            <label>Note</label>
            <textarea
              name="note"
              value={formData.note}
              onChange={handleChange}
              className="form-control"
              rows={4}
              placeholder="Note aggiuntive sulla pratica"
            />
          </div>

          {/* Tags */}
          <div className="form-group" style={{ marginTop: '1.5rem' }}>
            <label>Tags</label>
            <input
              type="text"
              name="tag"
              value={formData.tag}
              onChange={handleChange}
              className="form-control"
              placeholder="Tags separati da virgola"
            />
            <small style={{ color: '#6b7280', fontSize: '0.875rem' }}>
              Es: urgente, importante, da verificare
            </small>
          </div>
        </div>

        {/* Azioni */}
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
          <button
            type="button"
            onClick={() => navigate('/pratiche')}
            className="btn-secondary"
            disabled={loading}
          >
            Annulla
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Salvataggio...' : (isEdit ? 'Aggiorna' : 'Crea Pratica')}
          </button>
        </div>
      </form>
    </div>
  );
}
