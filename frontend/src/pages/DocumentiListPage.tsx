import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { documentiApi } from '@/api/documenti';
import type {
  Documento,
  DocumentoFilters,
  DocumentiTipo,
} from '@/types/documento';
import {
  AddIcon,
  DownloadIcon,
  DocumentiIcon,
  VisibilityIcon,
  EditIcon,
  DeleteIcon,
  UploadIcon,
} from '@/components/icons/Icons';

export function DocumentiListPage() {
  const navigate = useNavigate();
  const [documenti, setDocumenti] = useState<Documento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tipiDocumento, setTipiDocumento] = useState<DocumentiTipo[]>([]);
  const [filters, setFilters] = useState<DocumentoFilters>({
    search: '',
    ordering: '-data_documento',
  });
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const pageSize = 20;

  // Stati per la ricerca con debounce
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');

  // Debounce per la ricerca (per lettori di codici a barre)
  const searchTimeoutRef = useRef<number | null>(null);

  const loadTipiDocumento = useCallback(async () => {
    try {
      const data = await documentiApi.listTipi();
      setTipiDocumento(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading tipi documento:', error);
      setTipiDocumento([]);
    }
  }, []);

  const loadDocumenti = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await documentiApi.list(filters, currentPage, pageSize);

      setDocumenti(response.results);
      setTotalCount(response.count);
      setTotalPages(Math.ceil(response.count / pageSize));
    } catch (error) {
      console.error('Error loading documenti:', error);
      setError('Errore nel caricamento dei documenti');
    } finally {
      setLoading(false);
    }
  }, [filters, currentPage]);

  useEffect(() => {
    void loadTipiDocumento();
  }, [loadTipiDocumento]);

  useEffect(() => {
    void loadDocumenti();
  }, [loadDocumenti]);

  // Debounce effect per la ricerca
  useEffect(() => {
    // Cancella il timeout precedente se esiste
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Imposta un nuovo timeout per la ricerca (300ms di attesa)
    // Questo permette al lettore di codici a barre di completare la scansione
    // e rende la digitazione più fluida
    searchTimeoutRef.current = window.setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 300);

    // Cleanup del timeout
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  // Aggiorna i filtri quando cambia la query debouncata
  useEffect(() => {
    setFilters((prev) => ({
      ...prev,
      search: debouncedSearchQuery,
    }));
    setCurrentPage(1);
  }, [debouncedSearchQuery]);


  const handleFilterChange = <K extends keyof DocumentoFilters>(key: K, value: DocumentoFilters[K]) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
    setCurrentPage(1);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
  };

  const handleSort = (field: string) => {
    const currentOrdering = filters.ordering || '';
    let newOrdering = field;

    if (currentOrdering === field) {
      newOrdering = `-${field}`;
    } else if (currentOrdering === `-${field}`) {
      newOrdering = field;
    }

    setFilters((prev) => ({
      ...prev,
      ordering: newOrdering,
    }));
  };

  const getSortIcon = (field: string) => {
    const currentOrdering = filters.ordering || '';
    if (currentOrdering === field) {
      return ' ↑';
    } else if (currentOrdering === `-${field}`) {
      return ' ↓';
    }
    return '';
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDownload = async (documento: Documento) => {
    try {
      await documentiApi.downloadFile(documento.id);
    } catch (error) {
      console.error('Error downloading document:', error);
      alert('Errore durante il download del documento');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo documento?')) {
      return;
    }

    try {
      await documentiApi.delete(id);
      void loadDocumenti();
    } catch (error) {
      console.error('Error deleting document:', error);
      alert('Errore durante l\'eliminazione del documento');
    }
  };

  const getStatoBadgeClass = (stato: string) => {
    const classes: Record<string, string> = {
      bozza: 'badge-warning',
      definitivo: 'badge-success',
      protocollato: 'badge-info',
      archiviato: 'badge-secondary',
      annullato: 'badge-danger',
    };
    return classes[stato] || 'badge-secondary';
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <DocumentiIcon size={32} />
            Documenti
          </h1>
          <p className="text-muted">Gestione documenti ({totalCount} totali)</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link to="/import" className="btn-secondary">
            <UploadIcon size={18} />
            <span>Importa Documenti</span>
          </Link>
          <Link to="/documenti/new" className="btn-primary">
            <AddIcon size={18} />
            <span>Nuovo Documento</span>
          </Link>
        </div>
      </div>

      {/* Filtri */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="filters-grid">
          {/* Ricerca */}
          <div className="form-group">
            <input
              type="text"
              className="form-control"
              placeholder="🔍 Cerca per codice, descrizione..."
              value={searchQuery}
              onChange={handleSearchChange}
            />
          </div>

          {/* Tipo Documento */}
          <div className="form-group">
            <select
              className="form-control"
              value={filters.tipo || ''}
              onChange={(e) => handleFilterChange('tipo', e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">Tutti i tipi</option>
              {tipiDocumento && tipiDocumento.map((tipo) => (
                <option key={tipo.id} value={tipo.id}>
                  {tipo.nome}
                </option>
              ))}
            </select>
          </div>

          {/* Stato */}
          <div className="form-group">
            <select
              className="form-control"
              value={filters.stato || ''}
              onChange={(e) => handleFilterChange('stato', e.target.value || undefined)}
            >
              <option value="">Tutti gli stati</option>
              <option value="bozza">Bozza</option>
              <option value="definitivo">Definitivo</option>
              <option value="protocollato">Protocollato</option>
              <option value="archiviato">Archiviato</option>
              <option value="annullato">Annullato</option>
            </select>
          </div>

          {/* Formato */}
          <div className="form-group">
            <select
              className="form-control"
              value={filters.digitale === undefined ? '' : String(filters.digitale)}
              onChange={(e) => {
                const value = e.target.value;
                handleFilterChange('digitale', value === '' ? undefined : value === 'true');
              }}
            >
              <option value="">Tutti i formati</option>
              <option value="true">Digitale</option>
              <option value="false">Cartaceo</option>
            </select>
          </div>

          {/* Data Da */}
          <div className="form-group">
            <input
              type="date"
              className="form-control"
              placeholder="Data da"
              value={filters.data_da || ''}
              onChange={(e) => handleFilterChange('data_da', e.target.value || undefined)}
            />
          </div>

          {/* Data A */}
          <div className="form-group">
            <input
              type="date"
              className="form-control"
              placeholder="Data a"
              value={filters.data_a || ''}
              onChange={(e) => handleFilterChange('data_a', e.target.value || undefined)}
            />
          </div>
        </div>

        {/* Reset filtri */}
        {(filters.search || filters.tipo || filters.stato || filters.digitale !== undefined || filters.data_da || filters.data_a) && (
          <div style={{ marginTop: '1rem', textAlign: 'center' }}>
            <button
              onClick={() => {
                setFilters({ ordering: '-data_documento' });
                setCurrentPage(1);
              }}
              className="btn-secondary"
              style={{ fontSize: '0.875rem' }}
            >
              Reset filtri
            </button>
          </div>
        )}
      </div>

      {/* Risultati */}
      <div className="card">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p>Caricamento...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#dc3545' }}>
            <p>{error}</p>
            <button onClick={loadDocumenti} className="btn-primary" style={{ marginTop: '1rem' }}>
              Riprova
            </button>
          </div>
        ) : !documenti || documenti.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#6c757d' }}>
            <DocumentiIcon size={64} />
            <p style={{ marginTop: '1rem' }}>Nessun documento trovato</p>
          </div>
        ) : (
          <>
            {/* Tabella */}
            <div style={{ overflowX: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th onClick={() => handleSort('codice')} style={{ cursor: 'pointer' }}>
                      Codice{getSortIcon('codice')}
                    </th>
                    <th onClick={() => handleSort('data_documento')} style={{ cursor: 'pointer' }}>
                      Data{getSortIcon('data_documento')}
                    </th>
                    <th>Tipo</th>
                    <th>Descrizione</th>
                    <th>Cliente</th>
                    <th>Stato</th>
                    <th>Formato</th>
                    <th style={{ textAlign: 'right' }}>Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {documenti && documenti.map((documento) => (
                    <tr 
                      key={documento.id}
                      style={{ cursor: 'pointer' }}
                      onClick={(e) => {
                        // Non navigare se si clicca su un pulsante o link
                        if ((e.target as HTMLElement).closest('button, a')) return;
                        navigate(`/documenti/${documento.id}`);
                      }}
                    >
                      <td>
                        <Link 
                          to={`/documenti/${documento.id}`}
                          style={{ color: '#007bff', textDecoration: 'none', fontWeight: '600' }}
                          title="Visualizza dettaglio"
                        >
                          {documento.codice}
                        </Link>
                      </td>
                      <td>
                        {new Date(documento.data_documento).toLocaleDateString('it-IT')}
                      </td>
                      <td>
                        {documento.tipo_detail?.nome || '-'}
                      </td>
                      <td>
                        <Link 
                          to={`/documenti/${documento.id}`}
                          style={{ color: 'inherit', textDecoration: 'none' }}
                          title="Visualizza dettaglio"
                        >
                          <div style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {documento.descrizione}
                          </div>
                        </Link>
                      </td>
                      <td>
                        {documento.cliente_detail?.anagrafica_display || '-'}
                      </td>
                      <td>
                        <span className={`badge ${getStatoBadgeClass(documento.stato)}`}>
                          {documento.stato}
                        </span>
                      </td>
                      <td>
                        {documento.digitale ? '💾 Digitale' : '📄 Cartaceo'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                          <Link
                            to={`/documenti/${documento.id}`}
                            className="btn-icon"
                            title="Visualizza"
                          >
                            <VisibilityIcon size={18} />
                          </Link>
                          <Link
                            to={`/documenti/${documento.id}/edit`}
                            className="btn-icon"
                            title="Modifica"
                          >
                            <EditIcon size={18} />
                          </Link>
                          {documento.file && (
                            <button
                              onClick={() => handleDownload(documento)}
                              className="btn-icon"
                              title="Download"
                            >
                              <DownloadIcon size={18} />
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(documento.id)}
                            className="btn-icon btn-icon-danger"
                            title="Elimina"
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

            {/* Paginazione */}
            {totalPages > 1 && (
              <div className="pagination">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="btn-secondary"
                >
                  ← Precedente
                </button>
                <span className="pagination-info">
                  Pagina {currentPage} di {totalPages}
                </span>
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="btn-secondary"
                >
                  Successiva →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
