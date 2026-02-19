import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';

interface Scadenza {
  id: number;
  titolo: string;
  descrizione: string;
  data_scadenza: string;
  priorita: 'low' | 'medium' | 'high' | 'critical';
  stato: string;
  categoria?: string;
  periodicita?: 'once' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'custom';
}

interface ScadenzaOccorrenza {
  id: number;
  scadenza: Scadenza;
  inizio: string;
  fine: string;
  giornaliera: boolean;
  stato: string;
  num_alerts: number;
}

const priorityColors = {
  low: { bg: '#10b981', label: 'Bassa' },
  medium: { bg: '#f59e0b', label: 'Media' },
  high: { bg: '#ef4444', label: 'Alta' },
  critical: { bg: '#dc2626', label: '🔥 Critica' }
};

const statoOptions = [
  { value: '', label: 'Tutti' },
  { value: 'pending', label: 'In attesa' },
  { value: 'in_progress', label: 'In corso' },
  { value: 'completed', label: 'Completata' },
  { value: 'cancelled', label: 'Annullata' }
];

export const ScadenziarioPage: React.FC = () => {
  const [occorrenze, setOccorrenze] = useState<ScadenzaOccorrenza[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    stato: '',
    priorita: '',
    search: '',
    data_da: '',
    data_a: ''
  });

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const params: Record<string, string | number | undefined> = {
        page_size: 100,
        ordering: 'inizio'
      };

      if (filters.stato) params.stato = filters.stato;
      if (filters.priorita) params.scadenza__priorita = filters.priorita;
      if (filters.search) params.search = filters.search;
      if (filters.data_da) params.inizio__gte = filters.data_da;
      if (filters.data_a) params.inizio__lte = filters.data_a;

      const response = await apiClient.get('/scadenze/occorrenze/', { params });
      setOccorrenze(response.data.results || []);
    } catch (error) {
      console.error('Errore nel caricamento:', error);
      setOccorrenze([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const exportPDF = () => {
    const params = new URLSearchParams();
    if (filters.stato) params.append('stato', filters.stato);
    if (filters.priorita) params.append('priorita', filters.priorita);
    if (filters.data_da) params.append('data_da', filters.data_da);
    if (filters.data_a) params.append('data_a', filters.data_a);
    
    window.open(`/scadenze/scadenziario/export/pdf/?${params.toString()}`, '_blank');
  };

  const exportExcel = () => {
    const params = new URLSearchParams();
    if (filters.stato) params.append('stato', filters.stato);
    if (filters.priorita) params.append('priorita', filters.priorita);
    if (filters.data_da) params.append('data_da', filters.data_da);
    if (filters.data_a) params.append('data_a', filters.data_a);
    
    window.open(`/scadenze/scadenziario/export/excel/?${params.toString()}`, '_blank');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <div style={{ padding: '20px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h1 style={{ margin: 0 }}>📋 Scadenziario</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={exportPDF}
            className="btn btn-secondary"
            disabled={occorrenze.length === 0}
          >
            📄 Export PDF
          </button>
          <button 
            onClick={exportExcel}
            className="btn btn-secondary"
            disabled={occorrenze.length === 0}
          >
            📊 Export Excel
          </button>
          <Link to="/scadenze/calendario" className="btn btn-primary">
            📅 Calendario
          </Link>
        </div>
      </div>

      {/* Filtri */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '15px' }}>🔍 Filtri</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '15px'
        }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 500 }}>
              Stato
            </label>
            <select
              value={filters.stato}
              onChange={(e) => setFilters({ ...filters, stato: e.target.value })}
              className="form-select"
              style={{ width: '100%' }}
            >
              {statoOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 500 }}>
              Priorità
            </label>
            <select
              value={filters.priorita}
              onChange={(e) => setFilters({ ...filters, priorita: e.target.value })}
              className="form-select"
              style={{ width: '100%' }}
            >
              <option value="">Tutte</option>
              <option value="low">Bassa</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="critical">Critica</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 500 }}>
              Data Da
            </label>
            <input
              type="date"
              value={filters.data_da}
              onChange={(e) => setFilters({ ...filters, data_da: e.target.value })}
              className="form-control"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 500 }}>
              Data A
            </label>
            <input
              type="date"
              value={filters.data_a}
              onChange={(e) => setFilters({ ...filters, data_a: e.target.value })}
              className="form-control"
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 500 }}>
              Cerca
            </label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              placeholder="Titolo scadenza..."
              className="form-control"
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <button
          onClick={() => setFilters({ stato: '', priorita: '', search: '', data_da: '', data_a: '' })}
          className="btn btn-sm btn-secondary"
          style={{ marginTop: '15px' }}
        >
          🔄 Reset Filtri
        </button>
      </div>

      {/* Risultati */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ marginTop: 0 }}>
          Risultati ({occorrenze.length})
        </h3>

        {loading ? (
          <p style={{ textAlign: 'center', color: '#6b7280', padding: '40px' }}>
            Caricamento...
          </p>
        ) : occorrenze.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#6b7280', padding: '40px' }}>
            Nessuna scadenza trovata con i filtri selezionati
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse'
            }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Data Inizio</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Data Fine</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Scadenza</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Categoria</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Periodicità</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Priorità</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Stato Occ.</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Alert</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {occorrenze.map((occ) => {
                  const priorita = occ.scadenza?.priorita || 'low';
                  const color = priorityColors[priorita];
                  
                  return (
                    <tr 
                      key={occ.id}
                      style={{
                        borderBottom: '1px solid #f3f4f6',
                        background: occ.giornaliera ? '#fef3c7' : 'transparent'
                      }}
                    >
                      <td style={{ padding: '12px' }}>
                        <div style={{ fontWeight: 600 }}>
                          {formatDate(occ.inizio)}
                        </div>
                        {occ.giornaliera && (
                          <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>
                            🗓️ Giornaliera
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '12px' }}>
                        {occ.fine ? formatDate(occ.fine) : '-'}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <Link 
                          to={`/scadenze/${occ.scadenza?.id}`}
                          style={{ 
                            fontWeight: 600, 
                            color: '#374151',
                            textDecoration: 'none'
                          }}
                        >
                          {occ.scadenza?.titolo || 'N/A'}
                        </Link>
                        {occ.scadenza?.descrizione && (
                          <div style={{ 
                            fontSize: '11px', 
                            color: '#6b7280', 
                            marginTop: '4px',
                            lineHeight: '1.4'
                          }}>
                            {occ.scadenza.descrizione.substring(0, 50)}
                            {occ.scadenza.descrizione.length > 50 ? '...' : ''}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '12px' }}>
                        {occ.scadenza?.categoria && (
                          <span style={{
                            background: '#e0e7ff',
                            color: '#3730a3',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: 500
                          }}>
                            {occ.scadenza.categoria}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '12px', fontSize: '12px' }}>
                        {occ.scadenza?.periodicita === 'once' && '⚡ Una volta'}
                        {occ.scadenza?.periodicita === 'daily' && '📅 Giornaliera'}
                        {occ.scadenza?.periodicita === 'weekly' && '📆 Settimanale'}
                        {occ.scadenza?.periodicita === 'monthly' && '📊 Mensile'}
                        {occ.scadenza?.periodicita === 'yearly' && '🗓️ Annuale'}
                        {occ.scadenza?.periodicita === 'custom' && '⚙️ Personalizzata'}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          background: color.bg,
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: 600
                        }}>
                          {color.label}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          background: occ.stato === 'completed' ? '#d1fae5' : 
                                     occ.stato === 'in_progress' ? '#dbeafe' : 
                                     occ.stato === 'cancelled' ? '#fee2e2' : '#e5e7eb',
                          color: occ.stato === 'completed' ? '#065f46' : 
                                occ.stato === 'in_progress' ? '#1e40af' :
                                occ.stato === 'cancelled' ? '#991b1b' : '#374151'
                        }}>
                          {occ.stato === 'pending' && '⏳ In attesa'}
                          {occ.stato === 'scheduled' && '📅 Programmata'}
                          {occ.stato === 'in_progress' && '🔄 In corso'}
                          {occ.stato === 'completed' && '✅ Completata'}
                          {occ.stato === 'cancelled' && '❌ Annullata'}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        {occ.num_alerts > 0 && (
                          <span style={{ 
                            color: '#dc2626', 
                            fontWeight: 600,
                            fontSize: '13px'
                          }}>
                            ⏰ {occ.num_alerts}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <Link 
                          to={`/scadenze/${occ.scadenza?.id}`}
                          className="btn btn-sm btn-primary"
                        >
                          Dettagli
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScadenziarioPage;
