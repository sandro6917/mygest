/**
 * Tipi Documento List Page
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { documentiApi } from '@/api/documenti';
import type { DocumentiTipo } from '@/types/documento';
import { SearchIcon, VisibilityIcon, DescriptionIcon } from '@/components/icons/Icons';

export default function DocumentiTipiListPage() {
  const navigate = useNavigate();
  const [tipi, setTipi] = useState<DocumentiTipo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const loadTipi = useCallback(async () => {
    try {
      setLoading(true);
      const data = await documentiApi.listTipi();
      setTipi(data);
    } catch (err) {
      console.error('Error loading tipi documento:', err);
      alert('Errore nel caricamento dei tipi documento');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTipi();
  }, [loadTipi]);

  const tipiFiltrati = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return tipi;
    return tipi.filter(
      (tipo) => tipo.codice.toLowerCase().includes(q) || tipo.nome.toLowerCase().includes(q)
    );
  }, [tipi, searchQuery]);

  if (loading) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento tipi documento...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <DescriptionIcon size={28} />
            Tipi Documento
          </h1>
          <p style={{ color: '#6c757d', marginTop: '0.25rem' }}>
            Elenco di tutti i tipi di documento configurati (fisici e digitali)
          </p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="form-group">
          <label>Ricerca</label>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cerca per codice o nome..."
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
      </div>

      <div className="card">
        <div style={{ marginBottom: '1rem', color: '#6c757d' }}>
          Totale: {tipiFiltrati.length} tipi documento
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Codice</th>
                <th>Nome</th>
                <th>Attributi</th>
                <th>Estensioni Permesse</th>
                <th style={{ width: '80px' }}>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {tipiFiltrati.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
                    Nessun tipo documento trovato
                  </td>
                </tr>
              ) : (
                tipiFiltrati.map((tipo) => (
                  <tr
                    key={tipo.id}
                    onClick={() => navigate(`/documenti/tipi/${tipo.codice}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <Link
                        to={`/documenti/tipi/${tipo.codice}`}
                        onClick={(e) => e.stopPropagation()}
                        style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 500 }}
                      >
                        {tipo.codice}
                      </Link>
                    </td>
                    <td>{tipo.nome}</td>
                    <td>{tipo.attributi?.length || 0}</td>
                    <td>{tipo.estensioni_permesse || '-'}</td>
                    <td>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/documenti/tipi/${tipo.codice}`);
                        }}
                        className="btn-icon"
                        title="Visualizza tipo documento"
                      >
                        <VisibilityIcon size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
