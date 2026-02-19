import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { documentiApi } from '@/api/documenti';
import { fascicoliApi } from '@/api/fascicoli';
import { apiClient } from '@/api/client';
import type {
  DocumentoFormData,
  DocumentiTipo,
  AttributoDefinizione,
  AttributoValore,
  Cliente,
  DocumentoJsonPayload,
  AttributiPayload,
} from '@/types/documento';
import type { Fascicolo, TitolarioVoce, UnitaFisica } from '@/types/fascicolo';
import { ArrowBackIcon, CheckIcon, DocumentiIcon } from '@/components/icons/Icons';
import { ClienteAutocomplete } from '@/components/ClienteAutocomplete';
import { TitolarioAutocomplete } from '@/components/TitolarioAutocomplete';
import { TipoDocumentoAutocomplete } from '@/components/TipoDocumentoAutocomplete';
import { AnagraficaAutocomplete, type AnagraficaOption } from '@/components/AnagraficaAutocomplete';
import { FileSourceInfo } from '@/components/FileSourceInfo';

type ClientiApiResponse = Cliente[] | { results?: Cliente[] };

interface FormErrors {
  [key: string]: string;
}

export function DocumentoFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fascicoloId = searchParams.get('fascicolo_id');
  const isEdit = !!id;

  const [formData, setFormData] = useState<DocumentoFormData>({
    tipo: 0,
    descrizione: '',
    data_documento: new Date().toISOString().split('T')[0],
    stato: 'bozza',
    digitale: true,
    tracciabile: true,
    file_operation: 'copy',
    fascicolo: fascicoloId ? Number(fascicoloId) : undefined,
    ubicazione: undefined,
  });

  const [tipiDocumento, setTipiDocumento] = useState<DocumentiTipo[]>([]);
  const [attributi, setAttributi] = useState<AttributoDefinizione[]>([]);
  const [clienti, setClienti] = useState<Cliente[]>([]);
  const [titolarioVoci, setTitolarioVoci] = useState<TitolarioVoce[]>([]);
  const [unitaFisiche, setUnitaFisiche] = useState<UnitaFisica[]>([]);
  const [fascicolo, setFascicolo] = useState<Fascicolo | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(isEdit);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [existingFile, setExistingFile] = useState<{ name: string; url: string } | null>(null);
  const [removeFile, setRemoveFile] = useState(false);
  
  // Stato per eliminazione file originale
  const [sourceFilePath, setSourceFilePath] = useState('');
  const [deleteSourceFile, setDeleteSourceFile] = useState(false);
  
  // Stato per anagrafiche selezionate negli attributi dinamici
  const [anagraficheAttributi, setAnagraficheAttributi] = useState<Record<string, AnagraficaOption | null>>({});

  const getErrorMessage = (err: unknown, fallback: string) => {
    if (isAxiosError(err)) {
      const data = err.response?.data;
      if (data?.detail) {
        return data.detail;
      }
      if (data?.message) {
        return data.message;
      }
      if (data && typeof data === 'object') {
        const firstKey = Object.keys(data)[0];
        if (firstKey) {
          const value = (data as Record<string, unknown>)[firstKey];
          if (Array.isArray(value) && value.length > 0) {
            return String(value[0]);
          }
          if (typeof value === 'string') {
            return value;
          }
        }
      }
      return err.message || fallback;
    }
    if (err instanceof Error) {
      return err.message;
    }
    return fallback;
  };

  const loadTipiDocumento = useCallback(async () => {
    try {
      const data = await documentiApi.listTipi();
      setTipiDocumento(data);
    } catch (err) {
      console.error('Error loading tipi documento:', err);
    }
  }, []);

  const loadClienti = useCallback(async () => {
    try {
      const response = await apiClient.get<ClientiApiResponse>('/clienti/');
      const clientiArray = Array.isArray(response.data)
        ? response.data
        : response.data.results || [];
      setClienti(clientiArray);
    } catch (err) {
      console.error('Error loading clienti:', err);
    }
  }, []);

  const loadTitolarioVoci = useCallback(async () => {
    try {
      const data = await fascicoliApi.listTitolarioVoci();
      setTitolarioVoci(data);
    } catch (err) {
      console.error('Error loading titolario voci:', err);
    }
  }, []);

  const loadUnitaFisiche = useCallback(async () => {
    try {
      const data = await fascicoliApi.listUnitaFisiche();
      setUnitaFisiche(data);
    } catch (err) {
      console.error('Error loading unità fisiche:', err);
    }
  }, []);

  const loadFascicolo = useCallback(async () => {
    if (!fascicoloId) return;

    try {
      const data = await fascicoliApi.get(Number(fascicoloId));
      setFascicolo(data);

      setFormData((prev) => ({
        ...prev,
        cliente: data.cliente || undefined,
        titolario_voce: data.titolario_voce || undefined,
        ubicazione: data.ubicazione || undefined,
      }));
    } catch (err) {
      console.error('Error loading fascicolo:', err);
    }
  }, [fascicoloId]);

  const loadTipoDettaglio = useCallback(async (tipoId: number) => {
    try {
      const data = await documentiApi.getTipo(tipoId);
      setAttributi(data.attributi || []);
    } catch (err) {
      console.error('Error loading tipo dettaglio:', err);
    }
  }, []);

  const loadDocumento = useCallback(async () => {
    if (!id) return;

    try {
      setLoadingData(true);
      const data = await documentiApi.get(Number(id));

      if (data.tipo) {
        const tipoData = await documentiApi.getTipo(data.tipo);
        setAttributi(tipoData.attributi || []);
      }

      const newFormData: DocumentoFormData = {
        tipo: data.tipo,
        cliente: data.cliente,
        fascicolo: data.fascicolo,
        titolario_voce: data.titolario_voce,
        ubicazione: data.ubicazione ?? undefined,
        descrizione: data.descrizione,
        data_documento: data.data_documento,
        stato: data.stato,
        digitale: data.digitale,
        tracciabile: data.tracciabile,
        tags: data.tags,
        note: data.note,
        file_operation: 'copy',
      };

      if (data.attributi && Array.isArray(data.attributi)) {
        const newAnagraficheAttributi: Record<string, AnagraficaOption | null> = {};
        
        data.attributi.forEach((attr: AttributoValore) => {
          const codice = attr.definizione_detail?.codice || attr.definizione;
          if (codice) {
            newFormData[`attr_${codice}`] = attr.valore;
            
            // Se l'attributo è di tipo anagrafica, carica l'anagrafica
            const def = attributi.find(a => a.codice === codice);
            if (def && def.tipo_dato === 'int' && 
                def.widget && ['anagrafica', 'fk_anagrafica', 'anag'].includes(def.widget.toLowerCase())) {
              const anagraficaId = attr.valore;
              if (anagraficaId) {
                // Carica l'anagrafica dal server
                apiClient.get(`/anagrafiche/${anagraficaId}/`)
                  .then(response => {
                    newAnagraficheAttributi[codice] = response.data;
                    setAnagraficheAttributi(prev => ({
                      ...prev,
                      [codice]: response.data
                    }));
                  })
                  .catch(err => {
                    console.error(`Errore caricamento anagrafica ${anagraficaId}:`, err);
                  });
              }
            }
          }
        });
      }

      setFormData(newFormData);

      if (data.ubicazione_detail) {
        setUnitaFisiche((prev) => {
          if (prev.some((u) => u.id === data.ubicazione_detail?.id)) {
            return prev;
          }
          return [...prev, data.ubicazione_detail as UnitaFisica];
        });
      }

      if (data.file) {
        setExistingFile({
          name: data.file_name || 'File esistente',
          url: data.file_url || data.file,
        });
        setFilePreview(data.file_name || 'File esistente');
      }
    } catch (err) {
      console.error('Error loading documento:', err);
      alert(getErrorMessage(err, 'Errore nel caricamento del documento'));
      navigate('/documenti');
    } finally {
      setLoadingData(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    loadTipiDocumento();
    loadClienti();
    loadTitolarioVoci();
    loadUnitaFisiche();
  }, [loadTipiDocumento, loadClienti, loadTitolarioVoci, loadUnitaFisiche]);

  useEffect(() => {
    if (fascicoloId) {
      loadFascicolo();
    }
  }, [fascicoloId, loadFascicolo]);

  useEffect(() => {
    if (isEdit && id) {
      loadDocumento();
    }
  }, [id, isEdit, loadDocumento]);

  useEffect(() => {
    if (formData.tipo && !loadingData) {
      loadTipoDettaglio(formData.tipo);
    }
  }, [formData.tipo, loadingData, loadTipoDettaglio]);

  const getAttributeInputValue = (code: string): string => {
    const value = formData[`attr_${code}`];
    if (typeof value === 'number' || typeof value === 'string') {
      return String(value);
    }
    return '';
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    let processedValue: string | number | boolean | undefined =
      type === 'checkbox' ? checked : value;

    if (name === 'tipo') {
      processedValue = value ? Number(value) : 0;
    } else if (name === 'cliente' || name === 'fascicolo' || name === 'titolario_voce') {
      processedValue = value ? Number(value) : undefined;
    } else if (name === 'ubicazione') {
      processedValue = value ? Number(value) : undefined;
    }

    setFormData((prev) => {
      const next = {
        ...prev,
        [name]: processedValue,
      } as DocumentoFormData;
      if (name === 'digitale' && processedValue === true) {
        next.ubicazione = undefined;
      }
      return next;
    });

    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData((prev) => ({ ...prev, file }));
      setFilePreview(file.name);
      setRemoveFile(false); // Se carico un nuovo file, non devo rimuoverlo
    }
  };

  const handleRemoveFile = () => {
    setFormData((prev) => ({ ...prev, file: undefined }));
    setFilePreview(null);
    setExistingFile(null);
    setRemoveFile(true);
  };

  const handleDownloadFile = () => {
    if (existingFile?.url) {
      window.open(existingFile.url, '_blank');
    }
  };
  
  const handleSourcePathChange = (path: string, shouldDelete: boolean) => {
    setSourceFilePath(path);
    setDeleteSourceFile(shouldDelete);
  };

  const buildAttributiPayload = (): AttributiPayload => {
    const attributiData: AttributiPayload = {};
    attributi.forEach((attr) => {
      const fieldName = `attr_${attr.codice}`;
      const value = formData[fieldName];
      if (value !== undefined && value !== null && value !== '') {
        attributiData[attr.codice] = value as string | number | boolean;
      }
    });
    return attributiData;
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    const needsUbicazione = !formData.digitale && !formData.fascicolo;

    if (!formData.tipo) {
      newErrors.tipo = 'Il tipo documento è obbligatorio';
    }

    if (!formData.descrizione?.trim()) {
      newErrors.descrizione = 'La descrizione è obbligatoria';
    }

    if (!formData.data_documento) {
      newErrors.data_documento = 'La data documento è obbligatoria';
    }

    if (!formData.cliente && !formData.fascicolo) {
      newErrors.cliente = 'Il cliente è obbligatorio se non è specificato un fascicolo';
    }

    if (needsUbicazione && !formData.ubicazione) {
      newErrors.ubicazione = "L'ubicazione è obbligatoria per i documenti cartacei senza fascicolo";
    }

    // Valida attributi obbligatori
    attributi.forEach((attr) => {
      if (attr.obbligatorio) {
        const fieldName = `attr_${attr.codice}`;
        if (!formData[fieldName]) {
          newErrors[fieldName] = `${attr.nome} è obbligatorio`;
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      alert('Correggi gli errori nel form');
      return;
    }

    try {
      setLoading(true);

      // Determina se c'è un nuovo file da caricare
      const hasNewFile = formData.file instanceof File;

      let submitData: FormData | DocumentoJsonPayload;

      if (hasNewFile) {
        // Usa FormData se c'è un nuovo file
        submitData = new FormData();
        const formPayload = submitData as FormData;
        
        // Campi base
        Object.entries(formData).forEach(([key, value]) => {
          if (key === 'file' && value instanceof File) {
            formPayload.append('file', value);
          } else if (key.startsWith('attr_')) {
            // Skip - gestiti separatamente
          } else if (value !== undefined && value !== null && value !== '' && !(key === 'tipo' && value === 0)) {
            formPayload.append(key, String(value));
          }
        });

        // Attributi dinamici
        const attributiData = buildAttributiPayload();

        if (Object.keys(attributiData).length > 0) {
          formPayload.append('attributi', JSON.stringify(attributiData));
        }
        
        // Aggiungi campi per eliminazione file originale
        if (deleteSourceFile && sourceFilePath.trim()) {
          formPayload.append('delete_source_file', 'true');
          formPayload.append('source_file_path', sourceFilePath.trim());
        }
      } else {
        const payload: DocumentoJsonPayload = {
          tipo: formData.tipo || undefined,
          cliente: formData.cliente || undefined,
          fascicolo: formData.fascicolo || undefined,
          titolario_voce: formData.titolario_voce || undefined,
          ubicazione: formData.ubicazione ?? null,
          descrizione: formData.descrizione,
          data_documento: formData.data_documento,
          stato: formData.stato,
          digitale: formData.digitale,
          tracciabile: formData.tracciabile,
          file_operation: formData.file_operation,
          tags: formData.tags || '',
          note: formData.note || '',
        };

        if (removeFile) {
          payload.file = null;
        }

        const attributiData = buildAttributiPayload();
        if (Object.keys(attributiData).length > 0) {
          payload.attributi = attributiData;
        }

        if (!isEdit && deleteSourceFile && sourceFilePath.trim()) {
          payload.delete_source_file = true;
          payload.source_file_path = sourceFilePath.trim();
        }

        submitData = payload;
      }

      if (isEdit && id) {
        await documentiApi.update(Number(id), submitData);
        alert('Documento aggiornato con successo!');
      } else {
        await documentiApi.create(submitData);
        alert('Documento creato con successo!');
      }

      // Se c'è fascicolo_id, torna al fascicolo, altrimenti alla lista documenti
      if (fascicoloId) {
        navigate(`/fascicoli/${fascicoloId}`);
      } else {
        navigate('/documenti');
      }
    } catch (err) {
      console.error('Error saving documento:', err);
      if (isAxiosError(err) && err.response?.status === 400 && err.response.data && typeof err.response.data === 'object') {
        const apiErrors: FormErrors = {};
        Object.entries(err.response.data as Record<string, unknown>).forEach(([field, value]) => {
          if (Array.isArray(value) && value.length > 0) {
            apiErrors[field] = String(value[0]);
          } else if (typeof value === 'string') {
            apiErrors[field] = value;
          }
        });
        if (Object.keys(apiErrors).length > 0) {
          setErrors(apiErrors);
        }
      }
      alert(getErrorMessage(err, 'Errore nel salvataggio del documento'));
    } finally {
      setLoading(false);
    }
  };

  const requiresUbicazione = !formData.digitale && !formData.fascicolo;
  const shouldShowUbicazioneField = !formData.digitale || Boolean(formData.ubicazione);

  if (loadingData) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <DocumentiIcon size={32} />
            {isEdit ? 'Modifica Documento' : 'Nuovo Documento'}
          </h1>
          <p className="text-muted">
            {isEdit ? 'Aggiorna i dati del documento' : 'Inserisci i dati del nuovo documento'}
          </p>
        </div>
        <Link to="/documenti" className="btn-secondary">
          <ArrowBackIcon size={18} />
          <span>Annulla</span>
        </Link>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Informazioni Base */}
          <div className="card">
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
              Informazioni Base
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
              {/* Tipo Documento */}
              <div className="form-group">
                <label>
                  Tipo Documento <span style={{ color: '#dc3545' }}>*</span>
                </label>
                <TipoDocumentoAutocomplete
                  value={formData.tipo || null}
                  tipi={tipiDocumento}
                  onChange={(tipoId) => {
                    setFormData(prev => ({ ...prev, tipo: tipoId || 0 }));
                    // Carica gli attributi del tipo selezionato
                    if (tipoId && !loadingData) {
                      loadTipoDettaglio(tipoId);
                    } else {
                      setAttributi([]);
                    }
                  }}
                  disabled={loading}
                  required
                  placeholder="Cerca per codice o nome..."
                />
                {errors.tipo && <span style={{ color: '#dc3545', fontSize: '0.875rem' }}>{errors.tipo}</span>}
              </div>

              {/* Data Documento */}
              <div className="form-group">
                <label>
                  Data Documento <span style={{ color: '#dc3545' }}>*</span>
                </label>
                <input
                  type="date"
                  name="data_documento"
                  value={formData.data_documento}
                  onChange={handleChange}
                  className="form-control"
                  required
                />
                {errors.data_documento && (
                  <span style={{ color: '#dc3545', fontSize: '0.875rem' }}>{errors.data_documento}</span>
                )}
              </div>

              {/* Cliente */}
              <div className="form-group">
                <label>Cliente</label>
                <ClienteAutocomplete
                  value={formData.cliente || null}
                  clienti={clienti}
                  onChange={(clienteId) => setFormData(prev => ({ ...prev, cliente: clienteId || undefined }))}
                  disabled={loading}
                  placeholder="Cerca cliente per nome, CF o P.IVA..."
                />
                {errors.cliente && (
                  <span style={{ color: '#dc3545', fontSize: '0.875rem' }}>{errors.cliente}</span>
                )}
                {fascicoloId && fascicolo && (
                  <small style={{ color: '#6b7280', marginTop: '0.25rem', display: 'block' }}>
                    Cliente ereditato dal fascicolo {fascicolo.codice} (modificabile)
                  </small>
                )}
              </div>

              {/* Titolario Voce */}
              <div className="form-group">
                <label>Voce Titolario</label>
                <TitolarioAutocomplete
                  value={formData.titolario_voce || null}
                  voci={titolarioVoci}
                  onChange={(voceId) => setFormData(prev => ({ ...prev, titolario_voce: voceId || undefined }))}
                  disabled={loading}
                  placeholder="Cerca voce di titolario..."
                />
                {fascicoloId && fascicolo && formData.titolario_voce === fascicolo.titolario_voce && (
                  <small style={{ color: '#1976d2', marginTop: '0.25rem', display: 'block' }}>
                    ℹ️ Titolario ereditato dal fascicolo <strong>{fascicolo.codice}</strong>. Usa il pulsante "Cambia" per modificarlo.
                  </small>
                )}
                {fascicoloId && fascicolo && formData.titolario_voce !== fascicolo.titolario_voce && (
                  <small style={{ color: '#f57c00', marginTop: '0.25rem', display: 'block' }}>
                    ⚠️ Titolario diverso da quello del fascicolo ({fascicolo.titolario_voce_detail?.codice || fascicolo.titolario_voce}).
                  </small>
                )}
              </div>

              {shouldShowUbicazioneField && (
                <div className="form-group">
                  <label>
                    Ubicazione fisica {requiresUbicazione && <span style={{ color: '#dc3545' }}>*</span>}
                  </label>
                  <select
                    name="ubicazione"
                    value={formData.ubicazione ?? ''}
                    onChange={handleChange}
                    className="form-control"
                    disabled={loading || formData.digitale}
                  >
                    <option value="">{formData.digitale ? 'Non richiesto per documenti digitali' : 'Seleziona ubicazione'}</option>
                    {unitaFisiche.map((unita) => (
                      <option key={unita.id} value={unita.id}>
                        {unita.codice} - {unita.nome}
                      </option>
                    ))}
                  </select>
                  {errors.ubicazione && (
                    <span style={{ color: '#dc3545', fontSize: '0.875rem' }}>{errors.ubicazione}</span>
                  )}
                  {!formData.digitale && (
                    <small style={{ color: '#6b7280', marginTop: '0.25rem', display: 'block' }}>
                      Richiesto per documenti cartacei non collegati a un fascicolo con ubicazione.
                    </small>
                  )}
                </div>
              )}

              {/* Stato */}
              <div className="form-group">
                <label>Stato</label>
                <select
                  name="stato"
                  value={formData.stato}
                  onChange={handleChange}
                  className="form-control"
                >
                  <option value="bozza">Bozza</option>
                  <option value="definitivo">Definitivo</option>
                  <option value="protocollato">Protocollato</option>
                  <option value="archiviato">Archiviato</option>
                  <option value="annullato">Annullato</option>
                </select>
              </div>

              {/* Descrizione - full width */}
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>
                  Descrizione <span style={{ color: '#dc3545' }}>*</span>
                </label>
                <textarea
                  name="descrizione"
                  value={formData.descrizione}
                  onChange={handleChange}
                  className="form-control"
                  rows={3}
                  required
                  placeholder="Descrizione del documento..."
                />
                {errors.descrizione && (
                  <span style={{ color: '#dc3545', fontSize: '0.875rem' }}>{errors.descrizione}</span>
                )}
              </div>

              {/* Note - full width */}
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>Note</label>
                <textarea
                  name="note"
                  value={formData.note || ''}
                  onChange={handleChange}
                  className="form-control"
                  rows={3}
                  placeholder="Note aggiuntive..."
                />
              </div>

              {/* Tags */}
              <div className="form-group">
                <label>Tags</label>
                <input
                  type="text"
                  name="tags"
                  value={formData.tags || ''}
                  onChange={handleChange}
                  className="form-control"
                  placeholder="tag1, tag2, tag3"
                />
                <small style={{ color: '#6c757d', fontSize: '0.75rem' }}>
                  Separati da virgola
                </small>
              </div>

              {/* Checkboxes */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    name="digitale"
                    checked={formData.digitale}
                    onChange={handleChange}
                  />
                  <span>Digitale</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    name="tracciabile"
                    checked={formData.tracciabile}
                    onChange={handleChange}
                  />
                  <span>Tracciabile</span>
                </label>
              </div>
            </div>
          </div>

          {/* Attributi Personalizzati */}
          {attributi.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
                Attributi Personalizzati
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                {attributi.map((attr) => (
                  <div key={attr.id} className="form-group">
                    <label>
                      {attr.nome}
                      {attr.obbligatorio && <span style={{ color: '#dc3545' }}> *</span>}
                    </label>
                    
                    {/* Widget Anagrafica */}
                    {attr.tipo_dato === 'int' && 
                     attr.widget && ['anagrafica', 'fk_anagrafica', 'anag'].includes(attr.widget.toLowerCase()) ? (
                      <AnagraficaAutocomplete
                        value={anagraficheAttributi[attr.codice] || null}
                        onChange={(anagrafica) => {
                          setAnagraficheAttributi(prev => ({
                            ...prev,
                            [attr.codice]: anagrafica
                          }));
                          setFormData((prev) => ({
                            ...prev,
                            [`attr_${attr.codice}`]: anagrafica?.id || '',
                          }));
                        }}
                        required={attr.obbligatorio}
                        placeholder={`Seleziona ${attr.nome.toLowerCase()}...`}
                      />
                    ) : attr.tipo_dato === 'string' ? (
                      <input
                        type="text"
                        name={`attr_${attr.codice}`}
                        value={getAttributeInputValue(attr.codice)}
                        onChange={handleChange}
                        className="form-control"
                        required={attr.obbligatorio}
                      />
                    ) : (attr.tipo_dato === 'int' || attr.tipo_dato === 'decimal') ? (
                      <input
                        type="number"
                        name={`attr_${attr.codice}`}
                        value={getAttributeInputValue(attr.codice)}
                        onChange={handleChange}
                        className="form-control"
                        required={attr.obbligatorio}
                        step={attr.tipo_dato === 'decimal' ? '0.01' : '1'}
                      />
                    ) : (attr.tipo_dato === 'date' || attr.tipo_dato === 'datetime') ? (
                      <input
                        type="date"
                        name={`attr_${attr.codice}`}
                        value={getAttributeInputValue(attr.codice)}
                        onChange={handleChange}
                        className="form-control"
                        required={attr.obbligatorio}
                      />
                    ) : attr.tipo_dato === 'bool' ? (
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <input
                          type="checkbox"
                          name={`attr_${attr.codice}`}
                          checked={formData[`attr_${attr.codice}`] === 'true' || formData[`attr_${attr.codice}`] === true}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              [`attr_${attr.codice}`]: e.target.checked,
                            }))
                          }
                        />
                        <span>Sì</span>
                      </label>
                    ) : attr.tipo_dato === 'choice' ? (
                      <select
                        name={`attr_${attr.codice}`}
                        value={getAttributeInputValue(attr.codice)}
                        onChange={handleChange}
                        className="form-control"
                        required={attr.obbligatorio}
                      >
                        <option value="">Seleziona...</option>
                        {attr.scelte && attr.scelte.split(',').map((scelta, idx) => {
                          const [value, label] = scelta.trim().includes('|') 
                            ? scelta.trim().split('|') 
                            : [scelta.trim(), scelta.trim()];
                          return (
                            <option key={idx} value={value.trim()}>
                              {label.trim()}
                            </option>
                          );
                        })}
                      </select>
                    ) : null}
                    
                    {errors[`attr_${attr.codice}`] && (
                      <span style={{ color: '#dc3545', fontSize: '0.875rem' }}>
                        {errors[`attr_${attr.codice}`]}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* File Upload */}
          <div className="card">
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>File</h2>
            
            {/* File esistente */}
            {existingFile && !removeFile && !formData.file && (
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#f8f9fa', 
                borderRadius: '0.375rem',
                marginBottom: '1rem',
                border: '1px solid #dee2e6'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: '#28a745' }}><CheckIcon size={20} /></span>
                    <span style={{ fontWeight: '500' }}>File corrente: {existingFile.name}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      type="button"
                      onClick={handleDownloadFile}
                      className="btn-secondary"
                      style={{ padding: '0.375rem 0.75rem', fontSize: '0.875rem' }}
                    >
                      Scarica
                    </button>
                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      className="btn-secondary"
                      style={{ 
                        padding: '0.375rem 0.75rem', 
                        fontSize: '0.875rem',
                        backgroundColor: '#dc3545',
                        borderColor: '#dc3545',
                        color: 'white'
                      }}
                    >
                      Rimuovi
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Messaggio rimozione file */}
            {removeFile && (
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#fff3cd', 
                borderRadius: '0.375rem',
                marginBottom: '1rem',
                border: '1px solid #ffc107',
                color: '#856404'
              }}>
                ⚠️ Il file verrà rimosso al salvataggio
              </div>
            )}
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>{existingFile && !removeFile ? 'Sostituisci File' : 'Carica File'}</label>
                <input
                  type="file"
                  onChange={handleFileChange}
                  className="form-control"
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                />
                {filePreview && formData.file instanceof File && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#28a745' }}>
                    <CheckIcon size={16} /> Nuovo file: {filePreview}
                  </div>
                )}
                <small style={{ color: '#6c757d', fontSize: '0.75rem' }}>
                  Formati supportati: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG
                </small>
              </div>

              {formData.file && (
                <div className="form-group">
                  <label>Operazione File</label>
                  <select
                    name="file_operation"
                    value={formData.file_operation}
                    onChange={handleChange}
                    className="form-control"
                  >
                    <option value="copy">Copia - Mantiene il file nella directory temporanea</option>
                    <option value="move">Sposta - Rimuove il file dalla directory temporanea</option>
                  </select>
                  <small style={{ color: '#6c757d', fontSize: '0.75rem' }}>
                    <strong>Nota:</strong> Questa opzione gestisce il file nell'archivio del server.
                    Il file originale sul tuo computer non verrà eliminato per ragioni di sicurezza del browser.
                  </small>
                </div>
              )}
            </div>
            
            {/* Eliminazione file originale - Solo in creazione e con file caricato */}
            {!isEdit && formData.file && (
              <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #dee2e6' }}>
                <FileSourceInfo onSourcePathChange={handleSourcePathChange} />
              </div>
            )}
          </div>

          {/* Azioni */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
              <Link to="/documenti" className="btn-secondary">
                Annulla
              </Link>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? (
                  'Salvataggio...'
                ) : (
                  <>
                    <CheckIcon size={18} />
                    <span>{isEdit ? 'Aggiorna' : 'Crea'} Documento</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
