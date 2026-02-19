/**
 * Pagina Form Comunicazione
 * Crea o modifica una comunicazione
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { comunicazioniApi, emailContattiApi, mailingListApi, templatesApi, firmeApi, codiciTributoApi } from '@/api/comunicazioni';
import type { ComunicazioneFormData } from '@/types/comunicazioni';
import {
  TIPO_COMUNICAZIONE_CHOICES,
  DIREZIONE_CHOICES,
} from '@/types/comunicazioni';
import CodiceTributoAutocomplete from '@/components/comunicazioni/CodiceTributoAutocomplete';
import { AnagraficaAutocomplete, type AnagraficaOption } from '@/components/AnagraficaAutocomplete';
import AllegatiManager from '@/components/comunicazioni/AllegatiManager';
import '@/styles/comunicazioni.css';

const ComunicazioneFormPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEdit = !!id;

  // State per il form
  const [formData, setFormData] = useState<ComunicazioneFormData>({
    tipo: 'INFORMATIVA',
    direzione: 'OUT',
    oggetto: '',
    corpo: '',
  });

  const [searchContatti, setSearchContatti] = useState('');
  const [searchListe, setSearchListe] = useState('');
  const [selectedContatti, setSelectedContatti] = useState<number[]>([]);
  const [selectedListe, setSelectedListe] = useState<number[]>([]);
  const [templateFields, setTemplateFields] = useState<Record<string, any>>({});
  const [templateFieldsDisplay, setTemplateFieldsDisplay] = useState<Record<string, string>>({});
  const isLoadingInitialData = useRef(false);

  // Query per comunicazione esistente (in modifica)
  const { data: comunicazione, isLoading: loadingComunicazione } = useQuery({
    queryKey: ['comunicazione', id],
    queryFn: () => comunicazioniApi.get(Number(id)),
    enabled: isEdit,
  });

  // Query per templates
  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => templatesApi.list(),
  });

  // Query per firme
  const { data: firmeData, isLoading: firmeLoading } = useQuery({
    queryKey: ['firme'],
    queryFn: () => firmeApi.list(),
  });

  // Query per template selezionato
  const { data: selectedTemplate } = useQuery({
    queryKey: ['template', formData.template],
    queryFn: () => templatesApi.get(formData.template!),
    enabled: !!formData.template,
  });

  // Query per contatti email
  const { data: contattiData } = useQuery({
    queryKey: ['contatti', searchContatti],
    queryFn: () => emailContattiApi.search(searchContatti),
    enabled: searchContatti.length > 2,
  });

  // Debug searchContatti
  useEffect(() => {
    console.log('🔄 searchContatti cambiato:', searchContatti);
    console.log('📏 Lunghezza:', searchContatti.length);
    console.log('✅ Query abilitata:', searchContatti.length > 2);
    console.log('📦 contattiData:', contattiData);
  }, [searchContatti, contattiData]);

  // Query per liste
  const { data: listeData } = useQuery({
    queryKey: ['liste', searchListe],
    queryFn: () => mailingListApi.search(searchListe),
    enabled: searchListe.length > 2,
  });

  // Carica dati in modifica
  useEffect(() => {
    if (comunicazione) {
      isLoadingInitialData.current = true;
      setFormData({
        tipo: comunicazione.tipo,
        direzione: comunicazione.direzione,
        oggetto: comunicazione.oggetto,
        corpo: comunicazione.corpo,
        corpo_html: comunicazione.corpo_html,
        mittente: comunicazione.mittente,
        destinatari: comunicazione.destinatari,
        template: comunicazione.template,
        firma: comunicazione.firma,
        dati_template: comunicazione.dati_template,
        documento_protocollo: comunicazione.documento_protocollo,
      });
      setSelectedContatti(comunicazione.contatti_destinatari);
      setSelectedListe(comunicazione.liste_destinatari);
      
      // Carica i templateFields dai dati_template salvati
      if (comunicazione.dati_template) {
        setTemplateFields(comunicazione.dati_template);
      }
    }
  }, [comunicazione]);

  // Carica i valori display per i codici tributo e anagrafiche quando si modifica
  useEffect(() => {
    if (!comunicazione || !selectedTemplate || !comunicazione.dati_template) return;
    
    const loadDisplayValues = async () => {
      const displayValues: Record<string, string> = {};
      const contextFields = selectedTemplate.context_fields || [];
      
      for (const field of contextFields) {
        // Carica display per codici tributo
        if (field.field_type === 'codice_tributo' && comunicazione.dati_template[field.key]) {
          try {
            const codiceId = comunicazione.dati_template[field.key];
            const codice = await codiciTributoApi.get(parseInt(codiceId));
            displayValues[field.key] = codice.display;
          } catch (error) {
            console.error(`Errore caricamento codice tributo per ${field.key}:`, error);
          }
        }
        
        // Carica display per anagrafiche (widget anagrafica)
        if (field.field_type === 'integer' && 
            (field.widget === 'anagrafica' || field.widget === 'fk_anagrafica') && 
            comunicazione.dati_template[field.key]) {
          try {
            const anagraficaId = comunicazione.dati_template[field.key];
            // Usa l'API anagrafiche per ottenere il display_name
            const response = await fetch(`/api/v1/anagrafiche/${anagraficaId}/`);
            if (response.ok) {
              const anagrafica = await response.json();
              displayValues[field.key] = anagrafica.display_name || anagrafica.nominativo || `Anagrafica #${anagraficaId}`;
            }
          } catch (error) {
            console.error(`Errore caricamento anagrafica per ${field.key}:`, error);
          }
        }
      }
      
      if (Object.keys(displayValues).length > 0) {
        setTemplateFieldsDisplay(displayValues);
      }
      
      // Dopo aver caricato tutti i display values, segnala che il caricamento è completo
      isLoadingInitialData.current = false;
    };
    
    loadDisplayValues();
  }, [comunicazione, selectedTemplate]);

  // Popola oggetto e corpo quando viene selezionato un template
  useEffect(() => {
    if (selectedTemplate && !isEdit) {
      // Solo in creazione, non in modifica
      setFormData((prev) => ({
        ...prev,
        oggetto: selectedTemplate.oggetto || prev.oggetto,
        corpo: selectedTemplate.corpo_testo || prev.corpo,
        corpo_html: selectedTemplate.corpo_html || prev.corpo_html,
      }));
    }
  }, [selectedTemplate, isEdit]);

  /*
  // Funzione per rendere il template con i valori dei campi (rendering lato client semplificato)
  // DISABILITATO: Il rendering ora avviene sul backend
  const renderTemplate = (text: string): string => {
    if (!text) return text;
    let rendered = text;
    
    // Sostituisci tutte le variabili {{ nome_campo }} con i valori
    // NOTA: Questo è un rendering semplificato che non gestisce espressioni complesse come {{cliente.denominazione_anagrafica}}
    // Per un rendering completo, usa l'API render_preview (vedi previewRendered)
    Object.keys(templateFields).forEach((key) => {
      // Usa il valore display se disponibile (per codici tributo/anagrafiche), altrimenti il valore normale
      const value = templateFieldsDisplay[key] || templateFields[key];
      // Sostituisci solo {{key}}, non {{key.attr}}
      const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
      rendered = rendered.replace(regex, value != null ? String(value) : '');
    });
    
    return rendered;
  };
  */

  // State e query per preview renderizzata dal backend
  const [previewRendered, setPreviewRendered] = useState<{oggetto: string, corpo_testo: string} | null>(null);
  
  // Effettua il rendering del template tramite API quando cambiano i campi
  useEffect(() => {
    if (!selectedTemplate) {
      console.log('🔄 Preview: no template selected');
      setPreviewRendered(null);
      return;
    }
    
    console.log('🔄 Preview: chiamata API per template', selectedTemplate.id, 'con campi:', templateFields);
    
    // Debounce per evitare troppe richieste
    const timer = setTimeout(async () => {
      try {
        console.log('📤 POST render_preview con dati:', templateFields);
        
        // Importa apiClient
        const { apiClient } = await import('@/api/client');
        
        // Chiamata API con gestione CSRF per Django
        const response = await apiClient.post(
          `/comunicazioni/templates/${selectedTemplate.id}/render_preview/`,
          { dati_template: templateFields },
          {
            withCredentials: true,
            headers: {
              'X-Requested-With': 'XMLHttpRequest',
            }
          }
        );
        
        console.log('📥 Preview ricevuta:', response.data);
        setPreviewRendered(response.data);
      } catch (error: any) {
        console.error('❌ Errore rendering preview:', error);
        console.error('Response:', error.response?.data);
        console.error('Status:', error.response?.status);
        
        // In caso di errore, mostra almeno il template non renderizzato
        setPreviewRendered({
          oggetto: selectedTemplate.oggetto || '',
          corpo_testo: selectedTemplate.corpo_testo || '',
        });
      }
    }, 500);  // Attendi 500ms dopo l'ultimo cambiamento
    
    return () => clearTimeout(timer);
  }, [selectedTemplate, templateFields]);

  // Aggiorna il corpo quando cambiano i campi del template
  // DISABILITATO: Il rendering dei placeholder ora avviene sul backend con render_content()
  // per applicare correttamente la formattazione definita nei campi del template
  /*
  useEffect(() => {
    // Non aggiornare durante il caricamento iniziale dei dati
    if (isLoadingInitialData.current) {
      return;
    }
    
    if (selectedTemplate && Object.keys(templateFields).length > 0) {
      const renderedCorpo = renderTemplate(selectedTemplate.corpo_testo);
      const renderedOggetto = renderTemplate(selectedTemplate.oggetto);
      const renderedHtml = renderTemplate(selectedTemplate.corpo_html);
      
      setFormData((prev) => ({
        ...prev,
        oggetto: renderedOggetto,
        corpo: renderedCorpo,
        corpo_html: renderedHtml,
      }));
    }
  }, [templateFields, templateFieldsDisplay, selectedTemplate]);
  */

  // Mutation per create
  const createMutation = useMutation({
    mutationFn: (data: ComunicazioneFormData) => comunicazioniApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['comunicazioni'] });
      navigate(`/comunicazioni/${data.id}`);
    },
  });

  // Mutation per update
  const updateMutation = useMutation({
    mutationFn: (data: ComunicazioneFormData) =>
      comunicazioniApi.update(Number(id), data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['comunicazioni'] });
      queryClient.invalidateQueries({ queryKey: ['comunicazione', id] });
      navigate(`/comunicazioni/${data.id}`);
    },
  });

  // Mutation per rigenerare dal template
  const rigeneraMutation = useMutation({
    mutationFn: () => comunicazioniApi.rigenera(Number(id)),
    onSuccess: (response) => {
      // Aggiorna i dati della comunicazione
      queryClient.invalidateQueries({ queryKey: ['comunicazione', id] });
      queryClient.invalidateQueries({ queryKey: ['comunicazioni'] });
      
      // Mostra messaggio di successo
      alert(response.message);
      
      // Ricarica i dati del form
      window.location.reload();
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.error || 'Errore durante la rigenerazione';
      alert(`❌ ${errorMessage}`);
    },
  });

  // Handler per rigenerare
  const handleRigenera = () => {
    if (!comunicazione?.template) {
      alert('⚠️ Questa comunicazione non è stata creata da un template.');
      return;
    }
    
    if (comunicazione?.stato === 'inviata') {
      alert('⚠️ Non è possibile rigenerare una comunicazione già inviata.');
      return;
    }
    
    const conferma = window.confirm(
      '⚠️ ATTENZIONE!\n\n' +
      'Questa operazione sovrascriverà tutte le modifiche manuali ' +
      'apportate al contenuto della comunicazione.\n\n' +
      'Il contenuto verrà rigenerato dal template con i valori aggiornati.\n\n' +
      'Vuoi continuare?'
    );
    
    if (conferma) {
      rigeneraMutation.mutate();
    }
  };

  // Handler cambio campo
  const handleChange = (field: keyof ComunicazioneFormData, value: string | number | null) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Handler submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const dataToSubmit = {
      ...formData,
      contatti_destinatari: selectedContatti,
      liste_destinatari: selectedListe,
      dati_template: Object.keys(templateFields).length > 0 ? templateFields : undefined,
    };

    if (isEdit) {
      updateMutation.mutate(dataToSubmit);
    } else {
      createMutation.mutate(dataToSubmit);
    }
  };

  // Aggiungi contatto alla selezione
  const handleAddContatto = (contattoId: number) => {
    if (!selectedContatti.includes(contattoId)) {
      setSelectedContatti([...selectedContatti, contattoId]);
    }
    setSearchContatti('');
  };

  // Rimuovi contatto dalla selezione
  const handleRemoveContatto = (contattoId: number) => {
    setSelectedContatti(selectedContatti.filter((id) => id !== contattoId));
  };

  // Aggiungi lista alla selezione
  const handleAddLista = (listaId: number) => {
    if (!selectedListe.includes(listaId)) {
      setSelectedListe([...selectedListe, listaId]);
    }
    setSearchListe('');
  };

  // Rimuovi lista dalla selezione
  const handleRemoveLista = (listaId: number) => {
    setSelectedListe(selectedListe.filter((id) => id !== listaId));
  };

  if (isEdit && loadingComunicazione) {
    return <div className="page-container">Caricamento...</div>;
  }

  const isSubmitting = createMutation.isPending || updateMutation.isPending;
  const error = createMutation.error || updateMutation.error;

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <h1>{isEdit ? 'Modifica Comunicazione' : 'Nuova Comunicazione'}</h1>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {isEdit && comunicazione?.template && comunicazione?.stato !== 'inviata' && (
            <button
              type="button"
              className="btn btn-warning"
              onClick={handleRigenera}
              disabled={rigeneraMutation.isPending}
              title="Rigenera il contenuto dal template con i valori aggiornati"
            >
              {rigeneraMutation.isPending ? '⏳ Rigenerazione...' : '🔄 Rigenera da Template'}
            </button>
          )}
          <button
            className="btn btn-secondary"
            onClick={() => navigate(isEdit ? `/comunicazioni/${id}` : '/comunicazioni')}
          >
            ← Indietro
          </button>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-header">
            <h3>Informazioni Principali</h3>
          </div>
          <div className="card-body">
            {error && (
              <div className="alert alert-error">
                Errore: {error instanceof Error ? error.message : 'Errore sconosciuto'}
              </div>
            )}

            <div className="form-grid">
              {/* Tipo */}
              <div className="form-group">
                <label htmlFor="tipo">Tipo *</label>
                <select
                  id="tipo"
                  className="form-control"
                  value={formData.tipo}
                  onChange={(e) => handleChange('tipo', e.target.value)}
                  required
                >
                  {TIPO_COMUNICAZIONE_CHOICES.map((choice) => (
                    <option key={choice.value} value={choice.value}>
                      {choice.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Direzione */}
              <div className="form-group">
                <label htmlFor="direzione">Direzione *</label>
                <select
                  id="direzione"
                  className="form-control"
                  value={formData.direzione}
                  onChange={(e) => handleChange('direzione', e.target.value)}
                  required
                  disabled={isEdit && !!comunicazione?.protocollo_movimento}
                >
                  {DIREZIONE_CHOICES.map((choice) => (
                    <option key={choice.value} value={choice.value}>
                      {choice.label}
                    </option>
                  ))}
                </select>
                {isEdit && comunicazione?.protocollo_movimento && (
                  <small className="form-text">
                    Non modificabile: comunicazione già protocollata
                  </small>
                )}
              </div>

              {/* Oggetto */}
              <div className="form-group full-width">
                <label htmlFor="oggetto">Oggetto *</label>
                <input
                  type="text"
                  id="oggetto"
                  className="form-control"
                  value={formData.oggetto}
                  onChange={(e) => handleChange('oggetto', e.target.value)}
                  required
                  maxLength={255}
                />
              </div>

              {/* Mittente */}
              <div className="form-group full-width">
                <label htmlFor="mittente">Mittente</label>
                <input
                  type="email"
                  id="mittente"
                  className="form-control"
                  value={formData.mittente || ''}
                  onChange={(e) => handleChange('mittente', e.target.value)}
                  placeholder="Lascia vuoto per usare il mittente predefinito"
                />
              </div>

              {/* Template */}
              <div className="form-group">
                <label htmlFor="template">Template</label>
                <select
                  id="template"
                  className="form-control"
                  value={formData.template || ''}
                  onChange={(e) => {
                    const templateId = e.target.value ? Number(e.target.value) : null;
                    handleChange('template', templateId);
                    setTemplateFields({});
                    setTemplateFieldsDisplay({});
                  }}
                >
                  <option value="">Nessun template</option>
                  {templatesData?.results.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.nome}
                    </option>
                  ))}
                </select>
                {templatesLoading && <small className="form-text">Caricamento template...</small>}
              </div>

              {/* Firma */}
              <div className="form-group">
                <label htmlFor="firma">Firma</label>
                <select
                  id="firma"
                  className="form-control"
                  value={formData.firma || ''}
                  onChange={(e) => {
                    const firmaId = e.target.value ? Number(e.target.value) : null;
                    handleChange('firma', firmaId);
                  }}
                >
                  <option value="">Nessuna firma</option>
                  {firmeData?.results.map((firma) => (
                    <option key={firma.id} value={firma.id}>
                      {firma.nome}
                    </option>
                  ))}
                </select>
                {firmeLoading && <small className="form-text">Caricamento firme...</small>}
              </div>

              {/* Campi dinamici del template */}
              {selectedTemplate && selectedTemplate.context_fields.length > 0 && (
                <div className="form-group full-width">
                  <h4 className="mt-3 mb-3">Campi Template: {selectedTemplate.nome}</h4>
                  <div className="form-grid">
                    {selectedTemplate.context_fields.map((field) => {
                      // Debug: log del tipo di campo e widget
                      console.log('Field:', field.key, 'Type:', field.field_type, 'Widget:', field.widget, 'Label:', field.label);
                      return (
                      <div key={field.id} className="form-group">
                        <label htmlFor={`field_${field.key}`}>
                          {field.label || field.key}
                          {field.required && ' *'}
                        </label>
                        
                        {/* Text input */}
                        {field.field_type === 'text' && (
                          <input
                            type="text"
                            id={`field_${field.key}`}
                            className="form-control"
                            value={templateFields[field.key] || field.default_value || ''}
                            onChange={(e) => setTemplateFields(prev => ({
                              ...prev,
                              [field.key]: e.target.value
                            }))}
                            required={field.required}
                            placeholder={field.help_text || ''}
                          />
                        )}

                        {/* Textarea */}
                        {field.field_type === 'textarea' && (
                          <textarea
                            id={`field_${field.key}`}
                            className="form-control"
                            value={templateFields[field.key] || field.default_value || ''}
                            onChange={(e) => setTemplateFields(prev => ({
                              ...prev,
                              [field.key]: e.target.value
                            }))}
                            required={field.required}
                            rows={3}
                            placeholder={field.help_text || ''}
                          />
                        )}

                        {/* Number input (integer/decimal) - con gestione widget anagrafica */}
                        {(field.field_type === 'integer' || field.field_type === 'decimal') && !field.widget && (
                          <input
                            type="number"
                            id={`field_${field.key}`}
                            className="form-control"
                            value={templateFields[field.key] || field.default_value || ''}
                            onChange={(e) => setTemplateFields(prev => ({
                              ...prev,
                              [field.key]: field.field_type === 'integer' 
                                ? parseInt(e.target.value) || ''
                                : parseFloat(e.target.value) || ''
                            }))}
                            required={field.required}
                            step={field.field_type === 'decimal' ? '0.01' : '1'}
                            placeholder={field.help_text || ''}
                          />
                        )}

                        {/* Widget anagrafica per campi integer */}
                        {field.field_type === 'integer' && (field.widget === 'anagrafica' || field.widget === 'fk_anagrafica') && (
                          <AnagraficaAutocomplete
                            value={templateFieldsDisplay[field.key] ? {
                              id: templateFields[field.key],
                              display_name: templateFieldsDisplay[field.key],
                            } as AnagraficaOption : null}
                            onChange={(option) => {
                              if (option) {
                                setTemplateFields(prev => ({
                                  ...prev,
                                  [field.key]: option.id
                                }));
                                setTemplateFieldsDisplay(prev => ({
                                  ...prev,
                                  [field.key]: option.display_name
                                }));
                              } else {
                                setTemplateFields(prev => {
                                  const newFields = { ...prev };
                                  delete newFields[field.key];
                                  return newFields;
                                });
                                setTemplateFieldsDisplay(prev => {
                                  const newDisplay = { ...prev };
                                  delete newDisplay[field.key];
                                  return newDisplay;
                                });
                              }
                            }}
                            required={field.required}
                            placeholder={field.help_text || 'Seleziona un\'anagrafica...'}
                          />
                        )}

                        {/* Date input */}
                        {field.field_type === 'date' && (
                          <input
                            type="date"
                            id={`field_${field.key}`}
                            className="form-control"
                            value={templateFields[field.key] || field.default_value || ''}
                            onChange={(e) => setTemplateFields(prev => ({
                              ...prev,
                              [field.key]: e.target.value
                            }))}
                            required={field.required}
                          />
                        )}

                        {/* Datetime input */}
                        {field.field_type === 'datetime' && (
                          <input
                            type="datetime-local"
                            id={`field_${field.key}`}
                            className="form-control"
                            value={templateFields[field.key] || field.default_value || ''}
                            onChange={(e) => setTemplateFields(prev => ({
                              ...prev,
                              [field.key]: e.target.value
                            }))}
                            required={field.required}
                          />
                        )}

                        {/* Boolean checkbox */}
                        {field.field_type === 'boolean' && (
                          <div className="form-check">
                            <input
                              type="checkbox"
                              id={`field_${field.key}`}
                              className="form-check-input"
                              checked={templateFields[field.key] || field.default_value === 'true' || false}
                              onChange={(e) => setTemplateFields(prev => ({
                                ...prev,
                                [field.key]: e.target.checked
                              }))}
                            />
                            <label className="form-check-label" htmlFor={`field_${field.key}`}>
                              {field.help_text || field.label}
                            </label>
                          </div>
                        )}

                        {/* Choice select */}
                        {field.field_type === 'choice' && field.choices && (
                          <select
                            id={`field_${field.key}`}
                            className="form-control"
                            value={templateFields[field.key] || field.default_value || ''}
                            onChange={(e) => setTemplateFields(prev => ({
                              ...prev,
                              [field.key]: e.target.value
                            }))}
                            required={field.required}
                          >
                            <option value="">Seleziona...</option>
                            {field.choices.split(',').map((choice) => (
                              <option key={choice.trim()} value={choice.trim()}>
                                {choice.trim()}
                              </option>
                            ))}
                          </select>
                        )}

                        {/* Codice Tributo F24 autocomplete */}
                        {field.field_type === 'codice_tributo' && (
                          <CodiceTributoAutocomplete
                            value={templateFields[field.key] || ''}
                            onChange={(value, display) => {
                              setTemplateFields(prev => ({
                                ...prev,
                                [field.key]: value
                              }));
                              if (display) {
                                setTemplateFieldsDisplay(prev => ({
                                  ...prev,
                                  [field.key]: display
                                }));
                              }
                            }}
                            required={field.required}
                          />
                        )}

                        {field.help_text && (
                          <small className="form-text">{field.help_text}</small>
                        )}
                      </div>
                    )})}
                  </div>
                  
                  {/* Preview del testo renderizzato */}
                  {selectedTemplate && (
                    <div className="mt-4 p-3" style={{ backgroundColor: '#f8f9fa', borderRadius: '4px', border: '1px solid #dee2e6' }}>
                      <h5 style={{ marginBottom: '1rem', color: '#495057' }}>📄 Preview Messaggio</h5>
                      {previewRendered ? (
                        <>
                          <div style={{ marginBottom: '1rem' }}>
                            <strong>Oggetto:</strong>
                            <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px' }}
                                 dangerouslySetInnerHTML={{ __html: previewRendered.oggetto }} />
                          </div>
                          <div>
                            <strong>Corpo:</strong>
                            <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', whiteSpace: 'pre-wrap' }}>
                              {previewRendered.corpo_testo}
                            </div>
                          </div>
                        </>
                      ) : (
                        <div style={{ padding: '1rem', textAlign: 'center', color: '#6c757d' }}>
                          <i className="fas fa-spinner fa-spin"></i> Caricamento preview...
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Corpo */}
              <div className="form-group full-width">
                <label htmlFor="corpo">Corpo del Messaggio *</label>
                <textarea
                  id="corpo"
                  className="form-control"
                  value={formData.corpo}
                  onChange={(e) => handleChange('corpo', e.target.value)}
                  required
                  rows={10}
                />
                {selectedTemplate && (
                  <small className="form-text">
                    💡 Puoi usare variabili del template nel formato: {`{{ nome_campo }}`}
                  </small>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Destinatari */}
        <div className="card mt-3">
          <div className="card-header">
            <h3>Destinatari</h3>
          </div>
          <div className="card-body">
            <div className="form-grid">
              {/* Nota esplicativa */}
              <div className="form-group full-width">
                <div className="alert alert-info">
                  <i className="fas fa-info-circle"></i> Per inviare la comunicazione a clienti/anagrafiche, selezionare i contatti email dalla rubrica. 
                  La ricerca filtra anche per denominazione cliente/anagrafica.
                </div>
              </div>

              {/* Destinatari manuali */}
              <div className="form-group full-width">
                <label htmlFor="destinatari">Destinatari (Email separate da virgola)</label>
                <textarea
                  id="destinatari"
                  className="form-control"
                  value={formData.destinatari}
                  onChange={(e) => handleChange('destinatari', e.target.value)}
                  rows={3}
                  placeholder="email1@esempio.it, email2@esempio.it"
                />
              </div>

              {/* Contatti Email */}
              <div className="form-group full-width" style={{ position: 'relative' }}>
                <label>Contatti Email</label>
                <input
                  type="text"
                  className="form-control"
                  value={searchContatti}
                  onChange={(e) => {
                    console.log('🔤 Input contatti onChange:', e.target.value);
                    console.log('📏 Lunghezza:', e.target.value.length);
                    setSearchContatti(e.target.value);
                  }}
                  placeholder="Cerca per email, nominativo o cliente..."
                />
                {contattiData && contattiData.length > 0 && (
                  <div className="autocomplete-dropdown">
                    {contattiData.map((contatto) => (
                      <div
                        key={contatto.id}
                        className="autocomplete-item"
                        onClick={() => handleAddContatto(contatto.id)}
                      >
                        {contatto.display_name || `${contatto.nominativo} (${contatto.email})`}
                      </div>
                    ))}
                  </div>
                )}
                {selectedContatti.length > 0 && (
                  <div className="selected-items">
                    {selectedContatti.map((id) => {
                      const contatto = contattiData?.find((c) => c.id === id);
                      return (
                        <span key={id} className="badge badge-primary">
                          {contatto?.display_name || contatto?.nominativo || `ID: ${id}`}
                          <button
                            type="button"
                            className="badge-close"
                            onClick={() => handleRemoveContatto(id)}
                          >
                            ×
                          </button>
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Mailing Lists */}
              <div className="form-group full-width" style={{ position: 'relative' }}>
                <label>Liste di Distribuzione</label>
                <input
                  type="text"
                  className="form-control"
                  value={searchListe}
                  onChange={(e) => setSearchListe(e.target.value)}
                  placeholder="Cerca liste..."
                />
                {listeData && listeData.length > 0 && (
                  <div className="autocomplete-dropdown">
                    {listeData.map((lista) => (
                      <div
                        key={lista.id}
                        className="autocomplete-item"
                        onClick={() => handleAddLista(lista.id)}
                      >
                        {lista.nome} ({lista.contatti_count} contatti)
                      </div>
                    ))}
                  </div>
                )}
                {selectedListe.length > 0 && (
                  <div className="selected-items">
                    {selectedListe.map((id) => {
                      const lista = listeData?.find((l) => l.id === id);
                      return (
                        <span key={id} className="badge badge-info">
                          {lista?.nome || `ID: ${id}`}
                          <button
                            type="button"
                            className="badge-close"
                            onClick={() => handleRemoveLista(id)}
                          >
                            ×
                          </button>
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Azioni */}
        <div className="form-actions mt-3">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate(isEdit ? `/comunicazioni/${id}` : '/comunicazioni')}
            disabled={isSubmitting}
          >
            Annulla
          </button>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Salvataggio...' : isEdit ? 'Aggiorna' : 'Crea'}
          </button>
        </div>
      </form>

      {/* Allegati - fuori dal form principale per evitare form nested */}
      {isEdit && id ? (
        <div className="form-section mt-4">
          <AllegatiManager comunicazioneId={Number(id)} />
        </div>
      ) : (
        <div className="card mt-3">
          <div className="card-header">
            <h3>Allegati</h3>
          </div>
          <div className="card-body">
            <div className="alert alert-info">
              <i className="fas fa-info-circle"></i> Gli allegati potranno essere aggiunti dopo aver salvato la comunicazione.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComunicazioneFormPage;
