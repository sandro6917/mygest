/**
 * Pagina Lista Comunicazioni
 * Visualizza tutte le comunicazioni con filtri e paginazione
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { comunicazioniApi } from '@/api/comunicazioni';
import type { ComunicazioneFilters } from '@/types/comunicazioni';
import {
  TIPO_COMUNICAZIONE_CHOICES,
  DIREZIONE_CHOICES,
  STATO_CHOICES,
} from '@/types/comunicazioni';
import '@/styles/comunicazioni.css';

const ComunicazioniListPage = () => {
  const navigate = useNavigate();

  // Filtri e paginazione
  const [filters, setFilters] = useState<ComunicazioneFilters>({
    page: 1,
    page_size: 25,
    ordering: '-data_creazione',
  });

  // Query per lista comunicazioni
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['comunicazioni', filters],
    queryFn: () => comunicazioniApi.list(filters),
    refetchOnWindowFocus: true, // Ricarica quando la finestra torna in focus
    staleTime: 30 * 1000, // Considera i dati stale dopo 30 secondi
  });

  // Debug logging
  console.log('📊 ComunicazioniListPage - State:', {
    isLoading,
    error,
    hasData: !!data,
    count: data?.count,
    resultsLength: data?.results?.length,
    filters,
    dataKeys: data ? Object.keys(data) : [],
    fullData: data
  });

  // Handler cambio filtri
  const handleFilterChange = (field: keyof ComunicazioneFilters, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value || undefined,
      page: 1,
    }));
  };

  // Handler cambio pagina
  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({
      ...prev,
      page: newPage,
    }));
  };

  // Reset filtri
  const handleResetFilters = () => {
    setFilters({
      page: 1,
      page_size: 25,
      ordering: '-data_creazione',
    });
  };

  // Badge per stato
  const getStatoBadge = (stato: string) => {
    const badges: Record<string, { label: string; className: string }> = {
      inviata: { label: 'Inviata', className: 'badge-success' },
      errore: { label: 'Errore', className: 'badge-error' },
      bozza: { label: 'Bozza', className: 'badge-default' },
    };
    const badge = badges[stato] || badges.bozza;
    return <span className={`badge ${badge.className}`}>{badge.label}</span>;
  };

  // Formatta data
  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const totalPages = Math.ceil((data?.count || 0) / (filters.page_size || 25));
  const currentPage = filters.page || 1;

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <h1>Comunicazioni</h1>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/comunicazioni/create')}
        >
          ➕ Nuova Comunicazione
        </button>
      </div>

      {/* Filtri */}
      <div className="card mb-3">
        <div className="card-header">
          <h3>Filtri</h3>
        </div>
        <div className="card-body">
          <div className="filter-grid">
            <div className="form-group">
              <label>Cerca</label>
              <input
                type="text"
                className="form-control"
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Oggetto, corpo, mittente..."
              />
            </div>

            <div className="form-group">
              <label>Tipo</label>
              <select
                className="form-control"
                value={filters.tipo || ''}
                onChange={(e) => handleFilterChange('tipo', e.target.value)}
              >
                <option value="">Tutti</option>
                {TIPO_COMUNICAZIONE_CHOICES.map((choice) => (
                  <option key={choice.value} value={choice.value}>
                    {choice.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Direzione</label>
              <select
                className="form-control"
                value={filters.direzione || ''}
                onChange={(e) => handleFilterChange('direzione', e.target.value)}
              >
                <option value="">Tutte</option>
                {DIREZIONE_CHOICES.map((choice) => (
                  <option key={choice.value} value={choice.value}>
                    {choice.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Stato</label>
              <select
                className="form-control"
                value={filters.stato || ''}
                onChange={(e) => handleFilterChange('stato', e.target.value)}
              >
                <option value="">Tutti</option>
                {STATO_CHOICES.map((choice) => (
                  <option key={choice.value} value={choice.value}>
                    {choice.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group filter-actions">
              <button className="btn btn-secondary" onClick={handleResetFilters}>
                Reset
              </button>
              <button className="btn btn-primary" onClick={() => refetch()}>
                Applica
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabella */}
      <div className="card">
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Tipo</th>
                <th>Oggetto</th>
                <th>Direzione</th>
                <th>Destinatari</th>
                <th>Stato</th>
                <th>Data Creazione</th>
                <th>Data Invio</th>
                <th>Protocollo</th>
                <th className="text-right">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={10} className="text-center">
                    Caricamento...
                  </td>
                </tr>
              )}
              {!isLoading && data?.results && data.results.length === 0 && (
                <tr>
                  <td colSpan={10} className="text-center">
                    Nessuna comunicazione trovata
                  </td>
                </tr>
              )}
              {data?.results && data.results.map((comunicazione) => (
                <tr key={comunicazione.id}>
                  <td>{comunicazione.id}</td>
                  <td>
                    {TIPO_COMUNICAZIONE_CHOICES.find((c) => c.value === comunicazione.tipo)?.label}
                  </td>
                  <td>
                    <span className="text-truncate" title={comunicazione.oggetto}>
                      {comunicazione.oggetto}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        comunicazione.direzione === 'IN' ? 'badge-info' : 'badge-primary'
                      }`}
                    >
                      {DIREZIONE_CHOICES.find((c) => c.value === comunicazione.direzione)?.label}
                    </span>
                  </td>
                  <td>
                    {comunicazione.destinatari_con_anagrafica && comunicazione.destinatari_con_anagrafica.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        {comunicazione.destinatari_con_anagrafica.slice(0, 3).map((dest, idx) => (
                          <div key={idx} style={{ fontSize: '0.875rem' }}>
                            {dest.codice_anagrafica && (
                              <strong style={{ color: '#2563eb', marginRight: '0.5rem' }}>
                                [{dest.codice_anagrafica}]
                              </strong>
                            )}
                            <span style={{ color: '#64748b' }}>{dest.email}</span>
                          </div>
                        ))}
                        {comunicazione.destinatari_con_anagrafica.length > 3 && (
                          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                            +{comunicazione.destinatari_con_anagrafica.length - 3} altri
                          </span>
                        )}
                      </div>
                    ) : (
                      <span title={comunicazione.destinatari_calcolati.join(', ')}>
                        {comunicazione.destinatari_calcolati.length} destinatari
                      </span>
                    )}
                  </td>
                  <td>{getStatoBadge(comunicazione.stato)}</td>
                  <td>{formatDate(comunicazione.data_creazione)}</td>
                  <td>{formatDate(comunicazione.data_invio)}</td>
                  <td>
                    {comunicazione.protocollo_label && (
                      <span className="badge badge-secondary">{comunicazione.protocollo_label}</span>
                    )}
                  </td>
                  <td className="text-right">
                    <div className="btn-group">
                      <button
                        className="btn btn-sm btn-info"
                        onClick={() => navigate(`/comunicazioni/${comunicazione.id}`)}
                        title="Visualizza"
                      >
                        👁️
                      </button>
                      {comunicazione.stato === 'bozza' && (
                        <>
                          <button
                            className="btn btn-sm btn-warning"
                            onClick={() => navigate(`/comunicazioni/${comunicazione.id}/modifica`)}
                            title="Modifica"
                          >
                            ✏️
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Paginazione */}
        {data && data.count > 0 && (
          <div className="pagination-container">
            <div className="pagination-info">
              Righe {((currentPage - 1) * (filters.page_size || 25)) + 1} -{' '}
              {Math.min(currentPage * (filters.page_size || 25), data.count)} di {data.count}
            </div>
            <div className="pagination-controls">
              <button
                className="btn btn-sm btn-secondary"
                disabled={currentPage === 1}
                onClick={() => handlePageChange(currentPage - 1)}
              >
                ← Precedente
              </button>
              <span className="pagination-current">
                Pagina {currentPage} di {totalPages}
              </span>
              <button
                className="btn btn-sm btn-secondary"
                disabled={currentPage >= totalPages}
                onClick={() => handlePageChange(currentPage + 1)}
              >
                Successiva →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComunicazioniListPage;

