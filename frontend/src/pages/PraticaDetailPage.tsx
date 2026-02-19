/**
 * Pratica Detail Page
 */
import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, Tab, Box, Badge } from '@mui/material';
import { praticheApi } from '@/api/pratiche';
import { documentiApi } from '@/api/documenti';
import { fascicoliApi } from '@/api/fascicoli';
import type { Pratica, PraticaNotaFormData, PraticaNota } from '@/types/pratica';
import type { Documento } from '@/types/documento';
import { FascicoloAutocomplete } from '@/components/FascicoloAutocomplete';
import { TabPanel, a11yProps } from '@/components/common/TabPanel';
import {
  ArrowBackIcon,
  EditIcon,
  DeleteIcon,
  AddIcon,
  VisibilityIcon,
  DownloadIcon,
} from '@/components/icons/Icons';

type NotaFormState = Omit<PraticaNotaFormData, 'pratica'> & {
  tipo: PraticaNota['tipo'];
  stato: PraticaNota['stato'];
};

export default function PraticaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [pratica, setPratica] = useState<Pratica | null>(null);
  const [documenti, setDocumenti] = useState<Documento[]>([]);
  const [documentiFiltered, setDocumentiFiltered] = useState<Documento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNotaForm, setShowNotaForm] = useState(false);
  const [editingNotaId, setEditingNotaId] = useState<number | null>(null);
  const [showCollegaFascicoloModal, setShowCollegaFascicoloModal] = useState(false);
  const [selectedFascicoloId, setSelectedFascicoloId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [notaForm, setNotaForm] = useState<NotaFormState>({
    tipo: 'memo',
    testo: '',
    data: new Date().toISOString().split('T')[0],
    stato: 'aperta',
  });

  // Stati per i filtri documenti
  const [filterDocSearch, setFilterDocSearch] = useState('');
  const [filterDocTipo, setFilterDocTipo] = useState('');
  const [filterDocCliente, setFilterDocCliente] = useState('');
  const [filterDocDataDa, setFilterDocDataDa] = useState('');
  const [filterDocDataA, setFilterDocDataA] = useState('');
  const [tipiDocumento, setTipiDocumento] = useState<Array<{ id: number; codice: string; nome: string }>>([]);
  const [clientiDocumento, setClientiDocumento] = useState<Array<{ id: number; display: string }>>([]);

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

  const loadDocumenti = useCallback(async (fascicoli?: Pratica['fascicoli']) => {
    if (!fascicoli || fascicoli.length === 0) {
      setDocumenti([]);
      return;
    }

    try {
      const responses = await Promise.all(
        fascicoli.map((fascicolo) => documentiApi.list({ fascicolo: fascicolo.id }))
      );
      const allDocumenti = responses.flatMap((response) => response.results);
      setDocumenti(allDocumenti);
    } catch (err) {
      console.error('Error loading documenti:', err);
      alert(getErrorMessage(err, 'Errore nel caricamento dei documenti'));
    }
  }, [getErrorMessage]);

  const loadPratica = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);
      const data = await praticheApi.get(Number(id));
      setPratica(data);
      await loadDocumenti(data.fascicoli);
    } catch (err) {
      setError(getErrorMessage(err, 'Errore nel caricamento della pratica'));
    } finally {
      setLoading(false);
    }
  }, [getErrorMessage, id, loadDocumenti]);

  useEffect(() => {
    loadPratica();
  }, [loadPratica]);

  // Carica tipi di documento
  useEffect(() => {
    const loadTipiDocumento = async () => {
      try {
        const tipi = await documentiApi.listTipi();
        setTipiDocumento(tipi);
      } catch (err) {
        console.error('Error loading tipi documento:', err);
      }
    };
    loadTipiDocumento();
  }, []);

  // Estrai clienti unici dai documenti
  useEffect(() => {
    if (documenti.length > 0) {
      const clientiMap = new Map<number, string>();
      documenti.forEach(doc => {
        if (doc.cliente && doc.cliente_detail) {
          clientiMap.set(doc.cliente, doc.cliente_detail.anagrafica_display || `Cliente ${doc.cliente}`);
        }
      });
      const clientiUnique = Array.from(clientiMap.entries()).map(([id, display]) => ({ id, display }));
      setClientiDocumento(clientiUnique.sort((a, b) => a.display.localeCompare(b.display)));
    }
  }, [documenti]);

  // Applica filtri ai documenti
  useEffect(() => {
    let filtered = [...documenti];

    // Filtro fulltext
    if (filterDocSearch) {
      const searchLower = filterDocSearch.toLowerCase();
      filtered = filtered.filter(doc => 
        doc.codice?.toLowerCase().includes(searchLower) ||
        doc.descrizione?.toLowerCase().includes(searchLower) ||
        doc.fascicolo_detail?.codice?.toLowerCase().includes(searchLower) ||
        doc.fascicolo_detail?.titolo?.toLowerCase().includes(searchLower)
      );
    }

    // Filtro per tipo
    if (filterDocTipo) {
      filtered = filtered.filter(doc => doc.tipo === Number(filterDocTipo));
    }

    // Filtro per cliente
    if (filterDocCliente) {
      filtered = filtered.filter(doc => doc.cliente === Number(filterDocCliente));
    }

    // Filtro per data da
    if (filterDocDataDa) {
      const dataDa = new Date(filterDocDataDa);
      filtered = filtered.filter(doc => {
        const dataDoc = new Date(doc.data_documento);
        return dataDoc >= dataDa;
      });
    }

    // Filtro per data a
    if (filterDocDataA) {
      const dataA = new Date(filterDocDataA);
      filtered = filtered.filter(doc => {
        const dataDoc = new Date(doc.data_documento);
        return dataDoc <= dataA;
      });
    }

    setDocumentiFiltered(filtered);
  }, [documenti, filterDocSearch, filterDocTipo, filterDocCliente, filterDocDataDa, filterDocDataA]);

  const handlePreviewFile = (documento: Documento) => {
    if (documento.file) {
      const fileUrl = documento.file_url || documento.file;
      window.open(fileUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const handleDelete = async () => {
    if (!id || !window.confirm('Sei sicuro di voler eliminare questa pratica?')) return;

    try {
      await praticheApi.delete(Number(id));
      navigate(-1);
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante l\'eliminazione'));
    }
  };

  const handleAddNota = () => {
    setNotaForm({
      tipo: 'memo',
      testo: '',
      data: new Date().toISOString().split('T')[0],
      stato: 'aperta',
    });
    setEditingNotaId(null);
    setShowNotaForm(true);
  };

  const handleEditNota = (notaId: number) => {
    const nota = pratica?.note_collegate.find(n => n.id === notaId);
    if (nota) {
      setNotaForm({
        tipo: nota.tipo,
        testo: nota.testo,
        data: nota.data,
        stato: nota.stato,
      });
      setEditingNotaId(notaId);
      setShowNotaForm(true);
    }
  };

  const handleSaveNota = async () => {
    if (!id || !notaForm.testo.trim()) {
      alert('Inserisci il testo della nota');
      return;
    }

    try {
      const notaData: PraticaNotaFormData = {
        pratica: Number(id),
        ...notaForm,
      };

      if (editingNotaId) {
        await praticheApi.updateNota(editingNotaId, notaData);
      } else {
        await praticheApi.createNota(notaData);
      }

      await loadPratica();
      setShowNotaForm(false);
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante il salvataggio della nota'));
    }
  };

  const handleDeleteNota = async (notaId: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questa nota?')) return;

    try {
      await praticheApi.deleteNota(notaId);
      await loadPratica();
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante l\'eliminazione della nota'));
    }
  };

  const handleCollegaFascicolo = async () => {
    if (!id || !selectedFascicoloId) return;

    try {
      const fascicolo = await fascicoliApi.get(selectedFascicoloId);
      const currentPratiche = fascicolo.pratiche_details?.map(p => p.id) || [];
      const updatedPratiche = [...currentPratiche, Number(id)];
      
      await fascicoliApi.update(selectedFascicoloId, {
        pratiche: updatedPratiche
      });

      await loadPratica();
      setShowCollegaFascicoloModal(false);
      setSelectedFascicoloId(null);
      alert('Fascicolo collegato con successo!');
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante il collegamento del fascicolo'));
    }
  };

  const handleScollegaFascicolo = async (fascicoloId: number) => {
    if (!id || !window.confirm('Sei sicuro di voler scollegare questo fascicolo dalla pratica?')) return;

    try {
      const fascicolo = await fascicoliApi.get(fascicoloId);
      const currentPratiche = fascicolo.pratiche_details?.map(p => p.id) || [];
      const updatedPratiche = currentPratiche.filter(praticaId => praticaId !== Number(id));
      
      await fascicoliApi.update(fascicoloId, {
        pratiche: updatedPratiche
      });

      await loadPratica();
      alert('Fascicolo scollegato con successo!');
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante lo scollegamento del fascicolo'));
    }
  };

  const getStatoBadge = (stato: string) => {
    const badges: Record<string, string> = {
      aperta: 'badge-info',
      lavorazione: 'badge-warning',
      attesa: 'badge-secondary',
      chiusa: 'badge-success',
    };
    return badges[stato] || 'badge-secondary';
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
  };

  if (loading) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento...</p>
        </div>
      </div>
    );
  }

  if (error || !pratica) {
    return (
      <div className="page-container">
        <div className="alert alert-error">
          {error || 'Pratica non trovata'}
        </div>
        <button onClick={() => navigate(-1)} className="btn-secondary">
          Torna indietro
        </button>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <button
              onClick={() => navigate(-1)}
              className="btn-secondary"
              title="Torna alla pagina precedente"
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <ArrowBackIcon size={20} />
              Indietro
            </button>
            <h1 className="page-title">{pratica.codice}</h1>
            <span className={`badge ${getStatoBadge(pratica.stato)}`}>
              {pratica.stato_display}
            </span>
          </div>
          <p className="page-subtitle">{pratica.oggetto}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => navigate(`/pratiche/${id}/modifica`)}
            className="btn-secondary"
          >
            <EditIcon size={20} />
            Modifica
          </button>
          <button onClick={handleDelete} className="btn-danger">
            <DeleteIcon size={20} />
            Elimina
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', marginBottom: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="tabs pratiche"
        >
          <Tab label="Generale" {...a11yProps(0)} />
          <Tab 
            label={
              <Badge badgeContent={pratica.fascicoli?.length || 0} color="primary">
                <span style={{ marginRight: pratica.fascicoli?.length ? '20px' : '0' }}>Fascicoli</span>
              </Badge>
            } 
            {...a11yProps(1)} 
          />
          <Tab 
            label={
              <Badge badgeContent={documenti.length} color="primary">
                <span style={{ marginRight: documenti.length ? '20px' : '0' }}>Documenti</span>
              </Badge>
            } 
            {...a11yProps(2)} 
          />
          <Tab 
            label={
              <Badge badgeContent={pratica.note_collegate?.length || 0} color="primary">
                <span style={{ marginRight: pratica.note_collegate?.length ? '20px' : '0' }}>Note</span>
              </Badge>
            } 
            {...a11yProps(3)} 
          />
          <Tab 
            label={
              <Badge badgeContent={pratica.scadenze?.length || 0} color="primary">
                <span style={{ marginRight: pratica.scadenze?.length ? '20px' : '0' }}>Scadenze</span>
              </Badge>
            } 
            {...a11yProps(4)} 
          />
        </Tabs>
      </Box>

      {/* Tab 0: Generale */}
      <TabPanel value={activeTab} index={0}>
        {/* Layout a 2 colonne per le informazioni */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem', marginBottom: '1.5rem' }}>
          
          {/* Informazioni principali */}
          <div className="card">
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
              Informazioni Principali
            </h2>
            <div className="detail-row">
              <span className="detail-label">Tipo Pratica:</span>
              <span className="detail-value">{pratica.tipo_detail?.nome || '-'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Cliente:</span>
              {pratica.cliente ? (
                <span className="detail-value">
                  <a
                    href={`/anagrafiche/${pratica.cliente}`}
                    onClick={(e) => {
                      e.preventDefault();
                      navigate(`/anagrafiche/${pratica.cliente}`);
                    }}
                    style={{ color: '#2563eb', textDecoration: 'none' }}
                  >
                    {pratica.cliente_detail?.anagrafica_display || `Cliente ${pratica.cliente}`}
                  </a>
                </span>
              ) : (
                <span className="detail-value">-</span>
              )}
            </div>
            <div className="detail-row">
              <span className="detail-label">Responsabile:</span>
              <span className="detail-value">
                {pratica.responsabile_nome || '-'}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Stato:</span>
              <span className="detail-value">
                <span className={`badge ${getStatoBadge(pratica.stato)}`}>
                  {pratica.stato_display}
                </span>
              </span>
            </div>
          </div>

          {/* Date */}
          <div className="card">
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
              Date
            </h2>
            <div className="detail-row">
              <span className="detail-label">Data Apertura:</span>
              <span className="detail-value">{formatDate(pratica.data_apertura)}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Data Riferimento:</span>
              <span className="detail-value">{formatDate(pratica.data_riferimento)}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Periodo Riferimento:</span>
              <span className="detail-value">{pratica.periodo_riferimento_display}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Data Chiusura:</span>
              <span className="detail-value">{formatDate(pratica.data_chiusura)}</span>
            </div>
          </div>
        </div>

        {/* Note generali */}
        {pratica.note && (
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
              Note Generali
            </h2>
            <p style={{ whiteSpace: 'pre-wrap', color: '#4b5563', lineHeight: 1.6 }}>
              {pratica.note}
            </p>
          </div>
        )}

        {/* Tags */}
        {pratica.tag && (
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
              Tags
            </h2>
            <p className="detail-value">{pratica.tag}</p>
          </div>
        )}

        {/* Informazioni sistema */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Informazioni Sistema
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            <div className="detail-row">
              <span className="detail-label">Progressivo:</span>
              <span className="detail-value">{pratica.progressivo}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Periodo Key:</span>
              <span className="detail-value">{pratica.periodo_key}</span>
            </div>
          </div>
        </div>
      </TabPanel>

      {/* Tab 1: Fascicoli */}
      <TabPanel value={activeTab} index={1}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, margin: 0 }}>
              Fascicoli ({pratica.fascicoli?.length || 0})
            </h2>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                onClick={() => setShowCollegaFascicoloModal(true)} 
                className="btn-secondary"
              >
                <AddIcon size={18} />
                Collega Fascicolo
              </button>
              <button 
                onClick={() => navigate(`/fascicoli/nuovo?pratica_id=${pratica.id}`)} 
                className="btn-primary"
              >
                <AddIcon size={18} />
                Crea Fascicolo
              </button>
            </div>
          </div>

          {pratica.fascicoli && pratica.fascicoli.length > 0 ? (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Codice</th>
                    <th>Titolo</th>
                    <th>Stato</th>
                    <th style={{ width: '180px', textAlign: 'center' }}>Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {pratica.fascicoli.map((fascicolo) => (
                    <tr key={fascicolo.id}>
                      <td>
                        <a
                          href={`/fascicoli/${fascicolo.id}`}
                          onClick={(e) => {
                            e.preventDefault();
                            navigate(`/fascicoli/${fascicolo.id}`);
                          }}
                          style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 500 }}
                        >
                          {fascicolo.codice}
                        </a>
                      </td>
                      <td>{fascicolo.titolo}</td>
                      <td>
                        <span className={`badge ${
                          fascicolo.stato === 'corrente' ? 'badge-success' :
                          fascicolo.stato === 'storico' ? 'badge-info' :
                          fascicolo.stato === 'chiuso' ? 'badge-secondary' :
                          'badge-warning'
                        }`}>
                          {fascicolo.stato_display}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <button
                            onClick={() => navigate(`/fascicoli/${fascicolo.id}`)}
                            className="btn-icon"
                            title="Visualizza"
                          >
                            <VisibilityIcon size={18} />
                          </button>
                          <button
                            onClick={() => handleScollegaFascicolo(fascicolo.id)}
                            className="btn-icon btn-icon-danger"
                            title="Scollega fascicolo dalla pratica"
                          >
                            <DeleteIcon size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>
              Nessun fascicolo associato. Clicca su "Crea Fascicolo" per crearne uno.
            </p>
          )}
        </div>
      </TabPanel>

      {/* Tab 2: Documenti */}
      <TabPanel value={activeTab} index={2}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, margin: 0 }}>
              Documenti ({documentiFiltered.length})
            </h2>
          </div>

          {/* Filtri Documenti */}
          <div style={{ 
            display: 'flex', 
            gap: '0.75rem', 
            marginBottom: '1rem', 
            flexWrap: 'wrap',
            padding: '1rem',
            backgroundColor: '#f9fafb',
            borderRadius: '0.375rem'
          }}>
            <input
              type="text"
              placeholder="Cerca per codice, descrizione o fascicolo"
              value={filterDocSearch}
              onChange={(e) => setFilterDocSearch(e.target.value)}
              style={{
                flex: '1 1 300px',
                minWidth: '200px',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '0.875rem'
              }}
            />
            
            <select
              value={filterDocTipo}
              onChange={(e) => setFilterDocTipo(e.target.value)}
              style={{
                minWidth: '150px',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                backgroundColor: 'white'
              }}
            >
              <option value="">-- Tutti i tipi --</option>
              {tipiDocumento.map(tipo => (
                <option key={tipo.id} value={tipo.id}>
                  {tipo.codice} - {tipo.nome}
                </option>
              ))}
            </select>

            <select
              value={filterDocCliente}
              onChange={(e) => setFilterDocCliente(e.target.value)}
              style={{
                minWidth: '150px',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                backgroundColor: 'white'
              }}
            >
              <option value="">-- Tutti i clienti --</option>
              {clientiDocumento.map(cliente => (
                <option key={cliente.id} value={cliente.id}>
                  {cliente.display}
                </option>
              ))}
            </select>

            <input
              type="date"
              value={filterDocDataDa}
              onChange={(e) => setFilterDocDataDa(e.target.value)}
              placeholder="Data da"
              title="Data documento da"
              style={{
                minWidth: '140px',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                backgroundColor: 'white'
              }}
            />

            <input
              type="date"
              value={filterDocDataA}
              onChange={(e) => setFilterDocDataA(e.target.value)}
              placeholder="Data a"
              title="Data documento a"
              style={{
                minWidth: '140px',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                backgroundColor: 'white'
              }}
            />

            {(filterDocSearch || filterDocTipo || filterDocCliente || filterDocDataDa || filterDocDataA) && (
              <button
                onClick={() => {
                  setFilterDocSearch('');
                  setFilterDocTipo('');
                  setFilterDocCliente('');
                  setFilterDocDataDa('');
                  setFilterDocDataA('');
                }}
                className="btn-secondary"
                style={{
                  padding: '0.5rem 1rem',
                  fontSize: '0.875rem'
                }}
              >
                Reset
              </button>
            )}
          </div>

          {documentiFiltered.length > 0 ? (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Codice</th>
                    <th>Descrizione</th>
                    <th>Tipo</th>
                    <th>Fascicolo</th>
                    <th>Data</th>
                    <th>Stato</th>
                    <th style={{ width: '120px', textAlign: 'center' }}>Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {documentiFiltered.map((doc) => (
                    <tr key={doc.id}>
                      <td>
                        <a
                          href={`/documenti/${doc.id}`}
                          onClick={(e) => {
                            e.preventDefault();
                            navigate(`/documenti/${doc.id}`);
                          }}
                          style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 500 }}
                        >
                          {doc.codice}
                        </a>
                      </td>
                      <td>{doc.descrizione}</td>
                      <td>{doc.tipo_detail?.nome || doc.tipo}</td>
                      <td>
                        {doc.fascicolo_detail ? (
                          <a
                            href={`/fascicoli/${doc.fascicolo_detail.id}`}
                            onClick={(e) => {
                              e.preventDefault();
                              if (doc.fascicolo_detail) {
                                navigate(`/fascicoli/${doc.fascicolo_detail.id}`);
                              }
                            }}
                            style={{ color: '#2563eb', textDecoration: 'none' }}
                          >
                            {doc.fascicolo_detail.codice}
                          </a>
                        ) : (
                          <span style={{ color: '#6b7280' }}>-</span>
                        )}
                      </td>
                      <td>
                        {new Date(doc.data_documento).toLocaleDateString('it-IT')}
                      </td>
                      <td>
                        <span className={`badge ${
                          doc.stato === 'definitivo' ? 'badge-success' :
                          doc.stato === 'bozza' ? 'badge-warning' :
                          doc.stato === 'archiviato' ? 'badge-info' :
                          'badge-secondary'
                        }`}>
                          {doc.stato}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <button
                            onClick={() => navigate(`/documenti/${doc.id}`)}
                            className="btn-icon"
                            title="Visualizza dettaglio"
                          >
                            <VisibilityIcon size={18} />
                          </button>
                          {doc.file && (
                            <button
                              onClick={() => handlePreviewFile(doc)}
                              className="btn-icon"
                              title="Apri file"
                              style={{ color: '#059669' }}
                            >
                              <DownloadIcon size={18} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>
              {documenti.length === 0 
                ? 'Nessun documento associato ai fascicoli di questa pratica.'
                : 'Nessun documento corrisponde ai filtri selezionati.'}
            </p>
          )}
        </div>
      </TabPanel>

      {/* Tab 3: Note */}
      <TabPanel value={activeTab} index={3}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, margin: 0 }}>
              Note ({pratica.note_collegate?.length || 0})
            </h2>
            <button onClick={handleAddNota} className="btn-primary">
              <AddIcon size={18} />
              Aggiungi Nota
            </button>
          </div>

          {/* Form Nota */}
          {showNotaForm && (
            <div style={{ padding: '1rem', backgroundColor: '#f0f9ff', border: '1px solid #bfdbfe', borderRadius: '0.375rem', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>
                {editingNotaId ? 'Modifica Nota' : 'Nuova Nota'}
              </h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group">
                  <label>Tipo</label>
                  <select
                    value={notaForm.tipo}
                    onChange={(e) =>
                      setNotaForm((prev) => ({
                        ...prev,
                        tipo: e.target.value as NotaFormState['tipo'],
                      }))
                    }
                    className="form-control"
                  >
                    <option value="memo">Memo</option>
                    <option value="comunicazione">Comunicazione</option>
                    <option value="chiusura">Chiusura</option>
                    <option value="altro">Altro</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Data</label>
                  <input
                    type="date"
                    value={notaForm.data}
                    onChange={(e) => setNotaForm({ ...notaForm, data: e.target.value })}
                    className="form-control"
                  />
                </div>

                <div className="form-group">
                  <label>Stato</label>
                  <select
                    value={notaForm.stato}
                    onChange={(e) =>
                      setNotaForm((prev) => ({
                        ...prev,
                        stato: e.target.value as NotaFormState['stato'],
                      }))
                    }
                    className="form-control"
                  >
                    <option value="aperta">Aperta</option>
                    <option value="chiusa">Chiusa</option>
                  </select>
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label>Testo</label>
                <textarea
                  value={notaForm.testo}
                  onChange={(e) => setNotaForm({ ...notaForm, testo: e.target.value })}
                  className="form-control"
                  rows={4}
                  placeholder="Inserisci il testo della nota..."
                />
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                <button onClick={() => setShowNotaForm(false)} className="btn-secondary">
                  Annulla
                </button>
                <button onClick={handleSaveNota} className="btn-primary">
                  {editingNotaId ? 'Aggiorna' : 'Salva'}
                </button>
              </div>
            </div>
          )}

          {/* Lista Note */}
          {pratica.note_collegate && pratica.note_collegate.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {pratica.note_collegate.map((nota) => (
                <div
                  key={nota.id}
                  style={{
                    padding: '1rem',
                    backgroundColor: '#f9fafb',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.375rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span className={`badge ${nota.tipo === 'memo' ? 'badge-info' : nota.tipo === 'comunicazione' ? 'badge-warning' : nota.tipo === 'chiusura' ? 'badge-success' : 'badge-secondary'}`}>
                        {nota.tipo_display}
                      </span>
                      <span className={`badge ${nota.stato === 'aperta' ? 'badge-warning' : 'badge-secondary'}`}>
                        {nota.stato_display}
                      </span>
                      <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                        {formatDate(nota.data)}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => handleEditNota(nota.id)}
                        className="btn-icon"
                        title="Modifica nota"
                      >
                        <EditIcon size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteNota(nota.id)}
                        className="btn-icon btn-icon-danger"
                        title="Elimina nota"
                      >
                        <DeleteIcon size={18} />
                      </button>
                    </div>
                  </div>
                  <p style={{ whiteSpace: 'pre-wrap', color: '#4b5563', lineHeight: 1.6, margin: 0 }}>
                    {nota.testo}
                  </p>
                </div>
              ))}
            </div>
          ) : !showNotaForm && (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>
              Nessuna nota presente. Clicca su "Aggiungi Nota" per crearne una.
            </p>
          )}
        </div>
      </TabPanel>

      {/* Tab 4: Scadenze */}
      <TabPanel value={activeTab} index={4}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, margin: 0 }}>
              Scadenze Collegate ({pratica.scadenze?.length || 0})
            </h2>
            <button 
              onClick={() => navigate(`/scadenze/nuovo?pratica_id=${pratica.id}&return=/pratiche/${pratica.id}`)} 
              className="btn-primary"
            >
              <AddIcon size={18} />
              Crea Scadenza
            </button>
          </div>

          {pratica.scadenze && pratica.scadenze.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {pratica.scadenze.map((scadenza) => (
                <div
                  key={scadenza.id}
                  onClick={() => navigate(`/scadenze/${scadenza.id}`)}
                  style={{
                    padding: '1rem',
                    backgroundColor: '#f9fafb',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f3f4f6';
                    e.currentTarget.style.borderColor = '#d1d5db';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#f9fafb';
                    e.currentTarget.style.borderColor = '#e5e7eb';
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#111827', marginBottom: '0.5rem' }}>
                        {scadenza.titolo}
                      </h3>
                      {scadenza.descrizione && (
                        <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                          {scadenza.descrizione.length > 150 
                            ? `${scadenza.descrizione.substring(0, 150)}...` 
                            : scadenza.descrizione}
                        </p>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span
                      className={`badge ${
                        scadenza.stato === 'attiva' ? 'badge-success' :
                        scadenza.stato === 'completata' ? 'badge-info' :
                        scadenza.stato === 'in_scadenza' ? 'badge-warning' :
                        scadenza.stato === 'scaduta' ? 'badge-danger' :
                        'badge-secondary'
                      }`}
                    >
                      {scadenza.stato_display}
                    </span>
                    <span
                      className={`badge ${
                        scadenza.priorita === 'critical' ? 'badge-danger' :
                        scadenza.priorita === 'high' ? 'badge-warning' :
                        scadenza.priorita === 'medium' ? 'badge-info' :
                        'badge-secondary'
                      }`}
                    >
                      {scadenza.priorita_display}
                    </span>
                    {scadenza.categoria && (
                      <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                        {scadenza.categoria}
                      </span>
                    )}
                    {scadenza.data_scadenza && (
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', marginLeft: 'auto' }}>
                        📅 {new Date(scadenza.data_scadenza).toLocaleDateString('it-IT')}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>
              Nessuna scadenza collegata. Clicca su "Crea Scadenza" per crearne una.
            </p>
          )}
        </div>
      </TabPanel>

      {/* Modal Collega Fascicolo */}
      {showCollegaFascicoloModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => {
            setShowCollegaFascicoloModal(false);
            setSelectedFascicoloId(null);
          }}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '0.5rem',
              padding: '1.5rem',
              maxWidth: '500px',
              width: '90%',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
              Collega Fascicolo alla Pratica
            </h2>

            <div style={{ marginBottom: '1rem' }}>
              <label className="form-label">
                Seleziona Fascicolo *
              </label>
              <FascicoloAutocomplete
                value={selectedFascicoloId}
                onChange={setSelectedFascicoloId}
                required
                excludeIds={pratica.fascicoli?.map(f => f.id) || []}
              />
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.5rem' }}>
                Seleziona un fascicolo esistente da collegare a questa pratica. 
                I fascicoli già collegati sono esclusi dalla lista.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button
                type="button"
                onClick={() => {
                  setShowCollegaFascicoloModal(false);
                  setSelectedFascicoloId(null);
                }}
                className="btn-secondary"
              >
                Annulla
              </button>
              <button
                type="button"
                onClick={handleCollegaFascicolo}
                className="btn-primary"
                disabled={!selectedFascicoloId}
              >
                Collega Fascicolo
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
