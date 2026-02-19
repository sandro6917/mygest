/**
 * Pagina Dettaglio Comunicazione
 * Visualizza i dettagli completi di una comunicazione con azioni disponibili
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { comunicazioniApi } from '@/api/comunicazioni';
import AllegatiManager from '@/components/comunicazioni/AllegatiManager';
import {
  TIPO_COMUNICAZIONE_CHOICES,
  DIREZIONE_CHOICES,
} from '@/types/comunicazioni';
import '@/styles/comunicazioni.css';

const ComunicazioneDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Query per comunicazione
  const { data: comunicazione, isLoading } = useQuery({
    queryKey: ['comunicazione', id],
    queryFn: () => comunicazioniApi.get(Number(id)),
  });

  // Mutation per invio
  const sendMutation = useMutation({
    mutationFn: () => comunicazioniApi.send(Number(id)),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['comunicazione', id] });
      queryClient.invalidateQueries({ queryKey: ['comunicazioni'] });
      
      if (data.warning) {
        alert(data.warning);
      } else {
        alert('Comunicazione inviata con successo!');
      }
    },
    onError: (error) => {
      alert(`Errore nell'invio: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`);
    },
  });

  // Mutation per delete
  const deleteMutation = useMutation({
    mutationFn: () => comunicazioniApi.delete(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comunicazioni'] });
      navigate('/comunicazioni');
    },
    onError: (error) => {
      alert(
        `Errore nell'eliminazione: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`
      );
    },
  });

  // Handler invio
  const handleSend = () => {
    if (confirm('Sei sicuro di voler inviare questa comunicazione?')) {
      sendMutation.mutate();
    }
  };

  // Handler delete
  const handleDelete = () => {
    deleteMutation.mutate();
    setShowDeleteConfirm(false);
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

  if (isLoading) {
    return <div className="page-container">Caricamento...</div>;
  }

  if (!comunicazione) {
    return (
      <div className="page-container">
        <div className="alert alert-error">Comunicazione non trovata</div>
      </div>
    );
  }

  const canEdit = comunicazione.stato === 'bozza';
  const canSend = comunicazione.stato === 'bozza';
  const canDelete = comunicazione.stato === 'bozza';

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>
            Comunicazione #{comunicazione.id} {getStatoBadge(comunicazione.stato)}
          </h1>
          <p className="text-muted">{comunicazione.oggetto}</p>
        </div>
        <button className="btn btn-secondary" onClick={() => navigate('/comunicazioni')}>
          ← Torna alla Lista
        </button>
      </div>

      {/* Azioni */}
      <div className="action-bar mb-3">
        {canEdit && (
          <button
            className="btn btn-warning"
            onClick={() => navigate(`/comunicazioni/${id}/modifica`)}
          >
            ✏️ Modifica
          </button>
        )}
        {canSend && (
          <button
            className="btn btn-primary"
            onClick={handleSend}
            disabled={sendMutation.isPending}
          >
            📧 {sendMutation.isPending ? 'Invio in corso...' : 'Invia'}
          </button>
        )}
        {!comunicazione.protocollo_movimento && comunicazione.documento_protocollo && (
          <button
            className="btn btn-info"
            onClick={() => navigate(`/comunicazioni/${id}/protocolla`)}
          >
            📋 Protocolla
          </button>
        )}
        {canDelete && (
          <button
            className="btn btn-danger"
            onClick={() => setShowDeleteConfirm(true)}
            disabled={deleteMutation.isPending}
          >
            🗑️ Elimina
          </button>
        )}
      </div>

      {/* Errore invio */}
      {comunicazione.stato === 'errore' && comunicazione.log_errore && (
        <div className="alert alert-error mb-3">
          <strong>Errore invio:</strong>
          <pre>{comunicazione.log_errore}</pre>
        </div>
      )}

      {/* Dettagli Principali */}
      <div className="card mb-3">
        <div className="card-header">
          <h3>Informazioni Principali</h3>
        </div>
        <div className="card-body">
          <div className="detail-grid">
            <div className="detail-item">
              <strong>Tipo:</strong>
              <span>
                {TIPO_COMUNICAZIONE_CHOICES.find((c) => c.value === comunicazione.tipo)?.label}
              </span>
            </div>

            <div className="detail-item">
              <strong>Direzione:</strong>
              <span
                className={`badge ${
                  comunicazione.direzione === 'IN' ? 'badge-info' : 'badge-primary'
                }`}
              >
                {DIREZIONE_CHOICES.find((c) => c.value === comunicazione.direzione)?.label}
              </span>
            </div>

            <div className="detail-item">
              <strong>Data Creazione:</strong>
              <span>{formatDate(comunicazione.data_creazione)}</span>
            </div>

            <div className="detail-item">
              <strong>Data Invio:</strong>
              <span>{formatDate(comunicazione.data_invio)}</span>
            </div>

            {comunicazione.mittente && (
              <div className="detail-item">
                <strong>Mittente:</strong>
                <span>{comunicazione.mittente}</span>
              </div>
            )}

            {comunicazione.protocollo_label && (
              <div className="detail-item">
                <strong>Protocollo:</strong>
                <span className="badge badge-secondary">{comunicazione.protocollo_label}</span>
              </div>
            )}

            {comunicazione.template_nome && (
              <div className="detail-item">
                <strong>Template:</strong>
                <span className="badge badge-info">{comunicazione.template_nome}</span>
              </div>
            )}

            {comunicazione.firma_nome && (
              <div className="detail-item">
                <strong>Firma:</strong>
                <span className="badge badge-success">{comunicazione.firma_nome}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Destinatari */}
      <div className="card mb-3">
        <div className="card-header">
          <h3>Destinatari</h3>
        </div>
        <div className="card-body">
          <div className="detail-item">
            <strong>Totale Destinatari:</strong>
            <span className="badge badge-info">{comunicazione.destinatari_calcolati.length}</span>
          </div>
          <div className="detail-item">
            <strong>Elenco:</strong>
            <div className="email-list">
              {comunicazione.destinatari_calcolati.map((email, index) => (
                <span key={index} className="badge badge-light">
                  {email}
                </span>
              ))}
            </div>
          </div>
          {comunicazione.destinatari && (
            <div className="detail-item mt-2">
              <strong>Destinatari manuali:</strong>
              <span>{comunicazione.destinatari}</span>
            </div>
          )}
        </div>
      </div>

      {/* Contenuto */}
      <div className="card mb-3">
        <div className="card-header">
          <h3>Contenuto</h3>
        </div>
        <div className="card-body">
          <div className="detail-item mb-3">
            <strong>Oggetto:</strong>
            <p>{comunicazione.oggetto}</p>
          </div>

          {comunicazione.corpo_html ? (
            <div className="detail-item">
              <strong>Corpo (HTML):</strong>
              <div
                className="html-content"
                dangerouslySetInnerHTML={{ __html: comunicazione.corpo_html }}
              />
            </div>
          ) : (
            <div className="detail-item">
              <strong>Corpo:</strong>
              <pre className="message-body">{comunicazione.corpo}</pre>
            </div>
          )}
        </div>
      </div>

      {/* Allegati */}
      <div className="card mb-3">
        <AllegatiManager comunicazioneId={Number(id)} readonly={true} />
      </div>

      {/* Metadati Tecnici */}
      {(comunicazione.email_message_id || comunicazione.import_source) && (
        <div className="card mb-3">
          <div className="card-header">
            <h3>Informazioni Tecniche</h3>
          </div>
          <div className="card-body">
            {comunicazione.email_message_id && (
              <div className="detail-item">
                <strong>Message ID:</strong>
                <code>{comunicazione.email_message_id}</code>
              </div>
            )}
            {comunicazione.import_source && (
              <div className="detail-item">
                <strong>Sorgente Importazione:</strong>
                <span>{comunicazione.import_source}</span>
              </div>
            )}
            {comunicazione.importato_il && (
              <div className="detail-item">
                <strong>Importato il:</strong>
                <span>{formatDate(comunicazione.importato_il)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Conferma Eliminazione */}
      {showDeleteConfirm && (
        <div className="modal-overlay" onClick={() => setShowDeleteConfirm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Conferma Eliminazione</h3>
            <p>Sei sicuro di voler eliminare questa comunicazione?</p>
            <p className="text-danger">Questa azione non può essere annullata.</p>
            <div className="modal-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleteMutation.isPending}
              >
                Annulla
              </button>
              <button
                className="btn btn-danger"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Eliminazione...' : 'Elimina'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComunicazioneDetailPage;
