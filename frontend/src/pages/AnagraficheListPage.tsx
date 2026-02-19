import { useState, useEffect, useRef, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { AnagraficaList, AnagraficheListResponse, AnagraficaFilters, ClientiTipo, TipoSoggetto } from '../types/anagrafiche';
import { AddIcon, DownloadIcon, PrintIcon, AnagraficheIcon, PersonIcon, BusinessIcon, EmailIcon, VisibilityIcon } from '../components/icons/Icons';

export function AnagraficheListPage() {
  const [anagrafiche, setAnagrafiche] = useState<AnagraficaList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tipiCliente, setTipiCliente] = useState<ClientiTipo[]>([]);
  const [filters, setFilters] = useState<AnagraficaFilters>({
    search: '',
    tipo: '',
    is_cliente: '',
    tipo_cliente: '',
    page: 1,
    page_size: 20,
  });
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [ordering, setOrdering] = useState<string>('nominativo'); // Default: ordinamento alfabetico
  const [searchQuery, setSearchQuery] = useState(''); // Valore locale per l'input

  // Debounce per la ricerca (per lettori di codici a barre)
  const searchTimeoutRef = useRef<number | null>(null);

  const loadTipiCliente = useCallback(async () => {
    try {
      type TipiClienteResponse = { results?: ClientiTipo[] } | ClientiTipo[];
      const response = await apiClient.get<TipiClienteResponse>('/tipi-cliente/');
      const data = Array.isArray(response.data)
        ? response.data
        : response.data.results ?? [];
      setTipiCliente(data);
    } catch (error) {
      console.error('Error loading tipi cliente:', error);
    }
  }, []);

  const loadAnagrafiche = useCallback(async () => {
    try {
      setLoading(true);
      
      // Build query params
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.tipo) params.append('tipo', filters.tipo);
      if (filters.is_cliente !== '') params.append('is_cliente', String(filters.is_cliente));
      if (filters.tipo_cliente) params.append('tipo_cliente', String(filters.tipo_cliente));
      if (filters.page) params.append('page', String(filters.page));
      if (filters.page_size) params.append('page_size', String(filters.page_size));
      if (ordering) params.append('ordering', ordering); // Aggiungi ordinamento

      const response = await apiClient.get<AnagraficheListResponse>(`/anagrafiche/?${params}`);
      
      setAnagrafiche(response.data.results);
      setTotalCount(response.data.count);
      setTotalPages(Math.ceil(response.data.count / (filters.page_size || 20)));
      setError(null);
    } catch (error: unknown) {
      setError(getListErrorMessage(error, 'Errore nel caricamento delle anagrafiche'));
      console.error('Error loading anagrafiche:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, ordering]);

  useEffect(() => {
    void loadTipiCliente();
  }, [loadTipiCliente]);

  useEffect(() => {
    void loadAnagrafiche();
  }, [loadAnagrafiche]);

  // Cleanup del timeout quando il componente viene smontato
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);


  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value); // Aggiorna immediatamente il valore visibile
    
    // Cancella il timeout precedente se esiste
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Imposta un nuovo timeout per la ricerca (500ms di attesa)
    // Questo permette al lettore di codici a barre di completare la scansione
    searchTimeoutRef.current = window.setTimeout(() => {
      setFilters({ ...filters, search: value, page: 1 });
    }, 500);
  };

  const handleFilterChange = <K extends keyof AnagraficaFilters>(key: K, value: AnagraficaFilters[K]) => {
    setFilters({ ...filters, [key]: value, page: 1 });
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setFilters({
      search: '',
      tipo: '',
      is_cliente: '',
      tipo_cliente: '',
      page: 1,
      page_size: 20,
    });
    setOrdering('nominativo');
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
    window.scrollTo(0, 0);
  };

  const handleSort = (field: string) => {
    // Se clicco sulla stessa colonna, inverti l'ordine
    if (ordering === field) {
      setOrdering(`-${field}`);
    } else if (ordering === `-${field}`) {
      setOrdering(field);
    } else {
      setOrdering(field);
    }
  };

  const getSortIcon = (field: string) => {
    if (ordering === field) return ' ▲';
    if (ordering === `-${field}`) return ' ▼';
    return '';
  };

  const handleExportCSV = async () => {
    try {
      // Build query params (same as loadAnagrafiche)
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.tipo) params.append('tipo', filters.tipo);
      if (filters.is_cliente !== '') params.append('is_cliente', String(filters.is_cliente));
      if (filters.tipo_cliente) params.append('tipo_cliente', String(filters.tipo_cliente));

      // Download CSV
      const response = await apiClient.get(`/anagrafiche/export_csv/?${params}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `anagrafiche_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error: unknown) {
      alert('Errore nell\'esportazione CSV: ' + getListErrorMessage(error, 'Errore sconosciuto'));
    }
  };

  const handleExportPDF = async () => {
    try {
      // Build query params
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.tipo) params.append('tipo', filters.tipo);
      if (filters.is_cliente !== '') params.append('is_cliente', String(filters.is_cliente));
      if (filters.tipo_cliente) params.append('tipo_cliente', String(filters.tipo_cliente));

      // Download PDF
      const response = await apiClient.get(`/anagrafiche/export_pdf/?${params}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `elenco_anagrafiche_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error: unknown) {
      alert('Errore nella stampa PDF: ' + getListErrorMessage(error, 'Errore sconosciuto'));
    }
  };

  if (loading && anagrafiche.length === 0) {
    return (
      <div className="page-container">
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AnagraficheIcon size={32} />
          Anagrafiche
        </h1>
        <p>Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AnagraficheIcon size={32} />
            Anagrafiche
          </h1>
          <p className="text-muted">Gestione clienti e fornitori ({totalCount} totali)</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link to="/anagrafiche/new" className="btn-primary">
            <AddIcon size={18} />
            <span>Nuova Anagrafica</span>
          </Link>
          <Link to="/anagrafiche/import" className="btn-secondary" title="Importa da CSV">
            <DownloadIcon size={18} />
            <span>Importa CSV</span>
          </Link>
          <button 
            onClick={handleExportCSV}
            className="btn-secondary"
            disabled={loading || anagrafiche.length === 0}
            title="Esporta in CSV"
          >
            <DownloadIcon size={18} />
            <span>Esporta CSV</span>
          </button>
          <button 
            onClick={handleExportPDF}
            className="btn-secondary"
            disabled={loading || anagrafiche.length === 0}
            title="Stampa PDF"
          >
            <PrintIcon size={18} />
            <span>PDF</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>Filtri di Ricerca</h3>
          <button
            onClick={handleResetFilters}
            className="btn-secondary"
            style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
          >
            🔄 Reset Filtri
          </button>
        </div>
        <div className="filters-grid">
          <div className="form-group">
            <input
              type="text"
              className="form-control"
              placeholder="🔍 Cerca per nome, CF, P.IVA, email..."
              value={searchQuery}
              onChange={handleSearchChange}
            />
          </div>

          <div className="form-group">
            <select
              className="form-control"
              value={filters.tipo}
              onChange={(e) =>
                handleFilterChange('tipo', e.target.value as TipoSoggetto | '')
              }
            >
              <option value="">Tutti i tipi</option>
              <option value="PF">Persona Fisica</option>
              <option value="PG">Persona Giuridica</option>
            </select>
          </div>

          <div className="form-group">
            <select
              className="form-control"
              value={String(filters.is_cliente)}
              onChange={(e) => handleFilterChange('is_cliente', e.target.value === '' ? '' : e.target.value === 'true')}
            >
              <option value="">Tutti</option>
              <option value="true">Solo Clienti</option>
              <option value="false">Non Clienti</option>
            </select>
          </div>

          <div className="form-group">
            <select
              className="form-control"
              value={filters.tipo_cliente || ''}
              onChange={(e) => handleFilterChange('tipo_cliente', e.target.value ? Number(e.target.value) : '')}
              disabled={filters.is_cliente !== true}
            >
              <option value="">Tutti i tipi cliente</option>
              {tipiCliente.map(tipo => (
                <option key={tipo.id} value={tipo.id}>
                  {tipo.descrizione}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      {/* Table */}
      <div className="card">
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th 
                  className="sortable"
                  onClick={() => handleSort('nominativo')} 
                  title="Clicca per ordinare"
                >
                  Nominativo{getSortIcon('nominativo')}
                </th>
                <th 
                  className="sortable"
                  onClick={() => handleSort('codice')} 
                  title="Clicca per ordinare"
                >
                  Codice{getSortIcon('codice')}
                </th>
                <th 
                  className="sortable"
                  onClick={() => handleSort('tipo')} 
                  title="Clicca per ordinare"
                >
                  Tipo{getSortIcon('tipo')}
                </th>
                <th 
                  className="sortable"
                  onClick={() => handleSort('codice_fiscale')} 
                  title="Clicca per ordinare"
                >
                  Codice Fiscale{getSortIcon('codice_fiscale')}
                </th>
                <th 
                  className="sortable"
                  onClick={() => handleSort('partita_iva')} 
                  title="Clicca per ordinare"
                >
                  P.IVA{getSortIcon('partita_iva')}
                </th>
                <th>Email/PEC</th>
                <th>Telefono</th>
                <th>Tag</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {anagrafiche.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '2rem' }}>
                    {filters.search || filters.tipo || filters.is_cliente !== '' 
                      ? '🔍 Nessun risultato trovato'
                      : '📭 Nessuna anagrafica presente'}
                  </td>
                </tr>
              ) : (
                anagrafiche.map((anagrafica) => (
                  <tr key={anagrafica.id}>
                    <td>
                      <Link to={`/anagrafiche/${anagrafica.id}`} className="link-primary">
                        <strong>{anagrafica.display_name}</strong>
                      </Link>
                    </td>
                    <td>
                      {anagrafica.codice ? (
                        <code style={{ fontSize: '0.9em', fontWeight: 'bold' }}>{anagrafica.codice}</code>
                      ) : (
                        <span style={{ color: '#999', fontSize: '0.85em' }}>-</span>
                      )}
                    </td>
                    <td>
                      <span className={`badge badge-${anagrafica.tipo === 'PF' ? 'info' : 'success'}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        {anagrafica.tipo === 'PF' ? (
                          <>
                            <PersonIcon size={14} />
                            PF
                          </>
                        ) : (
                          <>
                            <BusinessIcon size={14} />
                            PG
                          </>
                        )}
                      </span>
                    </td>
                    <td><code>{anagrafica.codice_fiscale}</code></td>
                    <td>{anagrafica.partita_iva ? <code>{anagrafica.partita_iva}</code> : '-'}</td>
                    <td>
                      {anagrafica.pec && (
                        <div title="PEC" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <EmailIcon size={14} />
                          <small>{anagrafica.pec}</small>
                        </div>
                      )}
                      {anagrafica.email && (
                        <div title="Email" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <EmailIcon size={14} />
                          <small>{anagrafica.email}</small>
                        </div>
                      )}
                      {!anagrafica.pec && !anagrafica.email && '-'}
                    </td>
                    <td>{anagrafica.telefono || '-'}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                        {anagrafica.is_cliente && <span className="badge badge-primary">Cliente</span>}
                      </div>
                    </td>
                    <td>
                      <Link to={`/anagrafiche/${anagrafica.id}`} className="btn btn-sm btn-secondary">
                        <VisibilityIcon size={16} />
                        <span>Dettagli</span>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            <button
              className="btn btn-secondary"
              disabled={filters.page === 1}
              onClick={() => handlePageChange((filters.page || 1) - 1)}
            >
              ← Precedente
            </button>
            <span className="pagination-info">
              Pagina {filters.page} di {totalPages}
            </span>
            <button
              className="btn btn-secondary"
              disabled={filters.page === totalPages}
              onClick={() => handlePageChange((filters.page || 1) + 1)}
            >
              Successiva →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const getListErrorMessage = (error: unknown, fallback: string): string => {
  if (isAxiosError(error)) {
    const data = error.response?.data as { detail?: string; error?: string } | undefined;
    return data?.detail ?? data?.error ?? error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
};
