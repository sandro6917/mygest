/**
 * Pagina dettaglio movimento di protocollo
 * Con azione per stampare l'etichetta (ET_PROT_DOC)
 */
import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getMovimentoProtocollo } from '@/api/protocolloApi';
import type { MovimentoProtocollo } from '@/types/protocollo';
import { ArrowBackIcon, PrintIcon, InfoIcon } from '@/components/icons/Icons';

export function MovimentoProtocolloDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [movimento, setMovimento] = useState<MovimentoProtocollo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getErrorMessage = (err: unknown, fallback: string) => {
    if (isAxiosError(err)) {
      return (
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        fallback
      );
    }
    return fallback;
  };

  const loadMovimento = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      const data = await getMovimentoProtocollo(Number(id));
      setMovimento(data);
      setError(null);
    } catch (err) {
      const message = getErrorMessage(err, 'Errore nel caricamento del movimento di protocollo');
      setError(message);
      console.error('Error loading movimento:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadMovimento();
  }, [loadMovimento]);

  const handleStampaEtichetta = async () => {
    if (!movimento) return;

    try {
      // Costruisci i parametri per la stampa dell'etichetta
      const params = new URLSearchParams();
      params.append('movimento_id', movimento.id.toString());

      // Fetch del PDF tramite API (con JWT token negli headers)
      const response = await fetch(`/etichette/stampa/ET_PROT_DOC/?${params.toString()}`, {
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
      console.error('Errore stampa etichetta:', error);
      alert('Errore durante la stampa dell\'etichetta');
    }
  };

  const getDirezioneBadge = (direzione: string) => {
    if (direzione === 'IN') {
      return <span className="badge badge-success">ENTRATA (IN)</span>;
    }
    return <span className="badge badge-warning">USCITA (OUT)</span>;
  };

  const getStatoBadge = (chiuso: boolean, direzione: string) => {
    if (chiuso || direzione === 'IN') {
      return <span className="badge badge-success">Chiuso</span>;
    }
    return <span className="badge badge-warning">Aperto</span>;
  };

  if (loading) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento...</p>
        </div>
      </div>
    );
  }

  if (error || !movimento) {
    return (
      <div className="page-container">
        <div className="card">
          <div style={{ color: '#dc3545', marginBottom: '1rem' }}>
            {error || 'Movimento non trovato'}
          </div>
          <button onClick={() => navigate(-1)} className="btn-secondary">
            <ArrowBackIcon size={18} />
            <span>Torna indietro</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            📋 Movimento Protocollo
          </h1>
          <p className="text-muted">
            <strong>{movimento.protocollo_label}</strong> - {getDirezioneBadge(movimento.direzione)}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button onClick={() => navigate(-1)} className="btn-secondary">
            <ArrowBackIcon size={18} />
            <span>Indietro</span>
          </button>
          <button onClick={handleStampaEtichetta} className="btn-primary">
            <PrintIcon size={18} />
            <span>Stampa Etichetta</span>
          </button>
        </div>
      </div>

      {/* Dettagli Movimento */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <InfoIcon size={24} />
            Dettagli Movimento
          </h3>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Numero Protocollo */}
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Numero Protocollo</label>
              <p style={{ fontSize: '1.25rem', marginTop: '0.25rem' }}>
                {movimento.protocollo_label}
              </p>
            </div>

            {/* Direzione */}
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Direzione</label>
              <p style={{ marginTop: '0.25rem' }}>{getDirezioneBadge(movimento.direzione)}</p>
            </div>

            {/* Stato */}
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Stato</label>
              <p style={{ marginTop: '0.25rem' }}>{getStatoBadge(movimento.chiuso, movimento.direzione)}</p>
            </div>

            {/* Data */}
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Data Movimento</label>
              <p style={{ marginTop: '0.25rem' }}>
                {new Date(movimento.data).toLocaleString('it-IT', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>

            {/* Anno/Numero */}
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Anno / Numero</label>
              <p style={{ marginTop: '0.25rem' }}>
                {movimento.anno} / {movimento.numero.toString().padStart(6, '0')}
              </p>
            </div>

            {/* Cliente */}
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Cliente</label>
              <p style={{ marginTop: '0.25rem' }}>
                <Link to={`/anagrafiche/${movimento.cliente}`}>
                  {movimento.cliente_display || `#${movimento.cliente}`}
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Oggetto Protocollato */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h3>Oggetto Protocollato</h3>
        </div>
        <div className="card-body">
          {movimento.documento && (
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Documento</label>
              <p style={{ marginTop: '0.25rem' }}>
                <Link to={`/documenti/${movimento.documento}`}>
                  📄 {movimento.documento_display || `Documento #${movimento.documento}`}
                </Link>
              </p>
            </div>
          )}

          {movimento.fascicolo && (
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Fascicolo</label>
              <p style={{ marginTop: '0.25rem' }}>
                <Link to={`/fascicoli/${movimento.fascicolo}`}>
                  📁 {movimento.fascicolo_display || `Fascicolo #${movimento.fascicolo}`}
                </Link>
              </p>
            </div>
          )}

          {!movimento.documento && !movimento.fascicolo && movimento.target_label && (
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Oggetto Generico</label>
              <p style={{ marginTop: '0.25rem' }}>{movimento.target_label}</p>
              <p style={{ fontSize: '0.875rem', color: '#6c757d', marginTop: '0.25rem' }}>
                Tipo: {movimento.target_tipo || movimento.target_type || 'N/A'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Destinatario / Mittente */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h3>{movimento.direzione === 'IN' ? 'Mittente' : 'Destinatario'}</h3>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Nome Destinatario/Mittente */}
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>
                {movimento.direzione === 'IN' ? 'Da chi (mittente)' : 'A chi (destinatario)'}
              </label>
              <p style={{ marginTop: '0.25rem' }}>
                {movimento.destinatario || <span className="text-muted">Non specificato</span>}
              </p>
            </div>

            {/* Anagrafica Collegata */}
            {movimento.destinatario_anagrafica && (
              <div>
                <label className="form-label" style={{ fontWeight: 'bold' }}>Anagrafica Collegata</label>
                <p style={{ marginTop: '0.25rem' }}>
                  <Link to={`/anagrafiche/${movimento.destinatario_anagrafica}`}>
                    {movimento.destinatario_anagrafica_display || `#${movimento.destinatario_anagrafica}`}
                  </Link>
                  {movimento.destinatario_anagrafica_detail && (
                    <>
                      <br />
                      <span style={{ fontSize: '0.875rem', color: '#6c757d' }}>
                        {movimento.destinatario_anagrafica_detail.codice_fiscale || 
                         movimento.destinatario_anagrafica_detail.partita_iva}
                      </span>
                    </>
                  )}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Ubicazione */}
      {movimento.ubicazione && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header">
            <h3>Ubicazione Fisica</h3>
          </div>
          <div className="card-body">
            <div>
              <label className="form-label" style={{ fontWeight: 'bold' }}>Collocazione</label>
              {movimento.ubicazione_detail ? (
                <div style={{ marginTop: '0.25rem' }}>
                  <p>
                    <strong>{movimento.ubicazione_detail.codice}</strong>
                    {movimento.ubicazione_detail.nome && ` - ${movimento.ubicazione_detail.nome}`}
                  </p>
                  {movimento.ubicazione_detail.full_path && (
                    <p style={{ fontSize: '0.875rem', color: '#6c757d', marginTop: '0.25rem' }}>
                      📍 {movimento.ubicazione_detail.full_path}
                    </p>
                  )}
                  {movimento.ubicazione_detail.tipo_display && (
                    <p style={{ fontSize: '0.875rem', color: '#6c757d', marginTop: '0.25rem' }}>
                      Tipo: {movimento.ubicazione_detail.tipo_display}
                    </p>
                  )}
                </div>
              ) : (
                <p style={{ marginTop: '0.25rem' }}>
                  {movimento.ubicazione_full_path || `Ubicazione #${movimento.ubicazione}`}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Dettagli Aggiuntivi */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <h3>Dettagli Aggiuntivi</h3>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Operatore */}
            {movimento.operatore && (
              <div>
                <label className="form-label" style={{ fontWeight: 'bold' }}>Operatore</label>
                <p style={{ marginTop: '0.25rem' }}>
                  {movimento.operatore_display || `Utente #${movimento.operatore}`}
                </p>
              </div>
            )}

            {/* Data Rientro Prevista */}
            {movimento.data_rientro_prevista && (
              <div>
                <label className="form-label" style={{ fontWeight: 'bold' }}>Data Rientro Prevista</label>
                <p style={{ marginTop: '0.25rem' }}>
                  {new Date(movimento.data_rientro_prevista).toLocaleDateString('it-IT', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
            )}

            {/* Causale */}
            {movimento.causale && (
              <div style={{ gridColumn: '1 / -1' }}>
                <label className="form-label" style={{ fontWeight: 'bold' }}>Causale</label>
                <p style={{ marginTop: '0.25rem' }}>{movimento.causale}</p>
              </div>
            )}

            {/* Note */}
            {movimento.note && (
              <div style={{ gridColumn: '1 / -1' }}>
                <label className="form-label" style={{ fontWeight: 'bold' }}>Note</label>
                <p style={{ marginTop: '0.25rem', whiteSpace: 'pre-wrap' }}>{movimento.note}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rientro (se presente) */}
      {movimento.rientro_di && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header" style={{ backgroundColor: '#d4edda' }}>
            <h3 style={{ color: '#155724' }}>✓ Movimento di Rientro</h3>
          </div>
          <div className="card-body">
            <p>
              Questo movimento è il rientro del movimento di uscita{' '}
              <Link to={`/protocollo/movimenti/${movimento.rientro_di}`}>
                #{movimento.rientro_di}
              </Link>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default MovimentoProtocolloDetailPage;
