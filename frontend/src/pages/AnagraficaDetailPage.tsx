import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Tabs, Tab, Box, Badge } from '@mui/material';
import { apiClient } from '../api/client';
import { praticheApi } from '../api/pratiche';
import { fascicoliApi } from '../api/fascicoli';
import { documentiApi } from '../api/documenti';
import { TabPanel, a11yProps } from '../components/common/TabPanel';
import type { AnagraficaDetail } from '../types/anagrafiche';
import type { PraticaListItem, PraticheTipo, PraticaFilters } from '../types/pratica';
import type { FascicoloListItem, FascicoloFilters } from '../types/fascicolo';
import type { Documento, DocumentoFilters, DocumentiTipo } from '../types/documento';
import {
  EditIcon,
  DeleteIcon,
  ArrowBackIcon,
  PrintIcon,
  ClientIcon,
  PersonIcon,
  BusinessIcon,
  EmailIcon,
  PhoneIcon,
  LocationIcon,
  InfoIcon,
  CheckIcon,
  RefreshIcon,
  AddIcon,
  VisibilityIcon
} from '../components/icons/Icons';
import { IndirizziManager } from '../components/IndirizziManager';
import { ContattiEmailManager } from '../components/ContattiEmailManager';

// Debounce di un valore (usato per i campi di ricerca testuale nei filtri delle tab)
function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timeout = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timeout);
  }, [value, delayMs]);
  return debounced;
}

const PAGE_SIZE = 20;

export function AnagraficaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [anagrafica, setAnagrafica] = useState<AnagraficaDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  const loadAnagrafica = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      const response = await apiClient.get<AnagraficaDetail>(`/anagrafiche/${id}/`);
      setAnagrafica(response.data);
      setError(null);
    } catch (error: unknown) {
      const message = extractAxiosMessage(error);
      setError(message ?? 'Errore nel caricamento dell\'anagrafica');
      console.error('Error loading anagrafica:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  // Ricarica i dati quando l'id cambia
  useEffect(() => {
    if (!id) {
      return;
    }
    void loadAnagrafica();
  }, [id, loadAnagrafica]);

  const clienteId = anagrafica?.cliente?.id;

  // ========== Tab Pratiche ==========
  const [pratiche, setPratiche] = useState<PraticaListItem[]>([]);
  const [praticheTotal, setPraticheTotal] = useState(0);
  const [praticheLoading, setPraticheLoading] = useState(false);
  const [tipiPratica, setTipiPratica] = useState<PraticheTipo[]>([]);
  const [praticheSearch, setPraticheSearch] = useState('');
  const praticheSearchDebounced = useDebouncedValue(praticheSearch, 300);
  const [praticheTipo, setPraticheTipo] = useState('');
  const [praticheStato, setPraticheStato] = useState('');
  const [praticheDataDa, setPraticheDataDa] = useState('');
  const [praticheDataA, setPraticheDataA] = useState('');
  const [praticheAllPage, setPraticheAllPage] = useState(1);

  const praticheFilters: PraticaFilters = {
    cliente: clienteId,
    page: praticheAllPage,
    page_size: PAGE_SIZE,
    ordering: '-data_apertura',
    search: praticheSearchDebounced || undefined,
    tipo: praticheTipo ? Number(praticheTipo) : undefined,
    stato: praticheStato || undefined,
    data_apertura_da: praticheDataDa || undefined,
    data_apertura_a: praticheDataA || undefined,
  };
  const praticheFiltersKey = JSON.stringify(praticheFilters);

  useEffect(() => {
    if (!clienteId) return;
    let cancelled = false;
    setPraticheLoading(true);
    praticheApi.list(praticheFilters)
      .then((res) => {
        if (cancelled) return;
        setPratiche(res.results);
        setPraticheTotal(res.count);
      })
      .catch((err) => console.error('Errore nel caricamento delle pratiche del cliente:', err))
      .finally(() => { if (!cancelled) setPraticheLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteId, praticheFiltersKey]);

  useEffect(() => {
    praticheApi.listTipi().then(setTipiPratica).catch((err) => console.error('Errore nel caricamento dei tipi pratica:', err));
  }, []);

  const resetPraticheFiltri = () => {
    setPraticheSearch('');
    setPraticheTipo('');
    setPraticheStato('');
    setPraticheDataDa('');
    setPraticheDataA('');
    setPraticheAllPage(1);
  };

  // ========== Tab Fascicoli ==========
  const [fascicoli, setFascicoli] = useState<FascicoloListItem[]>([]);
  const [fascicoliTotal, setFascicoliTotal] = useState(0);
  const [fascicoliLoading, setFascicoliLoading] = useState(false);
  const [fascicoliSearch, setFascicoliSearch] = useState('');
  const fascicoliSearchDebounced = useDebouncedValue(fascicoliSearch, 300);
  const [fascicoliAnno, setFascicoliAnno] = useState('');
  const [fascicoliStato, setFascicoliStato] = useState('');
  const [fascicoliPage, setFascicoliPage] = useState(1);

  const fascicoliFilters: FascicoloFilters = {
    cliente: clienteId,
    page: fascicoliPage,
    page_size: PAGE_SIZE,
    ordering: '-anno,codice',
    search: fascicoliSearchDebounced || undefined,
    anno: fascicoliAnno ? Number(fascicoliAnno) : undefined,
    stato: fascicoliStato || undefined,
  };
  const fascicoliFiltersKey = JSON.stringify(fascicoliFilters);

  useEffect(() => {
    if (!clienteId) return;
    let cancelled = false;
    setFascicoliLoading(true);
    fascicoliApi.list(fascicoliFilters)
      .then((res) => {
        if (cancelled) return;
        setFascicoli(res.results);
        setFascicoliTotal(res.count);
      })
      .catch((err) => console.error('Errore nel caricamento dei fascicoli del cliente:', err))
      .finally(() => { if (!cancelled) setFascicoliLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteId, fascicoliFiltersKey]);

  const resetFascicoliFiltri = () => {
    setFascicoliSearch('');
    setFascicoliAnno('');
    setFascicoliStato('');
    setFascicoliPage(1);
  };

  const currentYear = new Date().getFullYear();
  const anniFascicoli = Array.from({ length: 10 }, (_, i) => currentYear - i);
  const statiFascicolo = [
    { value: 'corrente', label: 'Archivio corrente' },
    { value: 'deposito', label: 'Archivio deposito' },
    { value: 'storico', label: 'Archivio storico' },
    { value: 'scartato', label: 'Scartato' },
  ];

  // ========== Tab Documenti ==========
  const [documenti, setDocumenti] = useState<Documento[]>([]);
  const [documentiTotal, setDocumentiTotal] = useState(0);
  const [documentiLoading, setDocumentiLoading] = useState(false);
  const [tipiDocumento, setTipiDocumento] = useState<DocumentiTipo[]>([]);
  const [documentiSearch, setDocumentiSearch] = useState('');
  const documentiSearchDebounced = useDebouncedValue(documentiSearch, 300);
  const [documentiTipo, setDocumentiTipo] = useState('');
  const [documentiStato, setDocumentiStato] = useState('');
  const [documentiDataDa, setDocumentiDataDa] = useState('');
  const [documentiDataA, setDocumentiDataA] = useState('');
  const [documentiPage, setDocumentiPage] = useState(1);

  const documentiFilters: DocumentoFilters = {
    cliente: clienteId,
    search: documentiSearchDebounced || undefined,
    tipo: documentiTipo ? Number(documentiTipo) : undefined,
    stato: documentiStato || undefined,
    data_da: documentiDataDa || undefined,
    data_a: documentiDataA || undefined,
    ordering: '-data_documento',
  };
  const documentiFiltersKey = JSON.stringify(documentiFilters);

  useEffect(() => {
    if (!clienteId) return;
    let cancelled = false;
    setDocumentiLoading(true);
    documentiApi.list(documentiFilters, documentiPage, PAGE_SIZE)
      .then((res) => {
        if (cancelled) return;
        setDocumenti(res.results);
        setDocumentiTotal(res.count);
      })
      .catch((err) => console.error('Errore nel caricamento dei documenti del cliente:', err))
      .finally(() => { if (!cancelled) setDocumentiLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteId, documentiFiltersKey, documentiPage]);

  useEffect(() => {
    documentiApi.listTipi().then((data) => setTipiDocumento(Array.isArray(data) ? data : [])).catch((err) => console.error('Errore nel caricamento dei tipi documento:', err));
  }, []);

  const resetDocumentiFiltri = () => {
    setDocumentiSearch('');
    setDocumentiTipo('');
    setDocumentiStato('');
    setDocumentiDataDa('');
    setDocumentiDataA('');
    setDocumentiPage(1);
  };

  const handleDelete = async () => {
    if (!id) return;

    if (!confirm('Sei sicuro di voler eliminare questa anagrafica?')) {
      return;
    }

    try {
      setDeleting(true);
      await apiClient.delete(`/anagrafiche/${id}/`);
      navigate(-1); // Torna alla pagina precedente
    } catch (error: unknown) {
      alert(extractAxiosMessage(error) ?? 'Errore nell\'eliminazione dell\'anagrafica');
      setDeleting(false);
    }
  };

  const handleMakeCliente = async () => {
    if (!id) return;

    try {
      await apiClient.post(`/anagrafiche/${id}/make_cliente/`);
      loadAnagrafica(); // Reload to show updated data
    } catch (error: unknown) {
      alert(extractAxiosMessage(error) ?? 'Errore nella conversione a cliente');
    }
  };

  const handleRicalcolaCodice = async () => {
    if (!id) return;

    if (!confirm('Ricalcolare il codice anagrafica? Il codice attuale verrà sostituito se non coerente.')) {
      return;
    }

    try {
      const response = await apiClient.post(`/anagrafiche/${id}/ricalcola_codice/`);
      const data = response.data;

      // Verifica se il codice è cambiato
      if (data.unchanged) {
        alert(
          `✓ Codice già corretto!\n\n` +
          `${data.message}\n` +
          `Codice attuale: ${data.new_code}`
        );
      } else {
        // Mostra il risultato con il cambio
        alert(
          `Codice aggiornato con successo!\n\n` +
          `Vecchio codice: ${data.old_code || 'nessuno'}\n` +
          `Nuovo codice: ${data.new_code}`
        );
      }

      loadAnagrafica(); // Ricarica per mostrare il nuovo codice
    } catch (error: unknown) {
      alert(extractAxiosMessage(error) ?? 'Errore nel ricalcolo del codice');
    }
  };

  const handlePrintFascicolo = () => {
    if (!id || !anagrafica?.cliente) return;

    // Apri stampa in nuova finestra
    // URL: /etichette/anagrafiche/cliente/{cliente_id}/?module=FAS_CLI
    // Nota: le stampe sono su endpoint Django tradizionale, non /api/v1/
    const baseUrl = import.meta.env.VITE_API_URL
      ? import.meta.env.VITE_API_URL.replace('/api/v1', '')
      : 'http://localhost:8000';
    const stampaUrl = `${baseUrl}/etichette/anagrafiche/cliente/${anagrafica.cliente.id}/?module=FAS_CLI`;
    window.open(stampaUrl, '_blank');
  };

  if (loading) {
    return (
      <div className="page-container">
        <h1>📇 Dettaglio Anagrafica</h1>
        <p>Caricamento...</p>
      </div>
    );
  }

  if (error || !anagrafica) {
    return (
      <div className="page-container">
        <h1>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <PersonIcon size={32} />
            Dettaglio Anagrafica
          </span>
        </h1>
        <div className="alert alert-error">{error || 'Anagrafica non trovata'}</div>
        <button onClick={() => navigate(-1)} className="btn btn-secondary">
          <ArrowBackIcon size={18} />
          <span>Torna indietro</span>
        </button>
      </div>
    );
  }

  const praticheTotalPages = Math.ceil(praticheTotal / PAGE_SIZE);
  const fascicoliTotalPages = Math.ceil(fascicoliTotal / PAGE_SIZE);
  const documentiTotalPages = Math.ceil(documentiTotal / PAGE_SIZE);

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {anagrafica.tipo === 'PF' ? <PersonIcon size={32} /> : <BusinessIcon size={32} />}
            {anagrafica.display_name}
          </h1>
          <p className="text-muted" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            {anagrafica.tipo === 'PF' ? (
              <>
                <PersonIcon size={16} />
                Persona Fisica
              </>
            ) : (
              <>
                <BusinessIcon size={16} />
                Persona Giuridica
              </>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link to={`/anagrafiche/${id}/edit`} className="btn-primary">
            <EditIcon size={18} />
            <span>Modifica</span>
          </Link>

          {anagrafica.cliente && (
            <button
              className="btn-secondary"
              onClick={handlePrintFascicolo}
              title="Stampa Fascicolo Cliente"
            >
              <PrintIcon size={18} />
              <span>Fascicolo</span>
            </button>
          )}

          <button
            className="btn-secondary"
            onClick={handleDelete}
            disabled={deleting}
          >
            <DeleteIcon size={18} />
            <span>{deleting ? 'Eliminazione...' : 'Elimina'}</span>
          </button>
          <button onClick={() => navigate(-1)} className="btn-secondary">
            <ArrowBackIcon size={18} />
            <span>Indietro</span>
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
          aria-label="tabs anagrafica"
        >
          <Tab label="Dati Anagrafici" {...a11yProps(0)} />
          <Tab
            label={
              <Badge badgeContent={praticheTotal} color="primary">
                <span style={{ marginRight: praticheTotal ? '20px' : '0' }}>Pratiche</span>
              </Badge>
            }
            {...a11yProps(1)}
          />
          <Tab
            label={
              <Badge badgeContent={fascicoliTotal} color="primary">
                <span style={{ marginRight: fascicoliTotal ? '20px' : '0' }}>Fascicoli</span>
              </Badge>
            }
            {...a11yProps(2)}
          />
          <Tab
            label={
              <Badge badgeContent={documentiTotal} color="primary">
                <span style={{ marginRight: documentiTotal ? '20px' : '0' }}>Documenti</span>
              </Badge>
            }
            {...a11yProps(3)}
          />
        </Tabs>
      </Box>

      {/* Tab 0: Dati Anagrafici */}
      <TabPanel value={activeTab} index={0}>
      <div className="detail-grid">
        {/* Dati Identificativi */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>📋 Dati Identificativi</h2>
          <div className="detail-row">
            <span className="detail-label">Tipo:</span>
            <span className="detail-value">
              <span className={`badge badge-${anagrafica.tipo === 'PF' ? 'info' : 'success'}`}>
                {anagrafica.tipo === 'PF' ? 'Persona Fisica' : 'Persona Giuridica'}
              </span>
            </span>
          </div>

          {anagrafica.tipo === 'PG' && (
            <div className="detail-row">
              <span className="detail-label">Ragione Sociale:</span>
              <span className="detail-value"><strong>{anagrafica.ragione_sociale}</strong></span>
            </div>
          )}

          {anagrafica.tipo === 'PF' && (
            <>
              <div className="detail-row">
                <span className="detail-label">Nome:</span>
                <span className="detail-value">{anagrafica.nome}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Cognome:</span>
                <span className="detail-value"><strong>{anagrafica.cognome}</strong></span>
              </div>
            </>
          )}

          <div className="detail-row">
            <span className="detail-label">Codice Fiscale:</span>
            <span className="detail-value"><code>{anagrafica.codice_fiscale}</code></span>
          </div>

          {anagrafica.partita_iva && (
            <div className="detail-row">
              <span className="detail-label">Partita IVA:</span>
              <span className="detail-value"><code>{anagrafica.partita_iva}</code></span>
            </div>
          )}

          {anagrafica.codice && (
            <div className="detail-row">
              <span className="detail-label">Codice:</span>
              <span className="detail-value">
                <code>{anagrafica.codice}</code>
                <button
                  onClick={handleRicalcolaCodice}
                  className="btn btn-sm btn-secondary"
                  style={{ marginLeft: '0.5rem' }}
                  title="Ricalcola codice anagrafica"
                >
                  <RefreshIcon size={14} />
                  <span>Ricalcola</span>
                </button>
              </span>
            </div>
          )}

          {!anagrafica.codice && (
            <div className="detail-row">
              <span className="detail-label">Codice:</span>
              <span className="detail-value">
                <span className="text-muted">Non generato</span>
                <button
                  onClick={handleRicalcolaCodice}
                  className="btn btn-sm btn-primary"
                  style={{ marginLeft: '0.5rem' }}
                  title="Genera codice anagrafica"
                >
                  <AddIcon size={14} />
                  <span>Genera Codice</span>
                </button>
              </span>
            </div>
          )}
        </div>

        {/* Contatti */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <PhoneIcon size={20} />
            Contatti
          </h2>

          {anagrafica.pec && (
            <div className="detail-row">
              <span className="detail-label">PEC:</span>
              <span className="detail-value" style={{ minWidth: 0 }}>
                <a
                  href={`mailto:${anagrafica.pec}`}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    wordBreak: 'break-all',
                    overflowWrap: 'anywhere',
                    minWidth: 0
                  }}
                >
                  <span style={{ flexShrink: 0 }}>
                    <EmailIcon size={16} />
                  </span>
                  {anagrafica.pec}
                </a>
              </span>
            </div>
          )}

          {anagrafica.email && (
            <div className="detail-row">
              <span className="detail-label">Email:</span>
              <span className="detail-value" style={{ minWidth: 0 }}>
                <a
                  href={`mailto:${anagrafica.email}`}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    wordBreak: 'break-all',
                    overflowWrap: 'anywhere',
                    minWidth: 0
                  }}
                >
                  <span style={{ flexShrink: 0 }}>
                    <EmailIcon size={16} />
                  </span>
                  {anagrafica.email}
                </a>
              </span>
            </div>
          )}

          {anagrafica.telefono && (
            <div className="detail-row">
              <span className="detail-label">Telefono:</span>
              <span className="detail-value">
                <a href={`tel:${anagrafica.telefono}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                  <PhoneIcon size={16} />
                  {anagrafica.telefono}
                </a>
              </span>
            </div>
          )}

          {anagrafica.indirizzo && (
            <div className="detail-row">
              <span className="detail-label">Indirizzo:</span>
              <span className="detail-value">
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                  <LocationIcon size={16} />
                  {anagrafica.indirizzo}
                </span>
              </span>
            </div>
          )}
        </div>

        {/* Gestione Cliente */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ClientIcon size={20} />
            Gestione Cliente
          </h2>

          <div className="detail-row">
            <span className="detail-label">Status:</span>
            <span className="detail-value">
              {anagrafica.cliente ? (
                <span className="badge badge-primary">
                  <CheckIcon size={16} /> Cliente Attivo
                </span>
              ) : (
                <>
                  <span className="badge">Non Cliente</span>
                  <button
                    onClick={handleMakeCliente}
                    className="btn btn-sm btn-primary"
                    style={{ marginLeft: '0.5rem' }}
                  >
                    Converti in Cliente
                  </button>
                </>
              )}
            </span>
          </div>

          {anagrafica.cliente && (
            <>
              {anagrafica.cliente.tipo_cliente_display && (
                <div className="detail-row">
                  <span className="detail-label">Tipo Cliente:</span>
                  <span className="detail-value">
                    <span className="badge badge-info">
                      {anagrafica.cliente.tipo_cliente_display}
                    </span>
                  </span>
                </div>
              )}

              {anagrafica.cliente.cliente_dal && (
                <div className="detail-row">
                  <span className="detail-label">Cliente dal:</span>
                  <span className="detail-value">
                    {new Date(anagrafica.cliente.cliente_dal).toLocaleDateString('it-IT')}
                  </span>
                </div>
              )}

              {anagrafica.cliente.cliente_al && (
                <div className="detail-row">
                  <span className="detail-label">Cliente al:</span>
                  <span className="detail-value">
                    {new Date(anagrafica.cliente.cliente_al).toLocaleDateString('it-IT')}
                  </span>
                </div>
              )}

              {anagrafica.cliente.codice_destinatario && (
                <div className="detail-row">
                  <span className="detail-label">Codice Destinatario SDI:</span>
                  <span className="detail-value">
                    <code style={{ fontSize: '1.1em', padding: '0.25rem 0.5rem', background: 'var(--bg-secondary)', borderRadius: '4px' }}>
                      {anagrafica.cliente.codice_destinatario}
                    </code>
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Informazioni Sistema */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>🕒 Informazioni Sistema</h2>

          <div className="detail-row">
            <span className="detail-label">Creata il:</span>
            <span className="detail-value">
              {new Date(anagrafica.created_at).toLocaleString('it-IT')}
            </span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Aggiornata il:</span>
            <span className="detail-value">
              {new Date(anagrafica.updated_at).toLocaleString('it-IT')}
            </span>
          </div>
        </div>

        {/* Note */}
        {anagrafica.note && (
          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <InfoIcon size={20} />
              Note
            </h2>
            <p style={{ whiteSpace: 'pre-wrap' }}>{anagrafica.note}</p>
          </div>
        )}

        {/* Gestione Indirizzi */}
        <div style={{ gridColumn: '1 / -1' }}>
          <IndirizziManager
            anagraficaId={Number(id)}
            indirizzi={anagrafica.indirizzi || []}
            onUpdate={loadAnagrafica}
          />
        </div>

        {/* Gestione Contatti Email */}
        <div style={{ gridColumn: '1 / -1' }}>
          <ContattiEmailManager
            anagraficaId={Number(id)}
            contatti={anagrafica.contatti_email || []}
            onUpdate={loadAnagrafica}
          />
        </div>
      </div>
      </TabPanel>

      {/* Tab 1: Pratiche */}
      <TabPanel value={activeTab} index={1}>
        {!clienteId ? (
          <div className="card">
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '1rem', margin: 0 }}>
              Questa anagrafica non è ancora un cliente: convertila in cliente per vedere qui le pratiche collegate.
            </p>
          </div>
        ) : (
          <>
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="filters-grid">
                <div className="form-group">
                  <label>Ricerca</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Cerca per codice, oggetto..."
                    value={praticheSearch}
                    onChange={(e) => { setPraticheSearch(e.target.value); setPraticheAllPage(1); }}
                  />
                </div>
                <div className="form-group">
                  <label>Tipo Pratica</label>
                  <select
                    className="form-control"
                    value={praticheTipo}
                    onChange={(e) => { setPraticheTipo(e.target.value); setPraticheAllPage(1); }}
                  >
                    <option value="">Tutti i tipi</option>
                    {tipiPratica.map((tipo) => (
                      <option key={tipo.id} value={tipo.id}>{tipo.nome}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Stato</label>
                  <select
                    className="form-control"
                    value={praticheStato}
                    onChange={(e) => { setPraticheStato(e.target.value); setPraticheAllPage(1); }}
                  >
                    <option value="">Tutti gli stati</option>
                    <option value="aperta">Aperta</option>
                    <option value="lavorazione">In lavorazione</option>
                    <option value="attesa">In attesa</option>
                    <option value="chiusa">Chiusa</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Data Apertura Da</label>
                  <input
                    type="date"
                    className="form-control"
                    value={praticheDataDa}
                    onChange={(e) => { setPraticheDataDa(e.target.value); setPraticheAllPage(1); }}
                  />
                </div>
                <div className="form-group">
                  <label>Data Apertura A</label>
                  <input
                    type="date"
                    className="form-control"
                    value={praticheDataA}
                    onChange={(e) => { setPraticheDataA(e.target.value); setPraticheAllPage(1); }}
                  />
                </div>
              </div>
              {(praticheSearch || praticheTipo || praticheStato || praticheDataDa || praticheDataA) && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                  <button onClick={resetPraticheFiltri} className="btn-secondary">Reset Filtri</button>
                </div>
              )}
            </div>

            <div className="card">
              <div style={{ marginBottom: '1rem', color: '#6c757d' }}>
                {praticheLoading ? 'Caricamento...' : `Totale: ${praticheTotal} pratiche`}
              </div>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Codice</th>
                      <th>Tipo</th>
                      <th>Oggetto</th>
                      <th>Stato</th>
                      <th>Data Apertura</th>
                      <th style={{ width: '80px' }}>Azioni</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pratiche.length === 0 ? (
                      <tr>
                        <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
                          Nessuna pratica trovata
                        </td>
                      </tr>
                    ) : (
                      pratiche.map((pratica) => (
                        <tr key={pratica.id}>
                          <td><strong>{pratica.codice}</strong></td>
                          <td>{pratica.tipo_detail?.nome}</td>
                          <td>{pratica.oggetto}</td>
                          <td><span className="badge">{pratica.stato_display}</span></td>
                          <td>{new Date(pratica.data_apertura).toLocaleDateString('it-IT')}</td>
                          <td>
                            <button
                              onClick={() => navigate(`/pratiche/${pratica.id}`)}
                              className="btn-icon"
                              title="Visualizza pratica"
                            >
                              <VisibilityIcon size={18} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              {praticheTotalPages > 1 && (
                <div className="pagination">
                  <button
                    onClick={() => setPraticheAllPage((p) => p - 1)}
                    disabled={praticheAllPage === 1}
                    className="btn-secondary"
                  >
                    Precedente
                  </button>
                  <span>Pagina {praticheAllPage} di {praticheTotalPages}</span>
                  <button
                    onClick={() => setPraticheAllPage((p) => p + 1)}
                    disabled={praticheAllPage === praticheTotalPages}
                    className="btn-secondary"
                  >
                    Successiva
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </TabPanel>

      {/* Tab 2: Fascicoli */}
      <TabPanel value={activeTab} index={2}>
        {!clienteId ? (
          <div className="card">
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '1rem', margin: 0 }}>
              Questa anagrafica non è ancora un cliente: convertila in cliente per vedere qui i fascicoli collegati.
            </p>
          </div>
        ) : (
          <>
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="filters-grid">
                <div className="form-group">
                  <label>Ricerca</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Cerca per codice, titolo..."
                    value={fascicoliSearch}
                    onChange={(e) => { setFascicoliSearch(e.target.value); setFascicoliPage(1); }}
                  />
                </div>
                <div className="form-group">
                  <label>Anno</label>
                  <select
                    className="form-control"
                    value={fascicoliAnno}
                    onChange={(e) => { setFascicoliAnno(e.target.value); setFascicoliPage(1); }}
                  >
                    <option value="">Tutti gli anni</option>
                    {anniFascicoli.map((anno) => (
                      <option key={anno} value={anno}>{anno}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Stato</label>
                  <select
                    className="form-control"
                    value={fascicoliStato}
                    onChange={(e) => { setFascicoliStato(e.target.value); setFascicoliPage(1); }}
                  >
                    <option value="">Tutti gli stati</option>
                    {statiFascicolo.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              {(fascicoliSearch || fascicoliAnno || fascicoliStato) && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                  <button onClick={resetFascicoliFiltri} className="btn-secondary">Reset Filtri</button>
                </div>
              )}
            </div>

            <div className="card">
              <div style={{ marginBottom: '1rem', color: '#6c757d' }}>
                {fascicoliLoading ? 'Caricamento...' : `Totale: ${fascicoliTotal} fascicoli`}
              </div>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Codice</th>
                      <th>Titolo</th>
                      <th>Anno</th>
                      <th>Stato</th>
                      <th style={{ width: '80px' }}>Azioni</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fascicoli.length === 0 ? (
                      <tr>
                        <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
                          Nessun fascicolo trovato
                        </td>
                      </tr>
                    ) : (
                      fascicoli.map((fascicolo) => (
                        <tr key={fascicolo.id}>
                          <td><strong>{fascicolo.codice}</strong></td>
                          <td>{fascicolo.titolo}</td>
                          <td>{fascicolo.anno}</td>
                          <td><span className="badge">{fascicolo.stato_display}</span></td>
                          <td>
                            <button
                              onClick={() => navigate(`/fascicoli/${fascicolo.id}`)}
                              className="btn-icon"
                              title="Visualizza fascicolo"
                            >
                              <VisibilityIcon size={18} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              {fascicoliTotalPages > 1 && (
                <div className="pagination">
                  <button
                    onClick={() => setFascicoliPage((p) => p - 1)}
                    disabled={fascicoliPage === 1}
                    className="btn-secondary"
                  >
                    Precedente
                  </button>
                  <span>Pagina {fascicoliPage} di {fascicoliTotalPages}</span>
                  <button
                    onClick={() => setFascicoliPage((p) => p + 1)}
                    disabled={fascicoliPage === fascicoliTotalPages}
                    className="btn-secondary"
                  >
                    Successiva
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </TabPanel>

      {/* Tab 3: Documenti */}
      <TabPanel value={activeTab} index={3}>
        {!clienteId ? (
          <div className="card">
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '1rem', margin: 0 }}>
              Questa anagrafica non è ancora un cliente: convertila in cliente per vedere qui i documenti collegati.
            </p>
          </div>
        ) : (
          <>
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="filters-grid">
                <div className="form-group">
                  <label>Ricerca</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Cerca per codice, descrizione..."
                    value={documentiSearch}
                    onChange={(e) => { setDocumentiSearch(e.target.value); setDocumentiPage(1); }}
                  />
                </div>
                <div className="form-group">
                  <label>Tipo Documento</label>
                  <select
                    className="form-control"
                    value={documentiTipo}
                    onChange={(e) => { setDocumentiTipo(e.target.value); setDocumentiPage(1); }}
                  >
                    <option value="">Tutti i tipi</option>
                    {tipiDocumento.map((tipo) => (
                      <option key={tipo.id} value={tipo.id}>{tipo.nome}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Stato</label>
                  <select
                    className="form-control"
                    value={documentiStato}
                    onChange={(e) => { setDocumentiStato(e.target.value); setDocumentiPage(1); }}
                  >
                    <option value="">Tutti gli stati</option>
                    <option value="bozza">Bozza</option>
                    <option value="definitivo">Definitivo</option>
                    <option value="archiviato">Archiviato</option>
                    <option value="uscito">Uscito</option>
                    <option value="consegnato">Consegnato</option>
                    <option value="scaricato">Scaricato</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Data Da</label>
                  <input
                    type="date"
                    className="form-control"
                    value={documentiDataDa}
                    onChange={(e) => { setDocumentiDataDa(e.target.value); setDocumentiPage(1); }}
                  />
                </div>
                <div className="form-group">
                  <label>Data A</label>
                  <input
                    type="date"
                    className="form-control"
                    value={documentiDataA}
                    onChange={(e) => { setDocumentiDataA(e.target.value); setDocumentiPage(1); }}
                  />
                </div>
              </div>
              {(documentiSearch || documentiTipo || documentiStato || documentiDataDa || documentiDataA) && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                  <button onClick={resetDocumentiFiltri} className="btn-secondary">Reset Filtri</button>
                </div>
              )}
            </div>

            <div className="card">
              <div style={{ marginBottom: '1rem', color: '#6c757d' }}>
                {documentiLoading ? 'Caricamento...' : `Totale: ${documentiTotal} documenti`}
              </div>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Codice</th>
                      <th>Descrizione</th>
                      <th>Tipo</th>
                      <th>Data</th>
                      <th>Stato</th>
                      <th style={{ width: '80px' }}>Azioni</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documenti.length === 0 ? (
                      <tr>
                        <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
                          Nessun documento trovato
                        </td>
                      </tr>
                    ) : (
                      documenti.map((documento) => (
                        <tr key={documento.id}>
                          <td><strong>{documento.codice}</strong></td>
                          <td>{documento.descrizione}</td>
                          <td>
                            {documento.tipo_detail ? (
                              <Link to={`/documenti/tipi/${documento.tipo_detail.codice}`} style={{ color: '#2563eb', textDecoration: 'none' }}>
                                {documento.tipo_detail.nome}
                              </Link>
                            ) : '-'}
                          </td>
                          <td>{new Date(documento.data_documento).toLocaleDateString('it-IT')}</td>
                          <td><span className="badge">{documento.stato}</span></td>
                          <td>
                            <button
                              onClick={() => navigate(`/documenti/${documento.id}`)}
                              className="btn-icon"
                              title="Visualizza documento"
                            >
                              <VisibilityIcon size={18} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              {documentiTotalPages > 1 && (
                <div className="pagination">
                  <button
                    onClick={() => setDocumentiPage((p) => p - 1)}
                    disabled={documentiPage === 1}
                    className="btn-secondary"
                  >
                    Precedente
                  </button>
                  <span>Pagina {documentiPage} di {documentiTotalPages}</span>
                  <button
                    onClick={() => setDocumentiPage((p) => p + 1)}
                    disabled={documentiPage === documentiTotalPages}
                    className="btn-secondary"
                  >
                    Successiva
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </TabPanel>
    </div>
  );
}

const extractAxiosMessage = (error: unknown): string | null => {
  if (isAxiosError(error)) {
    const data = error.response?.data as { detail?: string; error?: string } | undefined;
    return data?.detail ?? data?.error ?? error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return null;
};
