/**
 * Pagina lista movimenti di protocollo
 * Con filtri e azione stampa registro
 */
import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getMovimentiProtocollo } from '@/api/protocolloApi';
import type { MovimentoProtocollo } from '@/types/protocollo';
import { VisibilityIcon, PrintIcon } from '@/components/icons/Icons';

export function MovimentoProtocolloListPage() {
  const navigate = useNavigate();
  const [movimenti, setMovimenti] = useState<MovimentoProtocollo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filtri
  const [filtroCliente, setFiltroCliente] = useState<string>('');
  const [filtroDirezione, setFiltroDirezione] = useState<string>('');
  const [filtroAnno, setFiltroAnno] = useState<string>('');
  const [filtroChiuso, setFiltroChiuso] = useState<string>('');
  const [filtroDataDa, setFiltroDataDa] = useState<string>('');
  const [filtroDataA, setFiltroDataA] = useState<string>('');
  
  // Paginazione
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const pageSize = 20;

  // Movimenti selezionati per la stampa
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const loadMovimenti = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = {};
      
      if (filtroCliente) params.cliente = parseInt(filtroCliente);
      if (filtroDirezione) params.direzione = filtroDirezione;
      if (filtroAnno) params.anno = parseInt(filtroAnno);
      if (filtroChiuso) params.chiuso = filtroChiuso === 'true';
      
      const data = await getMovimentiProtocollo(params);
      
      // Applica filtro data range sul client (se l'API non lo supporta)
      let filtered = data;
      if (filtroDataDa) {
        filtered = filtered.filter(m => new Date(m.data) >= new Date(filtroDataDa));
      }
      if (filtroDataA) {
        filtered = filtered.filter(m => new Date(m.data) <= new Date(filtroDataA));
      }
      
      setMovimenti(filtered);
      setTotalCount(filtered.length);
      setTotalPages(Math.ceil(filtered.length / pageSize));
    } catch (error) {
      console.error('Errore caricamento movimenti:', error);
      setError('Errore nel caricamento dei movimenti di protocollo');
    } finally {
      setLoading(false);
    }
  }, [filtroCliente, filtroDirezione, filtroAnno, filtroChiuso, filtroDataDa, filtroDataA]);

  useEffect(() => {
    void loadMovimenti();
  }, [loadMovimenti]);

  const handleResetFiltri = () => {
    setFiltroCliente('');
    setFiltroDirezione('');
    setFiltroAnno('');
    setFiltroChiuso('');
    setFiltroDataDa('');
    setFiltroDataA('');
    setCurrentPage(1);
  };

  const handleToggleSelect = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedIds.size === movimenti.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(movimenti.map(m => m.id)));
    }
  };

  const handleStampaRegistro = async () => {
    if (selectedIds.size === 0) {
      alert('Seleziona almeno un movimento da stampare');
      return;
    }

    try {
      // Costruisci i parametri per la stampa
      const params = new URLSearchParams();
      selectedIds.forEach(id => params.append('movimento_ids', id.toString()));
      if (filtroDataDa) params.append('data_da', filtroDataDa);
      if (filtroDataA) params.append('data_a', filtroDataA);

      // Fetch del PDF tramite API (con JWT token negli headers)
      const response = await fetch(`/etichette/stampa/REG_PROTOCOLLO/?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Errore nel caricamento del PDF');
      }

      // Converti la risposta in blob
      const blob = await response.blob();
      
      // Crea un URL temporaneo per il blob
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Apri in una nuova finestra
      window.open(blobUrl, '_blank');
      
      // Libera la memoria dopo un po'
      setTimeout(() => window.URL.revokeObjectURL(blobUrl), 100);
    } catch (error) {
      console.error('Errore stampa registro:', error);
      alert('Errore durante la stampa del registro');
    }
  };

  const getStatoBadge = (chiuso: boolean, direzione: string) => {
    if (chiuso || direzione === 'IN') {
      return <span className="badge badge-success">Chiuso</span>;
    }
    return <span className="badge badge-warning">Aperto</span>;
  };

  const getDirezioneBadge = (direzione: string) => {
    if (direzione === 'IN') {
      return <span className="badge badge-success">ENTRATA</span>;
    }
    return <span className="badge badge-warning">USCITA</span>;
  };

  // Calcola movimenti da mostrare nella pagina corrente
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const movimentiPaginati = movimenti.slice(startIndex, endIndex);

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            📋 Registro Protocollo
          </h1>
          <p className="text-muted">Movimenti di protocollazione ({totalCount} totali)</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleStampaRegistro}
            className="btn-primary"
            disabled={selectedIds.size === 0}
            title={selectedIds.size === 0 ? 'Seleziona almeno un movimento' : `Stampa ${selectedIds.size} movimenti selezionati`}
          >
            <PrintIcon size={18} />
            <span>Stampa Registro ({selectedIds.size})</span>
          </button>
        </div>
      </div>

      {/* Filtri */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {/* Cliente */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Cliente ID</label>
              <input
                type="number"
                className="form-control"
                value={filtroCliente}
                onChange={(e) => setFiltroCliente(e.target.value)}
                placeholder="ID cliente..."
              />
            </div>

            {/* Direzione */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Direzione</label>
              <select
                className="form-control"
                value={filtroDirezione}
                onChange={(e) => setFiltroDirezione(e.target.value)}
              >
                <option value="">Tutte</option>
                <option value="IN">Entrata (IN)</option>
                <option value="OUT">Uscita (OUT)</option>
              </select>
            </div>

            {/* Anno */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Anno</label>
              <input
                type="number"
                className="form-control"
                value={filtroAnno}
                onChange={(e) => setFiltroAnno(e.target.value)}
                placeholder="2026"
              />
            </div>

            {/* Stato */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Stato</label>
              <select
                className="form-control"
                value={filtroChiuso}
                onChange={(e) => setFiltroChiuso(e.target.value)}
              >
                <option value="">Tutti</option>
                <option value="true">Chiusi</option>
                <option value="false">Aperti</option>
              </select>
            </div>

            {/* Data Da */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Data Da</label>
              <input
                type="date"
                className="form-control"
                value={filtroDataDa}
                onChange={(e) => setFiltroDataDa(e.target.value)}
              />
            </div>

            {/* Data A */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Data A</label>
              <input
                type="date"
                className="form-control"
                value={filtroDataA}
                onChange={(e) => setFiltroDataA(e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button onClick={handleResetFiltri} className="btn-secondary">
              Reset Filtri
            </button>
          </div>
        </div>
      </div>

      {/* Errore */}
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center" style={{ padding: '2rem' }}>
          <div className="spinner">Caricamento...</div>
        </div>
      )}

      {/* Tabella */}
      {!loading && !error && (
        <div className="card">
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>
                    <input
                      type="checkbox"
                      checked={selectedIds.size === movimenti.length && movimenti.length > 0}
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th>Data</th>
                  <th>Protocollo</th>
                  <th>Direzione</th>
                  <th>Cliente</th>
                  <th>Oggetto</th>
                  <th>Destinatario</th>
                  <th>Ubicazione</th>
                  <th>Stato</th>
                  <th style={{ width: '100px' }}>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {movimentiPaginati.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="text-center" style={{ padding: '2rem' }}>
                      Nessun movimento trovato
                    </td>
                  </tr>
                ) : (
                  movimentiPaginati.map((movimento) => (
                    <tr key={movimento.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(movimento.id)}
                          onChange={() => handleToggleSelect(movimento.id)}
                        />
                      </td>
                      <td>
                        {new Date(movimento.data).toLocaleString('it-IT', {
                          year: 'numeric',
                          month: '2-digit',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td>
                        <strong>{movimento.protocollo_label}</strong>
                      </td>
                      <td>{getDirezioneBadge(movimento.direzione)}</td>
                      <td>{movimento.cliente_display || `#${movimento.cliente}`}</td>
                      <td>
                        {movimento.documento_display && (
                          <Link to={`/documenti/${movimento.documento}`}>
                            📄 {movimento.documento_display}
                          </Link>
                        )}
                        {movimento.fascicolo_display && (
                          <Link to={`/fascicoli/${movimento.fascicolo}`}>
                            📁 {movimento.fascicolo_display}
                          </Link>
                        )}
                        {!movimento.documento_display && !movimento.fascicolo_display && (
                          <span className="text-muted">{movimento.target_label || 'N/A'}</span>
                        )}
                      </td>
                      <td>
                        {movimento.destinatario_anagrafica_display || movimento.destinatario || '-'}
                      </td>
                      <td>
                        <small className="text-muted">
                          {movimento.ubicazione_full_path || '-'}
                        </small>
                      </td>
                      <td>{getStatoBadge(movimento.chiuso, movimento.direzione)}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.25rem' }}>
                          <button
                            onClick={() => navigate(`/protocollo/movimenti/${movimento.id}`)}
                            className="btn-icon"
                            title="Visualizza dettagli"
                          >
                            <VisibilityIcon size={18} />
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
            <div className="card-footer">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  Pagina {currentPage} di {totalPages} ({totalCount} totali)
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => setCurrentPage(1)}
                    disabled={currentPage === 1}
                    className="btn-secondary"
                  >
                    ««
                  </button>
                  <button
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="btn-secondary"
                  >
                    «
                  </button>
                  <button
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="btn-secondary"
                  >
                    »
                  </button>
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    disabled={currentPage === totalPages}
                    className="btn-secondary"
                  >
                    »»
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MovimentoProtocolloListPage;
