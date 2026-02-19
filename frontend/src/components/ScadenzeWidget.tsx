import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { CalendarIcon } from './icons/Icons';

interface ScadenzaOccorrenza {
  id: number;
  scadenza: {
    id: number;
    titolo: string;
    priorita: 'critical' | 'high' | 'medium' | 'low';
  };
  inizio: string;
  giornaliera: boolean;
  num_alerts: number;
}

export function ScadenzeWidget() {
  // Usa React Query per evitare richieste duplicate
  const { data, isLoading: loading } = useQuery({
    queryKey: ['scadenze-widget'],
    queryFn: async () => {
      const oggi = new Date();
      const settimana = new Date(oggi.getTime() + 7 * 24 * 60 * 60 * 1000);
      
      const response = await apiClient.get('/scadenze/occorrenze/', {
        params: {
          inizio__gte: oggi.toISOString().split('T')[0],
          inizio__lt: settimana.toISOString().split('T')[0],
          stato__in: 'pending,scheduled',
          ordering: 'inizio',
          page_size: 5
        }
      });

      // Calcola statistiche
      const occorrenze = response.data.results || [];
      
      const oggi_end = new Date(oggi);
      oggi_end.setHours(23, 59, 59);
      
      const oggi_count = occorrenze.filter((occ: ScadenzaOccorrenza) => 
        new Date(occ.inizio) <= oggi_end
      ).length;

      const critiche_count = occorrenze.filter((occ: ScadenzaOccorrenza) => 
        occ.scadenza.priorita === 'critical'
      ).length;

      return {
        oggi_count,
        settimana_count: occorrenze.length,
        critiche_count,
        alert_pendenti_count: occorrenze.reduce((sum: number, occ: ScadenzaOccorrenza) => 
          sum + (occ.num_alerts || 0), 0
        ),
        occorrenze: occorrenze.slice(0, 5)
      };
    },
    staleTime: 2 * 60 * 1000, // 2 minuti
    gcTime: 5 * 60 * 1000, // 5 minuti
  });

  const getPriorityBadge = (priorita: string) => {
    const badges = {
      critical: { emoji: '🔴', bg: '#dc2626' },
      high: { emoji: '🟠', bg: '#f59e0b' },
      medium: { emoji: '🔵', bg: '#3b82f6' },
      low: { emoji: '⚪', bg: '#6b7280' }
    };
    return badges[priorita as keyof typeof badges] || badges.low;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="card">
        <h2 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CalendarIcon size={20} />
          📅 Scadenze
        </h2>
        <div style={{ textAlign: 'center', padding: '2rem', color: '#9ca3af' }}>
          Caricamento...
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="card">
      <h2 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <CalendarIcon size={20} />
        📅 Scadenze
      </h2>

      {/* Statistiche */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        borderRadius: '8px',
        padding: '15px',
        marginBottom: '15px'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '10px',
          fontSize: '13px'
        }}>
          <div>
            <div style={{ opacity: 0.9 }}>Oggi</div>
            <div style={{ fontSize: '24px', fontWeight: 700 }}>{data.oggi_count}</div>
          </div>
          <div>
            <div style={{ opacity: 0.9 }}>7 giorni</div>
            <div style={{ fontSize: '24px', fontWeight: 700 }}>{data.settimana_count}</div>
          </div>
          <div>
            <div style={{ opacity: 0.9 }}>🔴 Critiche</div>
            <div style={{ fontSize: '20px', fontWeight: 700 }}>{data.critiche_count}</div>
          </div>
          <div>
            <div style={{ opacity: 0.9 }}>⏰ Alert</div>
            <div style={{ fontSize: '20px', fontWeight: 700 }}>{data.alert_pendenti_count}</div>
          </div>
        </div>
      </div>

      {/* Lista occorrenze */}
      {data.occorrenze && data.occorrenze.length > 0 ? (
        <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
          {data.occorrenze.map((occ: ScadenzaOccorrenza) => {
            const badge = getPriorityBadge(occ.scadenza?.priorita || 'low');
            return (
              <li key={occ.id} style={{
                padding: '10px 0',
                borderBottom: '1px solid #f3f4f6'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'start',
                  gap: '8px'
                }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: '11px',
                      color: '#6b7280',
                      marginBottom: '3px'
                    }}>
                      {formatDate(occ.inizio)}
                      {occ.giornaliera && ' 🗓️'}
                    </div>
                    <Link
                      to={`/scadenze/${occ.scadenza?.id || occ.id}`}
                      style={{
                        fontWeight: 600,
                        fontSize: '13px',
                        color: '#374151',
                        textDecoration: 'none'
                      }}
                    >
                      {occ.scadenza?.titolo 
                        ? (occ.scadenza.titolo.length > 40
                          ? occ.scadenza.titolo.substring(0, 40) + '...'
                          : occ.scadenza.titolo)
                        : 'Scadenza senza titolo'}
                    </Link>
                  </div>
                  <div>
                    {occ.scadenza && (occ.scadenza.priorita === 'critical' || occ.scadenza.priorita === 'high') && (
                      <span style={{
                        background: badge.bg,
                        color: 'white',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 600
                      }}>
                        {badge.emoji}
                      </span>
                    )}
                  </div>
                </div>
                {occ.num_alerts > 0 && (
                  <div style={{
                    fontSize: '10px',
                    color: '#6b7280',
                    marginTop: '4px'
                  }}>
                    ⏰ {occ.num_alerts} alert
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <p style={{
          color: '#9ca3af',
          textAlign: 'center',
          margin: '20px 0'
        }}>
          Nessuna scadenza imminente
        </p>
      )}

      {/* Azioni */}
      <div style={{
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap',
        marginTop: '15px'
      }}>
        <Link
          to="/scadenze/scadenziario"
          className="btn btn-sm btn-secondary"
          style={{ flex: 1, textAlign: 'center', textDecoration: 'none' }}
        >
          📋 Scadenziario
        </Link>
        <Link
          to="/scadenze/calendario"
          className="btn btn-sm btn-secondary"
          style={{ flex: 1, textAlign: 'center', textDecoration: 'none' }}
        >
          📅 Calendario
        </Link>
        <Link
          to="/scadenze/new"
          className="btn btn-sm btn-primary"
          style={{ width: '100%', textAlign: 'center' }}
        >
          + Nuova scadenza
        </Link>
      </div>
    </div>
  );
}
