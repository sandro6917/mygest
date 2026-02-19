/**
 * Pratiche List Page
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { praticheApi } from '@/api/pratiche';
import type { PraticaListItem, PraticheTipo, PraticaFilters } from '@/types/pratica';
import {
  AddIcon,
  DeleteIcon,
  VisibilityIcon,
  SearchIcon,
} from '@/components/icons/Icons';

export default function PraticheListPage() {
  const navigate = useNavigate();
  const [pratiche, setPratiche] = useState<PraticaListItem[]>([]);
  const [tipiPratica, setTipiPratica] = useState<PraticheTipo[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Filtri
  const [filters, setFilters] = useState<PraticaFilters>({
    page: 1,
    page_size: 20,
    ordering: '-data_apertura',
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTipo, setSelectedTipo] = useState('');
  const [selectedStato, setSelectedStato] = useState('');
  const [dataAperturaDa, setDataAperturaDa] = useState('');
  const [dataAperturaA, setDataAperturaA] = useState('');

  // Debounce per la ricerca (per lettori di codici a barre)
  const searchTimeoutRef = useRef<number | null>(null);

  const loadTipiPratica = useCallback(async () => {
    try {
      const data = await praticheApi.listTipi();
      setTipiPratica(data);
    } catch (err) {
      console.error('Error loading tipi pratica:', err);
    }
  }, []);

  const loadPratiche = useCallback(async () => {
    try {
      setLoading(true);
      const data = await praticheApi.list(filters);
      setPratiche(data.results);
      setTotalCount(data.count);
    } catch (err) {
      console.error('Error loading pratiche:', err);
      alert('Errore nel caricamento delle pratiche');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadTipiPratica();
  }, [loadTipiPratica]);

  useEffect(() => {
    loadPratiche();
  }, [loadPratiche]);

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
    
    // Imposta un nuovo timeout per la ricerca (300ms di attesa)
    // Questo permette al lettore di codici a barre di completare la scansione
    searchTimeoutRef.current = window.setTimeout(() => {
      setFilters((prev) => ({
        ...prev,
        page: 1,
        search: value || undefined,
      }));
    }, 300);
  };

  const handleTipoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedTipo(value);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      tipo: value ? Number(value) : undefined,
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

  const handleDataAperturaDaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setDataAperturaDa(value);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      data_apertura_da: value || undefined,
    }));
  };

  const handleDataAperturaAChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setDataAperturaA(value);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      data_apertura_a: value || undefined,
    }));
  };

  const handleReset = () => {
    setSearchQuery('');
    setSelectedTipo('');
    setSelectedStato('');
    setDataAperturaDa('');
    setDataAperturaA('');
    setFilters({
      page: 1,
      page_size: 20,
      ordering: '-data_apertura',
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
    if (!confirm('Sei sicuro di voler eliminare questa pratica?')) {
      return;
    }

    try {
      await praticheApi.delete(id);
      alert('Pratica eliminata con successo');
      loadPratiche();
    } catch (err) {
      console.error('Error deleting pratica:', err);
      alert('Errore nell\'eliminazione della pratica');
    }
  };

  const handleRowClick = (id: number) => {
    navigate(`/pratiche/${id}`);
  };

  const getSortIcon = (field: string) => {
    const currentOrdering = filters.ordering || '';
    if (currentOrdering === field) return ' ▲';
    if (currentOrdering === `-${field}`) return ' ▼';
    return '';
  };

  const getStatoBadgeClass = (stato: string) => {
    switch (stato) {
      case 'aperta':
        return 'badge-success';
      case 'lavorazione':
        return 'badge-warning';
      case 'attesa':
        return 'badge-info';
      case 'chiusa':
        return 'badge-secondary';
      default:
        return 'badge';
    }
  };

  const totalPages = Math.ceil(totalCount / (filters.page_size || 20));

  if (loading && pratiche.length === 0) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento pratiche...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Pratiche</h1>
          <p style={{ color: '#6c757d', marginTop: '0.25rem' }}>
            Gestione pratiche e procedure
          </p>
        </div>
        <button onClick={() => navigate('/pratiche/nuovo')} className="btn-primary">
          <AddIcon size={20} />
          Nuova Pratica
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
                placeholder="Cerca per codice, oggetto..."
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

          {/* Tipo Pratica */}
          <div className="form-group">
            <label>Tipo Pratica</label>
            <select
              value={selectedTipo}
              onChange={handleTipoChange}
              className="form-control"
            >
              <option value="">Tutti i tipi</option>
              {tipiPratica.map((tipo) => (
                <option key={tipo.id} value={tipo.id}>
                  {tipo.nome}
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
              <option value="aperta">Aperta</option>
              <option value="lavorazione">In lavorazione</option>
              <option value="attesa">In attesa</option>
              <option value="chiusa">Chiusa</option>
            </select>
          </div>

          {/* Data Apertura Da */}
          <div className="form-group">
            <label>Data Apertura Da</label>
            <input
              type="date"
              value={dataAperturaDa}
              onChange={handleDataAperturaDaChange}
              className="form-control"
            />
          </div>

          {/* Data Apertura A */}
          <div className="form-group">
            <label>Data Apertura A</label>
            <input
              type="date"
              value={dataAperturaA}
              onChange={handleDataAperturaAChange}
              className="form-control"
            />
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
          Totale: {totalCount} pratiche
        </div>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th onClick={() => handleSort('codice')} style={{ cursor: 'pointer' }}>
                  Codice{getSortIcon('codice')}
                </th>
                <th>Tipo</th>
                <th>Cliente</th>
                <th onClick={() => handleSort('oggetto')} style={{ cursor: 'pointer' }}>
                  Oggetto{getSortIcon('oggetto')}
                </th>
                <th>Stato</th>
                <th>Responsabile</th>
                <th onClick={() => handleSort('data_apertura')} style={{ cursor: 'pointer' }}>
                  Data Apertura{getSortIcon('data_apertura')}
                </th>
                <th>Data Chiusura</th>
                <th style={{ width: '100px', textAlign: 'center' }}>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {pratiche.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
                    Nessuna pratica trovata
                  </td>
                </tr>
              ) : (
                pratiche.map((pratica) => (
                  <React.Fragment key={pratica.id}>
                    <tr
                      onClick={() => handleRowClick(pratica.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td rowSpan={pratica.ultima_nota ? 2 : 1}>
                        <span style={{ color: '#0066cc', fontWeight: '500' }}>
                          {pratica.codice}
                        </span>
                        {pratica.num_note > 0 && (
                          <span
                            className="badge badge-info"
                            style={{ marginLeft: '0.5rem', fontSize: '0.75rem' }}
                            title={`${pratica.num_note} ${pratica.num_note === 1 ? 'nota' : 'note'}`}
                          >
                            📝 {pratica.num_note}
                          </span>
                        )}
                      </td>
                      <td>{pratica.tipo_detail.nome}</td>
                      <td>{pratica.cliente_detail.anagrafica_display}</td>
                      <td>{pratica.oggetto}</td>
                      <td>
                        <span className={`badge ${getStatoBadgeClass(pratica.stato)}`}>
                          {pratica.stato_display}
                        </span>
                      </td>
                      <td>{pratica.responsabile_nome || '-'}</td>
                      <td>{new Date(pratica.data_apertura).toLocaleDateString('it-IT')}</td>
                      <td>
                        {pratica.data_chiusura
                          ? new Date(pratica.data_chiusura).toLocaleDateString('it-IT')
                          : '-'}
                      </td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <button
                            onClick={() => navigate(`/pratiche/${pratica.id}`)}
                            className="btn-icon"
                            title="Visualizza"
                          >
                            <VisibilityIcon size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete(pratica.id)}
                            className="btn-icon btn-icon-danger"
                            title="Elimina"
                          >
                            <DeleteIcon size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                    {/* Riga per ultima nota */}
                    {pratica.ultima_nota && (
                      <tr
                        key={`${pratica.id}-nota`}
                        onClick={() => handleRowClick(pratica.id)}
                        style={{ 
                          cursor: 'pointer',
                          backgroundColor: '#f9fafb'
                        }}
                      >
                        <td 
                          colSpan={8} 
                          style={{ 
                            fontSize: '0.8rem', 
                            color: '#6b7280', 
                            fontStyle: 'italic',
                            padding: '0.5rem 1rem',
                            borderTop: 'none'
                          }}
                        >
                          💬 <strong>Ultima nota:</strong> {pratica.ultima_nota}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
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
            <span>
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
