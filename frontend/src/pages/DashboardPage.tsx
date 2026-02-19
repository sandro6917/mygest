import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { apiClient } from '../api/client';
import { ScadenzeWidget } from '../components/ScadenzeWidget';
import { 
  DashboardIcon, 
  DocumentiIcon, 
  CalendarIcon, 
  ClientIcon,
  InfoIcon,
  RefreshIcon,
  PraticheIcon
} from '../components/icons/Icons';

interface DashboardStats {
  pratiche_attive: number;
  pratiche_chiuse: number;
  documenti_count: number;
  scadenze_oggi: number;
  clienti_attivi: number;
  pratiche_per_mese: Array<{ mese: string; count: number }>;
}

export function DashboardPage() {
  const getErrorMessage = (err: unknown): string => {
    if (isAxiosError(err)) {
      return err.response?.data?.detail || err.message || 'Errore nel caricamento dei dati';
    }
    if (err instanceof Error) {
      return err.message;
    }
    return 'Errore nel caricamento dei dati';
  };

  // Usa React Query per gestire il fetch con caching automatico
  const { data: stats, isLoading: loading, error: queryError, refetch: loadStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await apiClient.get<DashboardStats>('/dashboard/stats/');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minuti
    gcTime: 10 * 60 * 1000, // 10 minuti
  });

  const error = queryError ? getErrorMessage(queryError) : null;

  if (loading) {
    return (
      <div className="page-container">
        <div className="page-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <DashboardIcon size={28} />
            <div>
              <h1 style={{ margin: 0 }}>Dashboard</h1>
              <p className="text-muted" style={{ margin: '0.25rem 0 0' }}>Panoramica del sistema</p>
            </div>
          </div>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <RefreshIcon size={32} />
          <p className="text-muted" style={{ marginTop: '1rem' }}>Caricamento dati...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="page-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <DashboardIcon size={28} />
            <div>
              <h1 style={{ margin: 0 }}>Dashboard</h1>
              <p className="text-muted" style={{ margin: '0.25rem 0 0' }}>Panoramica del sistema</p>
            </div>
          </div>
          <button onClick={() => loadStats()} className="btn btn-primary">
            <RefreshIcon size={16} />
            <span>Ricarica</span>
          </button>
        </div>
        <div className="card" style={{ margin: '1rem 0' }}>
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <InfoIcon size={32} />
            <p className="text-danger" style={{ marginTop: '1rem' }}>{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <DashboardIcon size={28} />
          <div>
            <h1 style={{ margin: 0 }}>Dashboard</h1>
            <p className="text-muted" style={{ margin: '0.25rem 0 0' }}>Panoramica del sistema</p>
          </div>
        </div>
        <button onClick={() => loadStats()} className="btn btn-secondary">
          <RefreshIcon size={16} />
          <span>Aggiorna</span>
        </button>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        <Link to="/pratiche" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ 
            padding: '1.5rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            border: '2px solid transparent',
            height: '100%'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--primary-color)';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'transparent';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '';
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
              <div style={{ 
                padding: '0.75rem', 
                backgroundColor: '#e3f2fd', 
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <PraticheIcon size={24} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#666' }}>Pratiche Attive</p>
                <h2 style={{ margin: '0.5rem 0', fontSize: '2rem', fontWeight: 'bold' }}>
                  {stats?.pratiche_attive || 0}
                </h2>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#999' }}>
                  {stats?.pratiche_chiuse || 0} chiuse
                </p>
              </div>
            </div>
          </div>
        </Link>

        <Link to="/documenti" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ 
            padding: '1.5rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            border: '2px solid transparent',
            height: '100%'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--primary-color)';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'transparent';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '';
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
              <div style={{ 
                padding: '0.75rem', 
                backgroundColor: '#f3e5f5', 
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <DocumentiIcon size={24} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#666' }}>Documenti</p>
                <h2 style={{ margin: '0.5rem 0', fontSize: '2rem', fontWeight: 'bold' }}>
                  {stats?.documenti_count || 0}
                </h2>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#999' }}>
                  Totale archivio
                </p>
              </div>
            </div>
          </div>
        </Link>

        <Link to="/scadenze" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ 
            padding: '1.5rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            border: '2px solid transparent',
            height: '100%'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--primary-color)';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'transparent';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '';
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
              <div style={{ 
                padding: '0.75rem', 
                backgroundColor: '#fff3e0', 
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <CalendarIcon size={24} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#666' }}>Scadenze Attive</p>
                <h2 style={{ margin: '0.5rem 0', fontSize: '2rem', fontWeight: 'bold' }}>
                  {stats?.scadenze_oggi || 0}
                </h2>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#999' }}>
                  In corso
                </p>
              </div>
            </div>
          </div>
        </Link>

        <Link to="/anagrafiche" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ 
            padding: '1.5rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            border: '2px solid transparent',
            height: '100%'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--primary-color)';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'transparent';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '';
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
              <div style={{ 
                padding: '0.75rem', 
                backgroundColor: '#e8f5e9', 
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <ClientIcon size={24} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#666' }}>Clienti Attivi</p>
                <h2 style={{ margin: '0.5rem 0', fontSize: '2rem', fontWeight: 'bold' }}>
                  {stats?.clienti_attivi || 0}
                </h2>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#999' }}>
                  Ultimi 6 mesi
                </p>
              </div>
            </div>
          </div>
        </Link>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
        <div className="card">
          <div className="card-header">
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
              <PraticheIcon size={20} />
              Pratiche per Mese
            </h2>
          </div>
          <div style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1rem', height: '250px' }}>
              {stats?.pratiche_per_mese.map((item) => {
                const maxCount = Math.max(...(stats?.pratiche_per_mese.map(p => p.count) || [1]));
                const heightPercent = item.count > 0 ? (item.count / maxCount) * 100 : 0;
                
                return (
                  <div 
                    key={item.mese} 
                    style={{ 
                      flex: 1, 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}
                  >
                    <div style={{ 
                      width: '100%', 
                      height: '200px', 
                      display: 'flex', 
                      alignItems: 'flex-end',
                      justifyContent: 'center'
                    }}>
                      <div
                        style={{
                          width: '80%',
                          height: `${heightPercent}%`,
                          backgroundColor: 'var(--primary-color)',
                          borderRadius: '4px 4px 0 0',
                          display: 'flex',
                          alignItems: 'flex-start',
                          justifyContent: 'center',
                          paddingTop: '0.5rem',
                          fontWeight: 'bold',
                          color: 'white',
                          transition: 'all 0.3s ease',
                          cursor: 'pointer',
                          minHeight: item.count > 0 ? '30px' : '0'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--primary-hover)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--primary-color)';
                        }}
                      >
                        {item.count > 0 && item.count}
                      </div>
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: '500', color: '#666' }}>
                      {item.mese}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Widget Scadenze Potenziato */}
        <ScadenzeWidget />
      </div>
    </div>
  );
}
