/**
 * Fascicoli List Page
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useNavigate } from 'react-router-dom';
import { fascicoliApi } from '@/api/fascicoli';
import type { FascicoloListItem, FascicoloFilters } from '@/types/fascicolo';
import {
  AddIcon,
  DeleteIcon,
  VisibilityIcon,
  SearchIcon,
} from '@/components/icons/Icons';

export default function FascicoliListPage() {
  const navigate = useNavigate();
  const [fascicoli, setFascicoli] = useState<FascicoloListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Filtri
  const [filters, setFilters] = useState<FascicoloFilters>({
    page: 1,
    page_size: 20,
    ordering: '-anno,codice',
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const [selectedAnno, setSelectedAnno] = useState('');
  const [selectedStato, setSelectedStato] = useState('');
  const [showOnlyRoot, setShowOnlyRoot] = useState(false);

  // Debounce per la ricerca (per lettori di codici a barre)
  const searchTimeoutRef = useRef<number | null>(null);

  // Anni disponibili (ultimi 10 anni)
  const currentYear = new Date().getFullYear();
  const anni = Array.from({ length: 10 }, (_, i) => currentYear - i);

  // Stati disponibili
  const stati = [
    { value: 'corrente', label: 'Archivio corrente' },
    { value: 'deposito', label: 'Archivio deposito' },
    { value: 'storico', label: 'Archivio storico' },
    { value: 'scartato', label: 'Scartato' },
  ];

  const getErrorMessage = (err: unknown, fallback: string) => {
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
  };

  const loadFascicoli = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fascicoliApi.list(filters);
      setFascicoli(data.results);
      setTotalCount(data.count);
    } catch (err) {
      console.error('Error loading fascicoli:', err);
      alert(getErrorMessage(err, 'Errore nel caricamento dei fascicoli'));
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadFascicoli();
  }, [loadFascicoli]);

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
      // Esegui la ricerca solo se:
      // - la query è vuota (per resettare i risultati)
      // - oppure contiene almeno 3 caratteri
      if (searchQuery.length === 0 || searchQuery.length >= 3) {
        setDebouncedSearchQuery(searchQuery);
      }
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
      page: 1,
      search: debouncedSearchQuery || undefined,
    }));
  }, [debouncedSearchQuery]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
  };

  const handleAnnoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedAnno(value);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      anno: value ? Number(value) : undefined,
    }));
  };

  const handleStatoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedStato(value);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      stato: value || undefined,
    }));
  };

  const handleShowOnlyRootChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setShowOnlyRoot(checked);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      parent__isnull: checked ? true : undefined,
    }));
  };

  const handleReset = () => {
    setSearchQuery('');
    setDebouncedSearchQuery('');
    setSelectedAnno('');
    setSelectedStato('');
    setShowOnlyRoot(false);
    setFilters({
      page: 1,
      page_size: 20,
      ordering: '-anno,codice',
    });
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo fascicolo?')) return;

    try {
      await fascicoliApi.delete(id);
      await loadFascicoli();
    } catch (err) {
      alert(getErrorMessage(err, 'Errore durante l\'eliminazione'));
    }
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({
      ...prev,
      page: newPage,
    }));
    window.scrollTo(0, 0);
  };

  const handleSortChange = (field: string) => {
    setFilters((prev) => {
      const currentOrdering = prev.ordering || '';
      let newOrdering: string;

      if (currentOrdering === field) {
        newOrdering = `-${field}`;
      } else if (currentOrdering === `-${field}`) {
        newOrdering = field;
      } else {
        newOrdering = field;
      }

      return {
        ...prev,
        ordering: newOrdering,
      };
    });
  };

  const getSortIcon = (field: string) => {
    const currentOrdering = filters.ordering || '';
    if (currentOrdering === field) return ' ▲';
    if (currentOrdering === `-${field}`) return ' ▼';
    return '';
  };

  const getStatoBadgeClass = (stato: string) => {
    switch (stato) {
      case 'corrente':
        return 'badge-success';
      case 'deposito':
        return 'badge-info';
      case 'storico':
        return 'badge-secondary';
      case 'scartato':
        return 'badge-danger';
      default:
        return 'badge-secondary';
    }
  };

  const totalPages = Math.ceil(totalCount / (filters.page_size || 20));
  const currentPage = filters.page || 1;

  if (loading) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento fascicoli...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>
            <span style={{ marginRight: '0.5rem', verticalAlign: 'middle' }}>📁</span>
            Fascicoli
          </h1>
          <p className="text-muted">
            {totalCount} fascicol{totalCount !== 1 ? 'i' : 'o'} trovat{totalCount !== 1 ? 'i' : 'o'}
          </p>
        </div>
        <button onClick={() => navigate('/fascicoli/nuovo')} className="btn-primary">
          <AddIcon size={20} />
          Nuovo Fascicolo
        </button>
      </div>

      {/* Filtri */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="filters-grid">
          {/* Ricerca */}
          <div className="form-group">
            <label>Ricerca</label>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Cerca per codice o titolo (min. 3 caratteri)..."
                className="form-control"
                style={{ paddingLeft: '2.5rem' }}
              />
              <div
                style={{
                  position: 'absolute',
                  left: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#6c757d',
                  pointerEvents: 'none',
                }}
              >
                <SearchIcon size={18} />
              </div>
            </div>
            {searchQuery.length > 0 && searchQuery.length < 3 && (
              <small style={{ color: '#6c757d', marginTop: '0.25rem', display: 'block' }}>
                Digita almeno 3 caratteri per cercare
              </small>
            )}
          </div>

          {/* Anno */}
          <div className="form-group">
            <label>Anno</label>
            <select
              value={selectedAnno}
              onChange={handleAnnoChange}
              className="form-control"
            >
              <option value="">Tutti gli anni</option>
              {anni.map((anno) => (
                <option key={anno} value={anno}>
                  {anno}
                </option>
              ))}
            </select>
          </div>

          {/* Stato */}
          <div className="form-group">
            <label>Stato</label>
            <select
              value={selectedStato}
              onChange={handleStatoChange}
              className="form-control"
            >
              <option value="">Tutti gli stati</option>
              {stati.map((stato) => (
                <option key={stato.value} value={stato.value}>
                  {stato.label}
                </option>
              ))}
            </select>
          </div>

          {/* Solo fascicoli radice */}
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={showOnlyRoot}
                onChange={handleShowOnlyRootChange}
                style={{ marginRight: '0.5rem' }}
              />
              Solo fascicoli principali
            </label>
          </div>

          {/* Reset */}
          <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button onClick={handleReset} className="btn-secondary">
              🔄 Reset
            </button>
          </div>
        </div>
      </div>

      {/* Tabella */}
      <div className="card">
        {fascicoli.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
            <p style={{ color: '#6c757d' }}>Nessun fascicolo trovato</p>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th 
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleSortChange('codice')}
                    >
                      Codice {getSortIcon('codice')}
                    </th>
                    <th>Titolo</th>
                    <th 
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleSortChange('anno')}
                    >
                      Anno {getSortIcon('anno')}
                    </th>
                    <th>Cliente</th>
                    <th>Stato</th>
                    <th>Ubicazione</th>
                    <th style={{ width: '120px' }}>Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {fascicoli.map((fascicolo) => (
                    <tr key={fascicolo.id}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          {fascicolo.parent && (
                            <span style={{ color: '#6c757d', fontSize: '0.75rem' }}>└─</span>
                          )}
                          <strong>{fascicolo.codice}</strong>
                        </div>
                      </td>
                      <td>
                        <div>{fascicolo.titolo}</div>
                        {fascicolo.titolario_voce_detail && (
                          <div style={{ fontSize: '0.75rem', color: '#6c757d' }}>
                            {fascicolo.titolario_voce_detail.codice} - {fascicolo.titolario_voce_detail.titolo}
                          </div>
                        )}
                      </td>
                      <td>{fascicolo.anno}</td>
                      <td>{fascicolo.cliente_display || '-'}</td>
                      <td>
                        <span className={`badge ${getStatoBadgeClass(fascicolo.stato)}`}>
                          {fascicolo.stato_display}
                        </span>
                      </td>
                      <td>{fascicolo.ubicazione_full_path || '-'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button
                            onClick={() => navigate(`/fascicoli/${fascicolo.id}`)}
                            className="btn-icon"
                            title="Visualizza"
                          >
                            <VisibilityIcon size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete(fascicolo.id)}
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

                <span style={{ padding: '0 1rem' }}>
                  Pagina {currentPage} di {totalPages}
                </span>

                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="btn-secondary"
                >
                  Successivo →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
