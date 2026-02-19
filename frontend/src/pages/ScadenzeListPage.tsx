/**
 * Scadenze List Page
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { scadenzeApi } from '@/api/scadenze';
import type { ScadenzaListItem, ScadenzaFilters } from '@/types/scadenza';
import {
  AddIcon,
  DeleteIcon,
  VisibilityIcon,
  SearchIcon,
} from '@/components/icons/Icons';

export default function ScadenzeListPage() {
  const navigate = useNavigate();
  const [scadenze, setScadenze] = useState<ScadenzaListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Filtri
  const [filters, setFilters] = useState<ScadenzaFilters>({
    page: 1,
    page_size: 20,
    ordering: '-aggiornato_il',
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStato, setSelectedStato] = useState('');
  const [selectedPriorita, setSelectedPriorita] = useState('');
  const [selectedPeriodicita, setSelectedPeriodicita] = useState('');

  // Debounce per la ricerca (per lettori di codici a barre)
  const searchTimeoutRef = useRef<number | null>(null);

  const loadScadenze = useCallback(async () => {
    try {
      setLoading(true);
      const data = await scadenzeApi.list(filters);
      setScadenze(data.results);
      setTotalCount(data.count);
    } catch (err) {
      console.error('Error loading scadenze:', err);
      alert('Errore nel caricamento delle scadenze');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadScadenze();
  }, [loadScadenze]);

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
    setSearchQuery(value);
    
    // Cancella il timeout precedente se esiste
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Imposta un nuovo timeout per la ricerca (500ms di attesa)
    // Questo permette al lettore di codici a barre di completare la scansione
    searchTimeoutRef.current = window.setTimeout(() => {
      setFilters((prev) => ({
        ...prev,
        page: 1,
        search: value || undefined,
      }));
    }, 500);
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

  const handlePrioritaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedPriorita(value);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      priorita: value || undefined,
    }));
  };

  const handlePeriodicitaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedPeriodicita(value);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      periodicita: value || undefined,
    }));
  };

  const handleReset = () => {
    setSearchQuery('');
    setSelectedStato('');
    setSelectedPriorita('');
    setSelectedPeriodicita('');
    setFilters({
      page: 1,
      page_size: 20,
      ordering: '-aggiornato_il',
    });
  };

  const handleSort = (field: string) => {
    const currentOrdering = filters.ordering || '';
    let newOrdering = field;

    if (currentOrdering === field) {
      newOrdering = `-${field}`;
    } else if (currentOrdering === `-${field}`) {
      newOrdering = field;
    }

    setFilters((prev) => ({ ...prev, ordering: newOrdering }));
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Sei sicuro di voler eliminare questa scadenza?')) {
      return;
    }

    try {
      await scadenzeApi.delete(id);
      alert('Scadenza eliminata con successo');
      loadScadenze();
    } catch (err) {
      console.error('Error deleting scadenza:', err);
      alert("Errore nell'eliminazione della scadenza");
    }
  };

  const handleRowClick = (id: number) => {
    navigate(`/scadenze/${id}`);
  };

  const getSortIcon = (field: string) => {
    const currentOrdering = filters.ordering || '';
    if (currentOrdering === field) return ' ▲';
    if (currentOrdering === `-${field}`) return ' ▼';
    return '';
  };

  const getStatoBadgeClass = (stato: string) => {
    switch (stato) {
      case 'bozza':
        return 'badge-secondary';
      case 'attiva':
        return 'badge-success';
      case 'completata':
        return 'badge-info';
      case 'archiviata':
        return 'badge-secondary';
      default:
        return 'badge';
    }
  };

  const getPrioritaBadgeClass = (priorita: string) => {
    switch (priorita) {
      case 'low':
        return 'badge-secondary';
      case 'medium':
        return 'badge-info';
      case 'high':
        return 'badge-warning';
      case 'critical':
        return 'badge-danger';
      default:
        return 'badge';
    }
  };

  const totalPages = Math.ceil(totalCount / (filters.page_size || 20));

  if (loading && scadenze.length === 0) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento scadenze...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Scadenze</h1>
          <p style={{ color: '#6c757d', marginTop: '0.25rem' }}>
            Gestione scadenze e occorrenze
          </p>
        </div>
        <button onClick={() => navigate('/scadenze/nuovo')} className="btn-primary">
          <AddIcon size={20} />
          Nuova Scadenza
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
                placeholder="Cerca per titolo, descrizione..."
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
              <option value="bozza">Bozza</option>
              <option value="attiva">Attiva</option>
              <option value="completata">Completata</option>
              <option value="archiviata">Archiviata</option>
            </select>
          </div>

          {/* Priorità */}
          <div className="form-group">
            <label>Priorità</label>
            <select
              value={selectedPriorita}
              onChange={handlePrioritaChange}
              className="form-control"
            >
              <option value="">Tutte le priorità</option>
              <option value="low">Bassa</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="critical">Critica</option>
            </select>
          </div>

          {/* Periodicità */}
          <div className="form-group">
            <label>Periodicità</label>
            <select
              value={selectedPeriodicita}
              onChange={handlePeriodicitaChange}
              className="form-control"
            >
              <option value="">Tutte</option>
              <option value="none">Nessuna</option>
              <option value="daily">Giornaliera</option>
              <option value="weekly">Settimanale</option>
              <option value="monthly">Mensile</option>
              <option value="yearly">Annuale</option>
              <option value="custom">Personalizzata</option>
            </select>
          </div>
        </div>

        {/* Bottone Reset */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button onClick={handleReset} className="btn-secondary">
            Reset Filtri
          </button>
        </div>
      </div>

      {/* Tabella */}
      <div className="card">
        <div style={{ marginBottom: '1rem', color: '#6c757d' }}>
          Totale: {totalCount} scadenze
        </div>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th onClick={() => handleSort('titolo')} style={{ cursor: 'pointer' }}>
                  Titolo{getSortIcon('titolo')}
                </th>
                <th onClick={() => handleSort('stato')} style={{ cursor: 'pointer' }}>
                  Stato{getSortIcon('stato')}
                </th>
                <th onClick={() => handleSort('priorita')} style={{ cursor: 'pointer' }}>
                  Priorità{getSortIcon('priorita')}
                </th>
                <th>Periodicità</th>
                <th>Assegnatari</th>
                <th>Occorrenze</th>
                <th>Prossima</th>
                <th onClick={() => handleSort('aggiornato_il')} style={{ cursor: 'pointer' }}>
                  Aggiornato{getSortIcon('aggiornato_il')}
                </th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '2rem' }}>
                    Caricamento...
                  </td>
                </tr>
              ) : scadenze.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '2rem' }}>
                    Nessuna scadenza trovata
                  </td>
                </tr>
              ) : (
                scadenze.map((scadenza) => (
                  <tr
                    key={scadenza.id}
                    onClick={() => handleRowClick(scadenza.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <span style={{ color: '#0066cc', fontWeight: '500' }}>
                        {scadenza.titolo}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getStatoBadgeClass(scadenza.stato)}`}>
                        {scadenza.stato_display}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getPrioritaBadgeClass(scadenza.priorita)}`}>
                        {scadenza.priorita_display}
                      </span>
                    </td>
                    <td>{scadenza.periodicita_display}</td>
                    <td>{scadenza.num_assegnatari}</td>
                    <td>{scadenza.num_occorrenze}</td>
                    <td>
                      {scadenza.prossima_occorrenza
                        ? new Date(scadenza.prossima_occorrenza).toLocaleDateString('it-IT')
                        : '-'}
                    </td>
                    <td>{new Date(scadenza.aggiornato_il).toLocaleDateString('it-IT')}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <div
                        style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}
                      >
                        <button
                          onClick={() => navigate(`/scadenze/${scadenza.id}`)}
                          className="btn-icon"
                          title="Visualizza"
                        >
                          <VisibilityIcon size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(scadenza.id)}
                          className="btn-icon btn-icon-danger"
                          title="Elimina"
                        >
                          <DeleteIcon size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginazione */}
        {totalPages > 1 && (
          <div className="pagination">
            <button
              onClick={() => handlePageChange(filters.page! - 1)}
              disabled={filters.page === 1}
              className="btn-secondary"
            >
              Precedente
            </button>
            <span style={{ padding: '0 1rem' }}>
              Pagina {filters.page} di {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(filters.page! + 1)}
              disabled={filters.page === totalPages}
              className="btn-secondary"
            >
              Successiva
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
