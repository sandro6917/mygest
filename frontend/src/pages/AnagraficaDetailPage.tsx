import { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { AnagraficaDetail } from '../types/anagrafiche';
import { 
  EditIcon, 
  DeleteIcon, 
  ArrowBackIcon, 
  PrintIcon, 
  ClientIcon, 
  PersonIcon, 
  BusinessIcon,
  EmailIcon,
  PhoneIcon,
  LocationIcon,
  InfoIcon,
  CheckIcon,
  RefreshIcon,
  AddIcon
} from '../components/icons/Icons';
import { IndirizziManager } from '../components/IndirizziManager';
import { ContattiEmailManager } from '../components/ContattiEmailManager';

export function AnagraficaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [anagrafica, setAnagrafica] = useState<AnagraficaDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadAnagrafica = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      const response = await apiClient.get<AnagraficaDetail>(`/anagrafiche/${id}/`);
      setAnagrafica(response.data);
      setError(null);
    } catch (error: unknown) {
      const message = extractAxiosMessage(error);
      setError(message ?? 'Errore nel caricamento dell\'anagrafica');
      console.error('Error loading anagrafica:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  // Ricarica i dati quando l'id cambia
  useEffect(() => {
    if (!id) {
      return;
    }
    void loadAnagrafica();
  }, [id, loadAnagrafica]);

  const handleDelete = async () => {
    if (!id) return;
    
    if (!confirm('Sei sicuro di voler eliminare questa anagrafica?')) {
      return;
    }

    try {
      setDeleting(true);
      await apiClient.delete(`/anagrafiche/${id}/`);
      navigate(-1); // Torna alla pagina precedente
    } catch (error: unknown) {
      alert(extractAxiosMessage(error) ?? 'Errore nell\'eliminazione dell\'anagrafica');
      setDeleting(false);
    }
  };

  const handleMakeCliente = async () => {
    if (!id) return;
    
    try {
      await apiClient.post(`/anagrafiche/${id}/make_cliente/`);
      loadAnagrafica(); // Reload to show updated data
    } catch (error: unknown) {
      alert(extractAxiosMessage(error) ?? 'Errore nella conversione a cliente');
    }
  };

  const handleRicalcolaCodice = async () => {
    if (!id) return;
    
    if (!confirm('Ricalcolare il codice anagrafica? Il codice attuale verrà sostituito se non coerente.')) {
      return;
    }
    
    try {
      const response = await apiClient.post(`/anagrafiche/${id}/ricalcola_codice/`);
      const data = response.data;
      
      // Verifica se il codice è cambiato
      if (data.unchanged) {
        alert(
          `✓ Codice già corretto!\n\n` +
          `${data.message}\n` +
          `Codice attuale: ${data.new_code}`
        );
      } else {
        // Mostra il risultato con il cambio
        alert(
          `Codice aggiornato con successo!\n\n` +
          `Vecchio codice: ${data.old_code || 'nessuno'}\n` +
          `Nuovo codice: ${data.new_code}`
        );
      }
      
      loadAnagrafica(); // Ricarica per mostrare il nuovo codice
    } catch (error: unknown) {
      alert(extractAxiosMessage(error) ?? 'Errore nel ricalcolo del codice');
    }
  };

  const handlePrintFascicolo = () => {
    if (!id || !anagrafica?.cliente) return;
    
    // Apri stampa in nuova finestra
    // URL: /etichette/anagrafiche/cliente/{cliente_id}/?module=FAS_CLI
    // Nota: le stampe sono su endpoint Django tradizionale, non /api/v1/
    const baseUrl = import.meta.env.VITE_API_URL 
      ? import.meta.env.VITE_API_URL.replace('/api/v1', '')
      : 'http://localhost:8000';
    const stampaUrl = `${baseUrl}/etichette/anagrafiche/cliente/${anagrafica.cliente.id}/?module=FAS_CLI`;
    window.open(stampaUrl, '_blank');
  };

  if (loading) {
    return (
      <div className="page-container">
        <h1>📇 Dettaglio Anagrafica</h1>
        <p>Caricamento...</p>
      </div>
    );
  }

  if (error || !anagrafica) {
    return (
      <div className="page-container">
        <h1>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <PersonIcon size={32} />
            Dettaglio Anagrafica
          </span>
        </h1>
        <div className="alert alert-error">{error || 'Anagrafica non trovata'}</div>
        <button onClick={() => navigate(-1)} className="btn btn-secondary">
          <ArrowBackIcon size={18} />
          <span>Torna indietro</span>
        </button>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {anagrafica.tipo === 'PF' ? <PersonIcon size={32} /> : <BusinessIcon size={32} />}
            {anagrafica.display_name}
          </h1>
          <p className="text-muted" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            {anagrafica.tipo === 'PF' ? (
              <>
                <PersonIcon size={16} />
                Persona Fisica
              </>
            ) : (
              <>
                <BusinessIcon size={16} />
                Persona Giuridica
              </>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link to={`/anagrafiche/${id}/edit`} className="btn-primary">
            <EditIcon size={18} />
            <span>Modifica</span>
          </Link>
          
          {anagrafica.cliente && (
            <button 
              className="btn-secondary" 
              onClick={handlePrintFascicolo}
              title="Stampa Fascicolo Cliente"
            >
              <PrintIcon size={18} />
              <span>Fascicolo</span>
            </button>
          )}
          
          <button 
            className="btn-secondary" 
            onClick={handleDelete}
            disabled={deleting}
          >
            <DeleteIcon size={18} />
            <span>{deleting ? 'Eliminazione...' : 'Elimina'}</span>
          </button>
          <button onClick={() => navigate(-1)} className="btn-secondary">
            <ArrowBackIcon size={18} />
            <span>Indietro</span>
          </button>
        </div>
      </div>

      <div className="detail-grid">
        {/* Dati Identificativi */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>📋 Dati Identificativi</h2>
          <div className="detail-row">
            <span className="detail-label">Tipo:</span>
            <span className="detail-value">
              <span className={`badge badge-${anagrafica.tipo === 'PF' ? 'info' : 'success'}`}>
                {anagrafica.tipo === 'PF' ? 'Persona Fisica' : 'Persona Giuridica'}
              </span>
            </span>
          </div>

          {anagrafica.tipo === 'PG' && (
            <div className="detail-row">
              <span className="detail-label">Ragione Sociale:</span>
              <span className="detail-value"><strong>{anagrafica.ragione_sociale}</strong></span>
            </div>
          )}

          {anagrafica.tipo === 'PF' && (
            <>
              <div className="detail-row">
                <span className="detail-label">Nome:</span>
                <span className="detail-value">{anagrafica.nome}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Cognome:</span>
                <span className="detail-value"><strong>{anagrafica.cognome}</strong></span>
              </div>
            </>
          )}

          <div className="detail-row">
            <span className="detail-label">Codice Fiscale:</span>
            <span className="detail-value"><code>{anagrafica.codice_fiscale}</code></span>
          </div>

          {anagrafica.partita_iva && (
            <div className="detail-row">
              <span className="detail-label">Partita IVA:</span>
              <span className="detail-value"><code>{anagrafica.partita_iva}</code></span>
            </div>
          )}

          {anagrafica.codice && (
            <div className="detail-row">
              <span className="detail-label">Codice:</span>
              <span className="detail-value">
                <code>{anagrafica.codice}</code>
                <button 
                  onClick={handleRicalcolaCodice}
                  className="btn btn-sm btn-secondary"
                  style={{ marginLeft: '0.5rem' }}
                  title="Ricalcola codice anagrafica"
                >
                  <RefreshIcon size={14} />
                  <span>Ricalcola</span>
                </button>
              </span>
            </div>
          )}
          
          {!anagrafica.codice && (
            <div className="detail-row">
              <span className="detail-label">Codice:</span>
              <span className="detail-value">
                <span className="text-muted">Non generato</span>
                <button 
                  onClick={handleRicalcolaCodice}
                  className="btn btn-sm btn-primary"
                  style={{ marginLeft: '0.5rem' }}
                  title="Genera codice anagrafica"
                >
                  <AddIcon size={14} />
                  <span>Genera Codice</span>
                </button>
              </span>
            </div>
          )}
        </div>

        {/* Contatti */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <PhoneIcon size={20} />
            Contatti
          </h2>
          
          {anagrafica.pec && (
            <div className="detail-row">
              <span className="detail-label">PEC:</span>
              <span className="detail-value" style={{ minWidth: 0 }}>
                <a 
                  href={`mailto:${anagrafica.pec}`} 
                  style={{ 
                    display: 'inline-flex', 
                    alignItems: 'center', 
                    gap: '0.25rem',
                    wordBreak: 'break-all',
                    overflowWrap: 'anywhere',
                    minWidth: 0
                  }}
                >
                  <span style={{ flexShrink: 0 }}>
                    <EmailIcon size={16} />
                  </span>
                  {anagrafica.pec}
                </a>
              </span>
            </div>
          )}

          {anagrafica.email && (
            <div className="detail-row">
              <span className="detail-label">Email:</span>
              <span className="detail-value" style={{ minWidth: 0 }}>
                <a 
                  href={`mailto:${anagrafica.email}`} 
                  style={{ 
                    display: 'inline-flex', 
                    alignItems: 'center', 
                    gap: '0.25rem',
                    wordBreak: 'break-all',
                    overflowWrap: 'anywhere',
                    minWidth: 0
                  }}
                >
                  <span style={{ flexShrink: 0 }}>
                    <EmailIcon size={16} />
                  </span>
                  {anagrafica.email}
                </a>
              </span>
            </div>
          )}

          {anagrafica.telefono && (
            <div className="detail-row">
              <span className="detail-label">Telefono:</span>
              <span className="detail-value">
                <a href={`tel:${anagrafica.telefono}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                  <PhoneIcon size={16} />
                  {anagrafica.telefono}
                </a>
              </span>
            </div>
          )}

          {anagrafica.indirizzo && (
            <div className="detail-row">
              <span className="detail-label">Indirizzo:</span>
              <span className="detail-value">
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                  <LocationIcon size={16} />
                  {anagrafica.indirizzo}
                </span>
              </span>
            </div>
          )}
        </div>

        {/* Gestione Cliente */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ClientIcon size={20} />
            Gestione Cliente
          </h2>
          
          <div className="detail-row">
            <span className="detail-label">Status:</span>
            <span className="detail-value">
              {anagrafica.cliente ? (
                <span className="badge badge-primary">
                  <CheckIcon size={16} /> Cliente Attivo
                </span>
              ) : (
                <>
                  <span className="badge">Non Cliente</span>
                  <button 
                    onClick={handleMakeCliente}
                    className="btn btn-sm btn-primary"
                    style={{ marginLeft: '0.5rem' }}
                  >
                    Converti in Cliente
                  </button>
                </>
              )}
            </span>
          </div>

          {anagrafica.cliente && (
            <>
              {anagrafica.cliente.tipo_cliente_display && (
                <div className="detail-row">
                  <span className="detail-label">Tipo Cliente:</span>
                  <span className="detail-value">
                    <span className="badge badge-info">
                      {anagrafica.cliente.tipo_cliente_display}
                    </span>
                  </span>
                </div>
              )}
              
              {anagrafica.cliente.cliente_dal && (
                <div className="detail-row">
                  <span className="detail-label">Cliente dal:</span>
                  <span className="detail-value">
                    {new Date(anagrafica.cliente.cliente_dal).toLocaleDateString('it-IT')}
                  </span>
                </div>
              )}
              
              {anagrafica.cliente.cliente_al && (
                <div className="detail-row">
                  <span className="detail-label">Cliente al:</span>
                  <span className="detail-value">
                    {new Date(anagrafica.cliente.cliente_al).toLocaleDateString('it-IT')}
                  </span>
                </div>
              )}
              
              {anagrafica.cliente.codice_destinatario && (
                <div className="detail-row">
                  <span className="detail-label">Codice Destinatario SDI:</span>
                  <span className="detail-value">
                    <code style={{ fontSize: '1.1em', padding: '0.25rem 0.5rem', background: 'var(--bg-secondary)', borderRadius: '4px' }}>
                      {anagrafica.cliente.codice_destinatario}
                    </code>
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Informazioni Sistema */}
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>🕒 Informazioni Sistema</h2>

          <div className="detail-row">
            <span className="detail-label">Creata il:</span>
            <span className="detail-value">
              {new Date(anagrafica.created_at).toLocaleString('it-IT')}
            </span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Aggiornata il:</span>
            <span className="detail-value">
              {new Date(anagrafica.updated_at).toLocaleString('it-IT')}
            </span>
          </div>
        </div>

        {/* Note */}
        {anagrafica.note && (
          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <InfoIcon size={20} />
              Note
            </h2>
            <p style={{ whiteSpace: 'pre-wrap' }}>{anagrafica.note}</p>
          </div>
        )}

        {/* Gestione Indirizzi */}
        <div style={{ gridColumn: '1 / -1' }}>
          <IndirizziManager 
            anagraficaId={Number(id)} 
            indirizzi={anagrafica.indirizzi || []} 
            onUpdate={loadAnagrafica}
          />
        </div>

        {/* Gestione Contatti Email */}
        <div style={{ gridColumn: '1 / -1' }}>
          <ContattiEmailManager 
            anagraficaId={Number(id)} 
            contatti={anagrafica.contatti_email || []} 
            onUpdate={loadAnagrafica}
          />
        </div>
      </div>
    </div>
  );
}

const extractAxiosMessage = (error: unknown): string | null => {
  if (isAxiosError(error)) {
    const data = error.response?.data as { detail?: string; error?: string } | undefined;
    return data?.detail ?? data?.error ?? error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return null;
};
