/**
 * Componente per gestire gli allegati di una comunicazione
 * Supporta: documenti, fascicoli e file upload
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { allegatiComunicazioneApi } from '@/api/comunicazioni';
import { DocumentoAutocomplete } from './DocumentoAutocomplete';
import { FascicoloAutocomplete } from './FascicoloAutocomplete';

interface AllegatiManagerProps {
  comunicazioneId: number;
  readonly?: boolean;
}

const AllegatiManager = ({ comunicazioneId, readonly = false }: AllegatiManagerProps) => {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [tipoAllegato, setTipoAllegato] = useState<'documento' | 'fascicolo' | 'file'>('file');
  const [documentoId, setDocumentoId] = useState<number | null>(null);
  const [fascicoloId, setFascicoloId] = useState<number | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [note, setNote] = useState('');

  // Query per lista allegati
  const { data: allegati, isLoading } = useQuery({
    queryKey: ['allegati', comunicazioneId],
    queryFn: async () => {
      const result = await allegatiComunicazioneApi.list(comunicazioneId);
      console.log('📋 Allegati ricevuti dall\'API:', result);
      return result;
    },
    enabled: !!comunicazioneId,
  });

  // Mutation per upload file
  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      console.log('📤 Uploading file:', {
        name: file.name,
        size: file.size,
        type: file.type
      });
      return allegatiComunicazioneApi.uploadFile(comunicazioneId, file, note);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['allegati', comunicazioneId] });
      resetForm();
      alert('File caricato con successo!');
    },
    onError: (error: any) => {
      console.error('❌ Errore upload allegato:', error);
      console.error('Response data:', error.response?.data);
      
      let errorMessage = 'Errore nel caricamento del file';
      
      if (error.response?.data) {
        const data = error.response.data;
        // Gestisce errori di validazione Django
        if (typeof data === 'object') {
          const errors = [];
          for (const [field, messages] of Object.entries(data)) {
            if (Array.isArray(messages)) {
              errors.push(`${field}: ${messages.join(', ')}`);
            } else {
              errors.push(`${field}: ${messages}`);
            }
          }
          errorMessage = errors.join('\n');
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.error) {
          errorMessage = data.error;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ ${errorMessage}`);
    },
  });

  // Mutation per aggiungere documento/fascicolo
  const addMutation = useMutation({
    mutationFn: (data: any) => {
      return allegatiComunicazioneApi.create(comunicazioneId, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['allegati', comunicazioneId] });
      resetForm();
      alert('Allegato aggiunto con successo!');
    },
    onError: (error: any) => {
      alert(`Errore nell'aggiunta: ${error.response?.data?.detail || error.message || 'Errore sconosciuto'}`);
    },
  });

  // Mutation per eliminare allegato
  const deleteMutation = useMutation({
    mutationFn: (id: number) => allegatiComunicazioneApi.delete(comunicazioneId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['allegati', comunicazioneId] });
      alert('Allegato eliminato con successo!');
    },
    onError: (error) => {
      alert(`Errore nell'eliminazione: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`);
    },
  });

  const resetForm = () => {
    setShowAddForm(false);
    setTipoAllegato('file');
    setDocumentoId(null);
    setFascicoloId(null);
    setSelectedFile(null);
    setNote('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (tipoAllegato === 'file') {
      if (!selectedFile) {
        alert('Seleziona un file da caricare');
        return;
      }
      uploadMutation.mutate(selectedFile);
    } else if (tipoAllegato === 'documento') {
      if (!documentoId) {
        alert('Seleziona un documento');
        return;
      }
      addMutation.mutate({ documento: documentoId, note });
    } else if (tipoAllegato === 'fascicolo') {
      if (!fascicoloId) {
        alert('Seleziona un fascicolo');
        return;
      }
      addMutation.mutate({ fascicolo: fascicoloId, note });
    }
  };

  const handleDelete = (id: number, filename: string) => {
    if (confirm(`Sei sicuro di voler eliminare l'allegato "${filename}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  const getTipoIcon = (tipo: string) => {
    switch (tipo) {
      case 'documento':
        return '📄';
      case 'fascicolo':
        return '📁';
      case 'file':
        return '📎';
      default:
        return '❓';
    }
  };

  if (isLoading) {
    return <div className="allegati-manager">Caricamento allegati...</div>;
  }

  return (
    <div className="allegati-manager">
      <div className="allegati-header">
        <h4>Allegati ({allegati?.length || 0})</h4>
        {!readonly && (
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? 'Annulla' : '+ Aggiungi Allegato'}
          </button>
        )}
      </div>

      {/* Form aggiunta allegato */}
      {showAddForm && !readonly && (
        <div className="allegato-form card mt-3 mb-3">
          <div className="card-body">
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Tipo Allegato</label>
                <select
                  className="form-control"
                  value={tipoAllegato}
                  onChange={(e) => setTipoAllegato(e.target.value as any)}
                >
                  <option value="file">Carica File</option>
                  <option value="documento">Documento Esistente</option>
                  <option value="fascicolo">Fascicolo (ZIP)</option>
                </select>
              </div>

              {tipoAllegato === 'file' && (
                <div className="form-group">
                  <label>File</label>
                  <input
                    type="file"
                    className="form-control"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    required
                  />
                </div>
              )}

              {tipoAllegato === 'documento' && (
                <div className="form-group">
                  <label>Documento</label>
                  <DocumentoAutocomplete
                    value={documentoId}
                    onChange={setDocumentoId}
                  />
                  <small className="form-text text-muted">
                    Cerca e seleziona un documento esistente con file allegato
                  </small>
                </div>
              )}

              {tipoAllegato === 'fascicolo' && (
                <div className="form-group">
                  <label>Fascicolo</label>
                  <FascicoloAutocomplete
                    value={fascicoloId}
                    onChange={setFascicoloId}
                  />
                  <small className="form-text text-muted">
                    Verrà generato un file ZIP con tutti i documenti del fascicolo
                  </small>
                </div>
              )}

              <div className="form-group">
                <label>Note (opzionale)</label>
                <textarea
                  className="form-control"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={2}
                  placeholder="Note sull'allegato"
                />
              </div>

              <div className="form-group mb-0">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={uploadMutation.isPending || addMutation.isPending}
                >
                  {uploadMutation.isPending || addMutation.isPending ? 'Caricamento...' : 'Aggiungi'}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary ml-2"
                  onClick={resetForm}
                >
                  Annulla
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lista allegati */}
      {allegati && allegati.length > 0 ? (
        <div className="allegati-list mt-3">
          <table className="table table-sm">
            <thead>
              <tr>
                <th style={{ width: '40px' }}>Tipo</th>
                <th>Nome File</th>
                <th>Note</th>
                <th>Data</th>
                {!readonly && <th style={{ width: '80px' }}>Azioni</th>}
              </tr>
            </thead>
            <tbody>
              {allegati.map((allegato) => (
                <tr key={allegato.id}>
                  <td className="text-center">{getTipoIcon(allegato.tipo)}</td>
                  <td>
                    {allegato.file_url ? (
                      <a href={allegato.file_url} target="_blank" rel="noopener noreferrer">
                        {allegato.filename}
                      </a>
                    ) : (
                      allegato.filename
                    )}
                    {allegato.documento_display && (
                      <small className="text-muted d-block">{allegato.documento_display}</small>
                    )}
                    {allegato.fascicolo_display && (
                      <small className="text-muted d-block">{allegato.fascicolo_display}</small>
                    )}
                  </td>
                  <td>
                    {allegato.note && (
                      <small className="text-muted">{allegato.note}</small>
                    )}
                  </td>
                  <td>
                    <small>{new Date(allegato.data_creazione).toLocaleDateString()}</small>
                  </td>
                  {!readonly && (
                    <td>
                      <button
                        type="button"
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(allegato.id, allegato.filename)}
                        disabled={deleteMutation.isPending}
                      >
                        🗑️
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="alert alert-info mt-3">
          Nessun allegato presente
        </div>
      )}
    </div>
  );
};

export default AllegatiManager;
