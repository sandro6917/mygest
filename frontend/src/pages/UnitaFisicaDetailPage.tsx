import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getUnitaFisica, getUnitaFisicaChildren } from '@/api/archivioFisico';
import { documentiApi } from '@/api/documenti';
import { fascicoliApi } from '@/api/fascicoli';
import { previewEtichettaPDF, previewListaContenutiPDF, previewCopertinaPDF, previewCopertinaA3PDF, previewFascicoliDocumentiPDF } from '@/api/archivio';
import type { UnitaFisicaDetail, UnitaFisica } from '@/types/archivioFisico';
import type { Documento } from '@/types/documento';
import type { FascicoloListItem } from '@/types/fascicolo';
import { AddIcon, EditIcon, DocumentiIcon } from '@/components/icons/Icons';
import './UnitaFisicaDetailPage.css';

export function UnitaFisicaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [unita, setUnita] = useState<UnitaFisicaDetail | null>(null);
  const [subunita, setSubunita] = useState<UnitaFisica[]>([]);
  const [documenti, setDocumenti] = useState<Documento[]>([]);
  const [fascicoli, setFascicoli] = useState<FascicoloListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'subunita' | 'documenti' | 'fascicoli'>('subunita');
  const [showListaMenu, setShowListaMenu] = useState(false);

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  useEffect(() => {
    // Chiudi il menu dropdown quando si clicca fuori
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.dropdown-wrapper')) {
        setShowListaMenu(false);
      }
    };

    if (showListaMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showListaMenu]);

  const loadData = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      // Carica dati unità fisica
      const unitaData = await getUnitaFisica(Number(id));
      setUnita(unitaData);

      // Carica sottounità
      const subunitaData = await getUnitaFisicaChildren(Number(id));
      setSubunita(subunitaData);

      // Carica documenti con questa ubicazione
      try {
        const documentiResponse = await documentiApi.list({ ubicazione: Number(id) }, 1, 100);
        setDocumenti(documentiResponse.results || []);
      } catch (err) {
        console.error('Error loading documenti:', err);
        setDocumenti([]);
      }

      // Carica fascicoli con questa ubicazione
      try {
        const fascicoliResponse = await fascicoliApi.list({ ubicazione: Number(id) });
        setFascicoli(fascicoliResponse.results || []);
      } catch (err) {
        console.error('Error loading fascicoli:', err);
        setFascicoli([]);
      }
    } catch (err) {
      console.error('Error loading unità fisica:', err);
      setError('Errore nel caricamento dei dati');
    } finally {
      setLoading(false);
    }
  };

  const getTypeIcon = (tipo: string) => {
    const icons: Record<string, string> = {
      ufficio: '🏢',
      stanza: '🚪',
      scaffale: '📚',
      mobile: '🗄️',
      anta: '📂',
      ripiano: '📋',
      contenitore: '📦',
      cartellina: '📁',
    };
    return icons[tipo] || '📌';
  };

  const handleSubunitaClick = (subunitaId: number) => {
    navigate(`/archivio/unita/${subunitaId}`);
  };

  const handleDocumentoClick = (documentoId: number) => {
    navigate(`/documenti/${documentoId}`);
  };

  const handleFascicoloClick = (fascicoloId: number) => {
    navigate(`/fascicoli/${fascicoloId}`);
  };

  const handleStampaEtichetta = async () => {
    if (!unita) return;
    
    try {
      // Configurazione completa dal database (StampaModulo/StampaCampo)
      await previewEtichettaPDF(unita.id);
    } catch (err) {
      console.error('Errore nella stampa dell\'etichetta:', err);
      alert('Errore durante la generazione dell\'etichetta');
    }
  };

  const handleStampaCopertina = async () => {
    if (!unita) return;
    
    try {
      // Stampa copertina A4 con codice e nome evidenziati
      await previewCopertinaPDF(unita.id);
    } catch (err) {
      console.error('Errore nella stampa della copertina:', err);
      alert('Errore durante la generazione della copertina');
    }
  };

  const handleStampaCopertinaA3 = async () => {
    if (!unita) return;
    
    try {
      // Stampa copertina A3 orizzontale
      await previewCopertinaA3PDF(unita.id);
    } catch (err) {
      console.error('Errore nella stampa della copertina A3:', err);
      alert('Errore durante la generazione della copertina A3');
    }
  };

  const handleStampaListaContenuti = async (tipoLista?: string) => {
    if (!unita) return;
    
    try {
      // Determina quale lista stampare
      let listaSlug: string | undefined;
      
      if (tipoLista === 'sottounita') {
        listaSlug = 'LST_OBJ'; // Lista sottounità (albero completo)
      } else if (tipoLista === 'subunita-dirette') {
        listaSlug = 'LST_SUBUNITA_DIRETTE'; // Lista sottounità dirette (1 livello, archivio fisso)
      } else if (tipoLista === 'fascicoli') {
        listaSlug = 'LST_FASCICOLI_UBICAZIONE'; // Lista fascicoli
      } else if (tipoLista === 'documenti') {
        listaSlug = 'LST_DOCUMENTI_UBICAZIONE'; // Lista documenti
      } else if (tipoLista === 'contenitori') {
        listaSlug = 'LST_CONTENITORI'; // Lista contenitori mobili (archivio_fisso=False)
      }
      
      await previewListaContenutiPDF(unita.id, listaSlug);
    } catch (err) {
      console.error('Errore nella stampa della lista contenuti:', err);
      alert('Errore durante la generazione della lista contenuti');
    }
  };

  if (loading) {
    return (
      <div className="unita-detail-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Caricamento...</p>
        </div>
      </div>
    );
  }

  if (error || !unita) {
    return (
      <div className="unita-detail-page">
        <div className="error-container">
          <p className="error-message">{error || 'Unità fisica non trovata'}</p>
          <button onClick={() => navigate('/archivio')} className="btn btn-primary">
            Torna all'archivio
          </button>
        </div>
      </div>
    );
  }

  const totalItems = subunita.length + documenti.length + fascicoli.length;

  return (
    <div className="unita-detail-page">
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <Link to="/archivio" className="breadcrumb-link">
          Archivio
        </Link>
        {unita.ancestors.map((ancestor) => (
          <span key={ancestor.id}>
            <span className="breadcrumb-separator">›</span>
            <Link to={`/archivio/unita/${ancestor.id}`} className="breadcrumb-link">
              {ancestor.codice}
            </Link>
          </span>
        ))}
        <span className="breadcrumb-separator">›</span>
        <span className="breadcrumb-current">{unita.codice}</span>
      </div>

      {/* Header */}
      <div className="page-header">
        <div className="header-left">
          <div className="title-row">
            <span className="unit-icon">{getTypeIcon(unita.tipo)}</span>
            <h1>{unita.nome}</h1>
            {!unita.attivo && <span className="badge badge-inactive">Non attivo</span>}
            {unita.archivio_fisso && <span className="badge badge-archivio-fisso">Archivio Fisso</span>}
          </div>
          <div className="unit-info">
            <div className="info-item">
              <span className="label">Codice:</span>
              <span className="value code">{unita.codice}</span>
            </div>
            <div className="info-item">
              <span className="label">Tipo:</span>
              <span className="value">{unita.tipo_display}</span>
            </div>
            <div className="info-item">
              <span className="label">Percorso:</span>
              <span className="value code">{unita.full_path}</span>
            </div>
          </div>
        </div>
        <div className="header-right">
          <button
            className="btn btn-secondary"
            onClick={handleStampaEtichetta}
            title="Visualizza Etichetta"
          >
            🏷️ <span>Etichetta</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleStampaCopertina}
            title="Stampa Copertina A4"
          >
            📄 <span>Copertina A4</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleStampaCopertinaA3}
            title="Stampa Copertina A3 Orizzontale"
          >
            📋 <span>Copertina A3</span>
          </button>
          <div className="dropdown-wrapper" style={{ position: 'relative', display: 'inline-block' }}>
            <button
              className="btn btn-secondary"
              onClick={() => setShowListaMenu(!showListaMenu)}
              title="Stampa Lista Contenuti"
            >
              📋 <span>Lista Contenuti</span> <span style={{ marginLeft: '4px' }}>▼</span>
            </button>
            {showListaMenu && (
              <div 
                className="dropdown-menu" 
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  marginTop: '4px',
                  backgroundColor: 'white',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                  zIndex: 1000,
                  minWidth: '200px',
                }}
              >
                <button
                  className="dropdown-item"
                  onClick={() => {
                    handleStampaListaContenuti('sottounita');
                    setShowListaMenu(false);
                  }}
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '8px 16px',
                    textAlign: 'left',
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  📁 Sottounità (Albero)
                </button>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    handleStampaListaContenuti('subunita-dirette');
                    setShowListaMenu(false);
                  }}
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '8px 16px',
                    textAlign: 'left',
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  🗂️ Archivio Fisso
                </button>
                <button
                  className="dropdown-item"
                  onClick={async () => {
                    if (unita) {
                      try {
                        await previewFascicoliDocumentiPDF(unita.id);
                      } catch (err) {
                        console.error('Errore nella stampa fascicoli e documenti:', err);
                        alert('Errore durante la generazione del PDF');
                      }
                    }
                    setShowListaMenu(false);
                  }}
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '8px 16px',
                    textAlign: 'left',
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  📋 Fascicoli e Documenti
                </button>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    handleStampaListaContenuti('contenitori');
                    setShowListaMenu(false);
                  }}
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '8px 16px',
                    textAlign: 'left',
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  📦 Contenitori
                </button>
              </div>
            )}
          </div>
          <button
            className="btn btn-secondary"
            onClick={() => navigate(`/archivio/unita/${unita.id}/modifica`)}
          >
            <EditIcon size={18} />
            <span>Modifica</span>
          </button>
          <button
            className="btn btn-primary"
            onClick={() => navigate(`/archivio/unita/nuovo?parent=${unita.id}`)}
          >
            <AddIcon size={18} />
            <span>Aggiungi Sottounità</span>
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-cards">
        <div className="stat-card" onClick={() => setActiveTab('subunita')}>
          <div className="stat-value">{subunita.length}</div>
          <div className="stat-label">Sottounità</div>
        </div>
        <div className="stat-card" onClick={() => setActiveTab('fascicoli')}>
          <div className="stat-value">{fascicoli.length}</div>
          <div className="stat-label">Fascicoli</div>
        </div>
        <div className="stat-card" onClick={() => setActiveTab('documenti')}>
          <div className="stat-value">{documenti.length}</div>
          <div className="stat-label">Documenti</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalItems}</div>
          <div className="stat-label">Totale Elementi</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'subunita' ? 'active' : ''}`}
            onClick={() => setActiveTab('subunita')}
          >
            Sottounità ({subunita.length})
          </button>
          <button
            className={`tab ${activeTab === 'fascicoli' ? 'active' : ''}`}
            onClick={() => setActiveTab('fascicoli')}
          >
            Fascicoli ({fascicoli.length})
          </button>
          <button
            className={`tab ${activeTab === 'documenti' ? 'active' : ''}`}
            onClick={() => setActiveTab('documenti')}
          >
            Documenti ({documenti.length})
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {/* Sottounità Tab */}
          {activeTab === 'subunita' && (
            <div className="subunita-list">
              {subunita.length === 0 ? (
                <div className="empty-state">
                  <p>Nessuna sottounità presente</p>
                  <button
                    className="btn btn-primary"
                    onClick={() => navigate(`/archivio/unita/nuovo?parent=${unita.id}`)}
                  >
                    <AddIcon size={18} />
                    <span>Aggiungi prima sottounità</span>
                  </button>
                </div>
              ) : (
                <div className="items-grid">
                  {subunita.map((sub) => (
                    <div
                      key={sub.id}
                      className="item-card subunita-card"
                      onClick={() => handleSubunitaClick(sub.id)}
                    >
                      <div className="card-icon">{getTypeIcon(sub.tipo)}</div>
                      <div className="card-content">
                        <div className="card-title">
                          <span className="card-code">{sub.codice}</span>
                          <span className="card-name">{sub.nome}</span>
                        </div>
                        <div className="card-meta">
                          <span className="card-type">{sub.tipo_display}</span>
                          {sub.archivio_fisso && (
                            <span className="badge badge-sm badge-archivio-fisso">Fisso</span>
                          )}
                          {!sub.attivo && (
                            <span className="badge badge-sm badge-inactive">Inattivo</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Fascicoli Tab */}
          {activeTab === 'fascicoli' && (
            <div className="fascicoli-list">
              {fascicoli.length === 0 ? (
                <div className="empty-state">
                  <p>Nessun fascicolo archiviato in questa unità</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Codice</th>
                        <th>Titolo</th>
                        <th>Anno</th>
                        <th>Cliente</th>
                        <th>Stato</th>
                        <th>Azioni</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fascicoli.map((fascicolo) => (
                        <tr key={fascicolo.id} onClick={() => handleFascicoloClick(fascicolo.id)}>
                          <td className="code-cell">{fascicolo.codice}</td>
                          <td className="title-cell">{fascicolo.titolo}</td>
                          <td>{fascicolo.anno}</td>
                          <td>{fascicolo.cliente_display}</td>
                          <td>
                            <span className={`status-badge status-${fascicolo.stato}`}>
                              {fascicolo.stato}
                            </span>
                          </td>
                          <td>
                            <button
                              className="btn-icon"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleFascicoloClick(fascicolo.id);
                              }}
                              title="Vedi dettagli"
                            >
                              <DocumentiIcon size={18} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Documenti Tab */}
          {activeTab === 'documenti' && (
            <div className="documenti-list">
              {documenti.length === 0 ? (
                <div className="empty-state">
                  <p>Nessun documento archiviato in questa unità</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Codice</th>
                        <th>Descrizione</th>
                        <th>Tipo</th>
                        <th>Cliente</th>
                        <th>Data</th>
                        <th>Stato</th>
                        <th>Azioni</th>
                      </tr>
                    </thead>
                    <tbody>
                      {documenti.map((documento) => (
                        <tr key={documento.id} onClick={() => handleDocumentoClick(documento.id)}>
                          <td className="code-cell">{documento.codice}</td>
                          <td className="title-cell">{documento.descrizione}</td>
                          <td>{documento.tipo_detail?.nome}</td>
                          <td>{documento.cliente_detail?.anagrafica_display}</td>
                          <td>{new Date(documento.data_documento).toLocaleDateString()}</td>
                          <td>
                            <span className={`status-badge status-${documento.stato}`}>
                              {documento.stato}
                            </span>
                          </td>
                          <td>
                            <button
                              className="btn-icon"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDocumentoClick(documento.id);
                              }}
                              title="Vedi dettagli"
                            >
                              <DocumentiIcon size={18} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Note Section */}
      {unita.note && (
        <div className="notes-section">
          <h3>Note</h3>
          <p>{unita.note}</p>
        </div>
      )}
    </div>
  );
}
