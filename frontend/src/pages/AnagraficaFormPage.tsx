import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { AnagraficaDetail, TipoSoggetto, ClientiTipo } from '../types/anagrafiche';
import { ArrowBackIcon, CheckIcon } from '../components/icons/Icons';

interface FormData {
  tipo: TipoSoggetto;
  ragione_sociale: string;
  nome: string;
  cognome: string;
  codice_fiscale: string;
  partita_iva: string;
  codice: string;
  pec: string;
  email: string;
  telefono: string;
  indirizzo: string;
  note: string;
  // Campi Cliente
  is_cliente: boolean;
  cliente_dal: string;
  cliente_al: string;
  codice_destinatario: string;
  tipo_cliente: number | null;
}

interface FormErrors {
  [key: string]: string;
}

export function AnagraficaFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [formData, setFormData] = useState<FormData>({
    tipo: 'PF',
    ragione_sociale: '',
    nome: '',
    cognome: '',
    codice_fiscale: '',
    partita_iva: '',
    codice: '',
    pec: '',
    email: '',
    telefono: '',
    indirizzo: '',
    note: '',
    // Campi Cliente
    is_cliente: false,
    cliente_dal: '',
    cliente_al: '',
    codice_destinatario: '',
    tipo_cliente: null,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(isEdit);
  const [tipiCliente, setTipiCliente] = useState<ClientiTipo[]>([]);

  const loadTipiCliente = useCallback(async () => {
    try {
      type TipiClienteResponse = { results?: ClientiTipo[] } | ClientiTipo[];
      const response = await apiClient.get<TipiClienteResponse>('/tipi-cliente/');
      const payload = Array.isArray(response.data)
        ? response.data
        : response.data.results ?? [];
      setTipiCliente(payload);
    } catch (error) {
      console.error('Error loading tipi cliente:', error);
    }
  }, []);

  const loadAnagrafica = useCallback(async () => {
    if (!id) return;

    try {
      setLoadingData(true);
      const response = await apiClient.get<AnagraficaDetail>(`/anagrafiche/${id}/`);
      const data = response.data;
      
      setFormData({
        tipo: data.tipo,
        ragione_sociale: data.ragione_sociale || '',
        nome: data.nome || '',
        cognome: data.cognome || '',
        codice_fiscale: data.codice_fiscale,
        partita_iva: data.partita_iva || '',
        codice: data.codice || '',
        pec: data.pec || '',
        email: data.email || '',
        telefono: data.telefono || '',
        indirizzo: data.indirizzo || '',
        note: data.note || '',
        // Campi Cliente
        is_cliente: !!data.cliente,
        cliente_dal: data.cliente?.cliente_dal || '',
        cliente_al: data.cliente?.cliente_al || '',
        codice_destinatario: data.cliente?.codice_destinatario || '',
        tipo_cliente: data.cliente?.tipo_cliente || null,
      });
    } catch (error: unknown) {
      alert(extractAnagraficaError(error) ?? 'Errore nel caricamento dell\'anagrafica');
      navigate('/anagrafiche');
    } finally {
      setLoadingData(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    if (isEdit && id) {
      void loadAnagrafica();
    } else {
      setLoadingData(false);
    }
    void loadTipiCliente();
  }, [id, isEdit, loadAnagrafica, loadTipiCliente]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => {
      const newData = { ...prev, [name]: value };
      
      // Per PG: quando cambia CF, precompila P.IVA con stesso valore
      if (prev.tipo === 'PG' && name === 'codice_fiscale' && value.length === 11) {
        newData.partita_iva = value;
      }
      
      return newData;
    });
    
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Validazione tipo soggetto
    if (!formData.tipo) {
      newErrors.tipo = 'Tipo soggetto obbligatorio';
    }

    // Validazione Persona Giuridica
    if (formData.tipo === 'PG') {
      if (!formData.ragione_sociale.trim()) {
        newErrors.ragione_sociale = 'Ragione sociale obbligatoria per Persona Giuridica';
      }
    }

    // Validazione Persona Fisica
    if (formData.tipo === 'PF') {
      if (!formData.nome.trim()) {
        newErrors.nome = 'Nome obbligatorio per Persona Fisica';
      }
      if (!formData.cognome.trim()) {
        newErrors.cognome = 'Cognome obbligatorio per Persona Fisica';
      }
    }

    // Validazione Codice Fiscale
    if (!formData.codice_fiscale.trim()) {
      newErrors.codice_fiscale = 'Codice fiscale obbligatorio';
    } else {
      const cf = formData.codice_fiscale.trim().toUpperCase();
      if (formData.tipo === 'PF') {
        // CF Persona Fisica: 16 caratteri alfanumerici
        if (cf.length !== 16) {
          newErrors.codice_fiscale = 'Il codice fiscale deve essere di 16 caratteri';
        } else if (!/^[A-Z0-9]{16}$/.test(cf)) {
          newErrors.codice_fiscale = 'Codice fiscale non valido';
        }
      } else {
        // CF Persona Giuridica: 11 cifre numeriche
        if (cf.length !== 11) {
          newErrors.codice_fiscale = 'Il codice fiscale PG deve essere di 11 cifre';
        } else if (!/^\d{11}$/.test(cf)) {
          newErrors.codice_fiscale = 'Il codice fiscale PG deve contenere solo numeri';
        }
      }
    }

    // Validazione Partita IVA (opzionale, ma se presente deve essere valida)
    if (formData.partita_iva.trim()) {
      const piva = formData.partita_iva.trim();
      if (piva.length !== 11) {
        newErrors.partita_iva = 'La partita IVA deve essere di 11 cifre';
      } else if (!/^\d{11}$/.test(piva)) {
        newErrors.partita_iva = 'La partita IVA deve contenere solo numeri';
      }
    }

    // Validazione Email (opzionale, ma se presente deve essere valida)
    if (formData.email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        newErrors.email = 'Email non valida';
      }
    }

    // Validazione PEC (opzionale, ma se presente deve essere valida)
    if (formData.pec.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.pec)) {
        newErrors.pec = 'PEC non valida';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);

      // Prepare data (uppercase CF)
      // NOTA: indirizzo, email, pec sono READ-ONLY e sincronizzati automaticamente
      const submitData: Record<string, unknown> = {
        tipo: formData.tipo,
        ragione_sociale: formData.tipo === 'PG' ? formData.ragione_sociale.trim() : '',
        nome: formData.tipo === 'PF' ? formData.nome.trim() : '',
        cognome: formData.tipo === 'PF' ? formData.cognome.trim() : '',
        codice_fiscale: formData.codice_fiscale.trim().toUpperCase(),
        partita_iva: formData.partita_iva.trim() || '',
        telefono: formData.telefono.trim() || '',
        note: formData.note.trim() || '',
        // NON inviamo: indirizzo, email, pec (gestiti da signal backend)
      };
      
      // Dati Cliente (se flag attivo)
      if (formData.is_cliente) {
        submitData.is_cliente = true;
        submitData.cliente_dal = formData.cliente_dal || null;
        submitData.cliente_al = formData.cliente_al || null;
        submitData.codice_destinatario = formData.codice_destinatario.trim() || '';
        submitData.tipo_cliente = formData.tipo_cliente || null;
      }

      // In modifica, includi il codice se presente
      if (isEdit && formData.codice) {
        submitData.codice = formData.codice;
      }

      if (isEdit && id) {
        await apiClient.put(`/anagrafiche/${id}/`, submitData);
        alert('Anagrafica aggiornata con successo!');
        navigate(`/anagrafiche/${id}`);
      } else {
        const response = await apiClient.post('/anagrafiche/', submitData);
        alert('Anagrafica creata con successo!');
        navigate(`/anagrafiche/${response.data.id}`);
      }
    } catch (error: unknown) {
      if (isAxiosError(error) && error.response?.data) {
        const responseData = error.response.data as Record<string, string | string[]>;
        const serverErrors: FormErrors = {};
        Object.entries(responseData).forEach(([key, messages]) => {
          serverErrors[key] = Array.isArray(messages) ? messages.join(', ') : messages;
        });
        setErrors(serverErrors);
      } else {
        alert((error instanceof Error ? error.message : undefined) || 'Errore nel salvataggio dell\'anagrafica');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="page-container">
        <h1>{isEdit ? 'Modifica Anagrafica' : 'Nuova Anagrafica'}</h1>
        <p>Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>{isEdit ? '✏️ Modifica Anagrafica' : '➕ Nuova Anagrafica'}</h1>
        <Link to="/anagrafiche" className="btn-secondary">
          <ArrowBackIcon size={18} />
          <span>Torna alla lista</span>
        </Link>
      </div>

      <form onSubmit={handleSubmit} className="form-card">
        {/* Tipo Soggetto */}
        <div className="form-section">
          <h2>Tipo Soggetto</h2>
          <div className="form-group">
            <label htmlFor="tipo">Tipo *</label>
            <select
              id="tipo"
              name="tipo"
              value={formData.tipo}
              onChange={handleChange}
              className={errors.tipo ? 'error' : ''}
              disabled={isEdit} // Non permettere cambio tipo in modifica
            >
              <option value="PF">Persona Fisica</option>
              <option value="PG">Persona Giuridica</option>
            </select>
            {errors.tipo && <span className="error-message">{errors.tipo}</span>}
          </div>
        </div>

        {/* Dati Identificativi */}
        <div className="form-section">
          <h2>Dati Identificativi</h2>
          
          {formData.tipo === 'PG' ? (
            <div className="form-group">
              <label htmlFor="ragione_sociale">Ragione Sociale *</label>
              <input
                type="text"
                id="ragione_sociale"
                name="ragione_sociale"
                value={formData.ragione_sociale}
                onChange={handleChange}
                className={errors.ragione_sociale ? 'error' : ''}
                placeholder="Es. Rossi S.r.l."
              />
              {errors.ragione_sociale && <span className="error-message">{errors.ragione_sociale}</span>}
            </div>
          ) : (
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="nome">Nome *</label>
                <input
                  type="text"
                  id="nome"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  className={errors.nome ? 'error' : ''}
                  placeholder="Es. Mario"
                />
                {errors.nome && <span className="error-message">{errors.nome}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="cognome">Cognome *</label>
                <input
                  type="text"
                  id="cognome"
                  name="cognome"
                  value={formData.cognome}
                  onChange={handleChange}
                  className={errors.cognome ? 'error' : ''}
                  placeholder="Es. Rossi"
                />
                {errors.cognome && <span className="error-message">{errors.cognome}</span>}
              </div>
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="codice_fiscale">
                Codice Fiscale * {formData.tipo === 'PF' ? '(16 caratteri)' : '(11 cifre)'}
              </label>
              <input
                type="text"
                id="codice_fiscale"
                name="codice_fiscale"
                value={formData.codice_fiscale}
                onChange={handleChange}
                className={errors.codice_fiscale ? 'error' : ''}
                placeholder={formData.tipo === 'PF' ? 'RSSMRA80A01H501X' : '12345678901'}
                maxLength={16}
                style={{ textTransform: 'uppercase' }}
              />
              {errors.codice_fiscale && <span className="error-message">{errors.codice_fiscale}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="partita_iva">Partita IVA (11 cifre)</label>
              <input
                type="text"
                id="partita_iva"
                name="partita_iva"
                value={formData.partita_iva}
                onChange={handleChange}
                className={errors.partita_iva ? 'error' : ''}
                placeholder="12345678901"
                maxLength={11}
              />
              {errors.partita_iva && <span className="error-message">{errors.partita_iva}</span>}
            </div>
          </div>

          {/* Codice interno - solo visualizzazione in modifica */}
          {isEdit && formData.codice && (
            <div className="form-group">
              <label htmlFor="codice">Codice Interno (generato automaticamente)</label>
              <input
                type="text"
                id="codice"
                name="codice"
                value={formData.codice}
                disabled
                style={{ background: 'var(--background)', cursor: 'not-allowed' }}
              />
              <small style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                Il codice viene generato automaticamente al momento della creazione
              </small>
            </div>
          )}
        </div>

        {/* Contatti */}
        <div className="form-section">
          <h2>Contatti</h2>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="pec">
                PEC 
                <small style={{ marginLeft: '0.5rem', color: '#666', fontWeight: 'normal' }}>
                  (sincronizzato da contatto PEC preferito)
                </small>
              </label>
              <input
                type="email"
                id="pec"
                name="pec"
                value={formData.pec}
                readOnly
                disabled
                className="read-only"
                placeholder="Verrà sincronizzato dal contatto email PEC preferito"
                style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
              />
              <small style={{ color: '#666', fontSize: '0.85em' }}>
                ℹ️ Gestisci i contatti PEC nella sezione "Contatti Email" dalla pagina dettaglio
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="email">
                Email
                <small style={{ marginLeft: '0.5rem', color: '#666', fontWeight: 'normal' }}>
                  (sincronizzato da contatto Generico preferito)
                </small>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                readOnly
                disabled
                className="read-only"
                placeholder="Verrà sincronizzato dal contatto email Generico preferito"
                style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
              />
              <small style={{ color: '#666', fontSize: '0.85em' }}>
                ℹ️ Gestisci le email nella sezione "Contatti Email" dalla pagina dettaglio
              </small>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="telefono">Telefono</label>
              <input
                type="tel"
                id="telefono"
                name="telefono"
                value={formData.telefono}
                onChange={handleChange}
                placeholder="+39 123 4567890"
              />
            </div>

            <div className="form-group">
              <label htmlFor="indirizzo">
                Indirizzo
                <small style={{ marginLeft: '0.5rem', color: '#666', fontWeight: 'normal' }}>
                  (sincronizzato da indirizzo principale)
                </small>
              </label>
              <input
                type="text"
                id="indirizzo"
                name="indirizzo"
                value={formData.indirizzo}
                readOnly
                disabled
                className="read-only"
                placeholder="Verrà sincronizzato dall'indirizzo principale"
                style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
              />
              <small style={{ color: '#666', fontSize: '0.85em' }}>
                ℹ️ Gestisci gli indirizzi nella sezione "Indirizzi" dalla pagina dettaglio
              </small>
            </div>
          </div>
        </div>

        {/* Gestione Cliente */}
        <div className="form-section">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h2>🛍️ Gestione Cliente</h2>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
              <input
                type="checkbox"
                name="is_cliente"
                checked={formData.is_cliente}
                onChange={(e) => setFormData(prev => ({ ...prev, is_cliente: e.target.checked }))}
                style={{ cursor: 'pointer' }}
              />
              <span>Converti in Cliente</span>
            </label>
          </div>

          {formData.is_cliente && (
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="cliente_dal">Cliente dal</label>
                <input
                  type="date"
                  id="cliente_dal"
                  name="cliente_dal"
                  value={formData.cliente_dal}
                  onChange={handleChange}
                />
                <small style={{ color: 'var(--text-muted)' }}>Data inizio rapporto cliente</small>
              </div>

              <div className="form-group">
                <label htmlFor="cliente_al">Cliente al</label>
                <input
                  type="date"
                  id="cliente_al"
                  name="cliente_al"
                  value={formData.cliente_al}
                  onChange={handleChange}
                />
                <small style={{ color: 'var(--text-muted)' }}>Data fine rapporto cliente (opzionale)</small>
              </div>

              <div className="form-group">
                <label htmlFor="codice_destinatario">Codice Destinatario SDI</label>
                <input
                  type="text"
                  id="codice_destinatario"
                  name="codice_destinatario"
                  value={formData.codice_destinatario}
                  onChange={handleChange}
                  placeholder="XXXXXXX (7 caratteri)"
                  maxLength={7}
                  style={{ textTransform: 'uppercase' }}
                />
                <small style={{ color: 'var(--text-muted)' }}>
                  Codice per fatturazione elettronica (7 caratteri)
                </small>
              </div>

              <div className="form-group">
                <label htmlFor="tipo_cliente">Tipo Cliente</label>
                <select
                  id="tipo_cliente"
                  name="tipo_cliente"
                  value={formData.tipo_cliente || ''}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    tipo_cliente: e.target.value ? Number(e.target.value) : null 
                  }))}
                >
                  <option value="">-- Seleziona tipo cliente --</option>
                  {tipiCliente.map(tipo => (
                    <option key={tipo.id} value={tipo.id}>
                      {tipo.descrizione}
                    </option>
                  ))}
                </select>
                <small style={{ color: 'var(--text-muted)' }}>
                  Classificazione del cliente (es. Privato, Azienda, Ente)
                </small>
              </div>
            </div>
          )}

          {!formData.is_cliente && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
              Attiva il flag "Converti in Cliente" per visualizzare i campi specifici per la gestione del cliente (date rapporto e codice destinatario SDI).
            </p>
          )}
        </div>

        {/* Note */}
        <div className="form-section">
          <h2>Note</h2>
          <div className="form-group">
            <label htmlFor="note">Note aggiuntive</label>
            <textarea
              id="note"
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows={4}
              placeholder="Inserisci eventuali note..."
            />
          </div>
        </div>

        {/* Actions */}
        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={loading}>
            <CheckIcon size={18} />
            <span>{loading ? 'Salvataggio...' : isEdit ? 'Aggiorna' : 'Crea'}</span>
          </button>
          <Link to="/anagrafiche" className="btn-secondary">
            Annulla
          </Link>
        </div>
      </form>
    </div>
  );
}

const extractAnagraficaError = (error: unknown): string | null => {
  if (isAxiosError(error)) {
    const data = error.response?.data as { detail?: string; error?: string } | undefined;
    return data?.detail ?? data?.error ?? error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return null;
};
