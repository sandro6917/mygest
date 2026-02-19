/**
 * Pagina popup per protocollazione documenti e fascicoli
 * Aperta tramite window.open() dalle detail page
 */
import React, { useState, useEffect } from 'react';
import { isAxiosError } from 'axios';
import { useSearchParams } from 'react-router-dom';
import type { ProtocollazioneInput } from '@/api/protocolloApi';
import { protocollaDocumento, protocollaFascicolo } from '@/api/protocolloApi';
import { archivioApi } from '@/api/archivio';
import type { UbicazioneOption } from '@/components/UbicazioneAutocomplete';
import { UbicazioneAutocomplete } from '@/components/UbicazioneAutocomplete';
import '@/styles/global.css';

console.log('🔵 ProtocollazionePopupPage module loaded');

const ProtocollazionePopupPageContent: React.FC = () => {
  console.log('🟢 Component render started');
  
  const [searchParams] = useSearchParams();
  const tipo = searchParams.get('tipo') as 'documento' | 'fascicolo' | null;
  const id = searchParams.get('id');
  const titolo = searchParams.get('titolo');

  console.log('🔴 ProtocollazionePopupPage - params:', { tipo, id, titolo });

  const [loading, setLoading] = useState(false);
  const [direzione, setDirezione] = useState<'IN' | 'OUT'>('IN');
  const [quando, setQuando] = useState<string>('');
  const [daChiAChi, setDaChiAChi] = useState('');
  const [dataRientroPrevista, setDataRientroPrevista] = useState('');
  const [ubicazioneId, setUbicazioneId] = useState<number | null>(null);
  const [causale, setCausale] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);
  const [unitaFisiche, setUnitaFisiche] = useState<UbicazioneOption[]>([]);
  const [loadingUnita, setLoadingUnita] = useState(true);

  const getErrorMessage = (err: unknown) => {
    if (isAxiosError(err)) {
      return (
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        'Errore durante la protocollazione'
      );
    }
    if (err instanceof Error) {
      return err.message;
    }
    return 'Errore durante la protocollazione';
  };

  useEffect(() => {
    // Inizializza data/ora corrente
    const now = new Date();
    const localDatetime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
    setQuando(localDatetime);

    // Carica unità fisiche per l'autocomplete
    const loadUnitaFisiche = async () => {
      try {
        setLoadingUnita(true);
        console.log('Caricamento unità fisiche...');
        const unita = await archivioApi.list();
        console.log('Unità fisiche caricate:', unita.length, unita);
        const options: UbicazioneOption[] = unita.map(u => ({
          id: u.id,
          tipo: u.tipo || '',
          codice: u.codice,
          nome: u.nome,
          full_path: u.full_path,
        }));
        console.log('Opzioni preparate:', options.length, options);
        setUnitaFisiche(options);
      } catch (err) {
        console.error('Errore caricamento unità fisiche:', err);
      } finally {
        setLoadingUnita(false);
      }
    };

    loadUnitaFisiche();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!tipo || !id) {
      setError('Parametri mancanti');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const data: ProtocollazioneInput = {
        direzione,
        quando: new Date(quando).toISOString(),
      };

      if (direzione === 'IN') {
        data.da_chi = daChiAChi;
      } else {
        data.a_chi = daChiAChi;
      }

      if (dataRientroPrevista) {
        data.data_rientro_prevista = dataRientroPrevista;
      }
      if (ubicazioneId) {
        data.ubicazione_id = ubicazioneId;
      }
      if (causale) {
        data.causale = causale;
      }
      if (note) {
        data.note = note;
      }

      if (tipo === 'documento') {
        await protocollaDocumento(parseInt(id), data);
      } else {
        await protocollaFascicolo(parseInt(id), data);
      }

      setSuccess(true);
      
      // Notifica la finestra parent e chiudi dopo 1 secondo
      if (window.opener) {
        window.opener.postMessage({ type: 'protocollazione-success' }, '*');
      }
      setTimeout(() => {
        window.close();
      }, 1000);
    } catch (err) {
      console.error('Errore protocollazione:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (!tipo || !id) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center',
        backgroundColor: '#ffffff',
        minHeight: '100vh',
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
        <h2 style={{ color: '#dc3545', marginBottom: '1rem' }}>⚠️ Parametri mancanti</h2>
        <p style={{ color: '#6c757d', marginBottom: '1rem' }}>
          Impossibile aprire la finestra di protocollazione.
        </p>
        <p style={{ fontSize: '0.875rem', color: '#6c757d' }}>
          Tipo: {tipo || 'non specificato'}<br />
          ID: {id || 'non specificato'}
        </p>
        <button 
          onClick={() => window.close()} 
          style={{
            marginTop: '1.5rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Chiudi
        </button>
      </div>
    );
  }

  if (success) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center',
        backgroundColor: '#ffffff',
        minHeight: '100vh',
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
        <div style={{ color: '#28a745', fontSize: '3rem', marginBottom: '1rem' }}>✓</div>
        <h2 style={{ color: '#28a745', marginBottom: '1rem' }}>Protocollazione completata!</h2>
        <p style={{ color: '#6c757d' }}>Questa finestra si chiuderà automaticamente...</p>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '2rem', 
      maxWidth: '600px', 
      margin: '0 auto',
      backgroundColor: '#ffffff',
      minHeight: '100vh',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <h2 style={{ marginBottom: '1.5rem', color: '#1a1a1a' }}>
        Protocolla {tipo === 'documento' ? 'Documento' : 'Fascicolo'}
      </h2>
      
      {titolo && (
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#f8f9fa', 
          borderRadius: '4px',
          marginBottom: '1.5rem',
          color: '#1a1a1a'
        }}>
          <strong>{titolo}</strong>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {error && (
          <div style={{ 
            padding: '0.75rem', 
            marginBottom: '1rem',
            backgroundColor: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
            color: '#721c24'
          }}>
            {error}
          </div>
        )}

        {/* Direzione */}
        <div className="form-group">
          <label className="form-label">
            Direzione <span style={{ color: '#dc3545' }}>*</span>
          </label>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="radio"
                value="IN"
                checked={direzione === 'IN'}
                onChange={(e) => setDirezione(e.target.value as 'IN' | 'OUT')}
              />
              <span style={{ 
                padding: '0.25rem 0.5rem',
                backgroundColor: '#28a745',
                color: 'white',
                borderRadius: '4px',
                fontSize: '0.875rem'
              }}>
                ENTRATA (IN)
              </span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="radio"
                value="OUT"
                checked={direzione === 'OUT'}
                onChange={(e) => setDirezione(e.target.value as 'IN' | 'OUT')}
              />
              <span style={{ 
                padding: '0.25rem 0.5rem',
                backgroundColor: '#ffc107',
                color: '#212529',
                borderRadius: '4px',
                fontSize: '0.875rem'
              }}>
                USCITA (OUT)
              </span>
            </label>
          </div>
        </div>

        {/* Data/Ora */}
        <div className="form-group">
          <label className="form-label" htmlFor="quando">
            Data e Ora <span style={{ color: '#dc3545' }}>*</span>
          </label>
          <input
            type="datetime-local"
            id="quando"
            className="form-control"
            value={quando}
            onChange={(e) => setQuando(e.target.value)}
            required
          />
        </div>

        {/* Da chi / A chi */}
        <div className="form-group">
          <label className="form-label" htmlFor="daChiAChi">
            {direzione === 'IN' ? 'Da chi' : 'A chi'} <span style={{ color: '#dc3545' }}>*</span>
          </label>
          <input
            type="text"
            id="daChiAChi"
            className="form-control"
            value={daChiAChi}
            onChange={(e) => setDaChiAChi(e.target.value)}
            placeholder={direzione === 'IN' ? 'Nome del mittente' : 'Nome del destinatario'}
            required
          />
          <small style={{ color: '#6c757d', fontSize: '0.875rem' }}>
            {direzione === 'IN' 
              ? 'Indica da chi è stato ricevuto il documento/fascicolo'
              : 'Indica a chi è stato consegnato il documento/fascicolo'}
          </small>
        </div>

        {/* Data rientro prevista (solo per OUT) */}
        {direzione === 'OUT' && (
          <div className="form-group">
            <label className="form-label" htmlFor="dataRientroPrevista">
              Data Rientro Prevista
            </label>
            <input
              type="date"
              id="dataRientroPrevista"
              className="form-control"
              value={dataRientroPrevista}
              onChange={(e) => setDataRientroPrevista(e.target.value)}
            />
            <small style={{ color: '#6c757d', fontSize: '0.875rem' }}>
              Quando prevedi che il documento/fascicolo rientrerà
            </small>
          </div>
        )}

        {/* Ubicazione (autocomplete per IN) */}
        {direzione === 'IN' && (
          <div className="form-group">
            <label className="form-label">
              Ubicazione {loadingUnita && <span style={{ fontSize: '0.75rem', color: '#6c757d' }}>(Caricamento...)</span>}
            </label>
            <UbicazioneAutocomplete
              value={ubicazioneId}
              unitaFisiche={unitaFisiche}
              onChange={setUbicazioneId}
              placeholder={loadingUnita ? "Caricamento ubicazioni..." : "Seleziona ubicazione..."}
              disabled={loadingUnita}
            />
            <small style={{ color: '#6c757d', fontSize: '0.875rem' }}>
              Dove verrà archiviato il documento/fascicolo
              {loadingUnita && (
                <span style={{ color: '#ffc107', marginLeft: '0.5rem' }}>
                  ⏳ Caricamento in corso...
                </span>
              )}
              {!loadingUnita && unitaFisiche.length === 0 && (
                <span style={{ color: '#dc3545', marginLeft: '0.5rem' }}>
                  ⚠️ Nessuna ubicazione trovata (verifica console per errori)
                </span>
              )}
              {!loadingUnita && unitaFisiche.length > 0 && (
                <span style={{ color: '#28a745', marginLeft: '0.5rem' }}>
                  ✓ {unitaFisiche.length} ubicazioni disponibili
                </span>
              )}
            </small>
          </div>
        )}

        {/* Causale */}
        <div className="form-group">
          <label className="form-label" htmlFor="causale">
            Causale
          </label>
          <input
            type="text"
            id="causale"
            className="form-control"
            value={causale}
            onChange={(e) => setCausale(e.target.value)}
            placeholder="Motivo della protocollazione"
          />
        </div>

        {/* Note */}
        <div className="form-group">
          <label className="form-label" htmlFor="note">
            Note
          </label>
          <textarea
            id="note"
            className="form-control"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            placeholder="Note aggiuntive..."
          />
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
          <button
            type="button"
            onClick={() => window.close()}
            className="btn-secondary"
            disabled={loading}
          >
            Annulla
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Salvataggio...' : 'Protocolla'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Error Boundary wrapper
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    console.error('🚨 ErrorBoundary caught error:', error);
    return { hasError: true, error };
  }

  componentDidCatch(_error: Error, errorInfo: React.ErrorInfo) {
    console.error('🚨 Component stack:', errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', color: 'red', fontFamily: 'monospace' }}>
          <h2>⚠️ Errore nel componente</h2>
          <pre>{this.state.error?.message}</pre>
          <pre>{this.state.error?.stack}</pre>
        </div>
      );
    }

    return this.props.children;
  }
}

const ProtocollazionePopupPage: React.FC = () => {
  return (
    <ErrorBoundary>
      <ProtocollazionePopupPageContent />
    </ErrorBoundary>
  );
};

export default ProtocollazionePopupPage;
