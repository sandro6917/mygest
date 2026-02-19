import { useState } from 'react';
import { isAxiosError } from 'axios';
import { AddIcon, EditIcon, DeleteIcon, EmailIcon, StarIcon } from './icons/Icons';
import { apiClient } from '../api/client';

interface EmailContatto {
  id?: number;
  nominativo: string;
  email: string;
  tipo: string;
  tipo_display?: string;
  note: string;
  is_preferito: boolean;
  attivo: boolean;
}

interface ContattiEmailManagerProps {
  anagraficaId: number;
  contatti: EmailContatto[];
  onUpdate: () => void;
}

const TIPI_CONTATTO = [
  { value: 'GEN', label: 'Generico' },
  { value: 'PEC', label: 'PEC' },
  { value: 'AMM', label: 'Amministrativo' },
  { value: 'COM', label: 'Commerciale' },
  { value: 'TEC', label: 'Tecnico' },
  { value: 'ALT', label: 'Altro' },
];

export function ContattiEmailManager({ anagraficaId, contatti, onUpdate }: ContattiEmailManagerProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<EmailContatto>({
    nominativo: '',
    email: '',
    tipo: 'GEN',
    note: '',
    is_preferito: false,
    attivo: true,
  });

  const resetForm = () => {
    setFormData({
      nominativo: '',
      email: '',
      tipo: 'GEN',
      note: '',
      is_preferito: false,
      attivo: true,
    });
    setIsAdding(false);
    setEditingId(null);
  };

  const handleAdd = () => {
    resetForm();
    setIsAdding(true);
  };

  const handleEdit = (contatto: EmailContatto) => {
    setFormData(contatto);
    setEditingId(contatto.id!);
    setIsAdding(false);
  };

  const handleSave = async () => {
    try {
      if (editingId) {
        // Update
        await apiClient.put(`/anagrafiche/${anagraficaId}/contatti-email/${editingId}/`, formData);
        alert('Contatto aggiornato!');
      } else {
        // Create
        await apiClient.post(`/anagrafiche/${anagraficaId}/contatti-email/`, formData);
        alert('Contatto aggiunto!');
      }
      resetForm();
      onUpdate();
    } catch (error: unknown) {
      const errorMsg = extractErrorMessage(error);
      alert('Errore: ' + errorMsg);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Eliminare questo contatto?')) return;
    
    try {
      await apiClient.delete(`/anagrafiche/${anagraficaId}/contatti-email/${id}/`);
      alert('Contatto eliminato!');
      onUpdate();
    } catch (error: unknown) {
      alert('Errore: ' + extractErrorMessage(error));
    }
  };

  const extractErrorMessage = (error: unknown): string => {
    if (isAxiosError(error)) {
      if (error.response?.data) {
        return typeof error.response.data === 'string'
          ? error.response.data
          : JSON.stringify(error.response.data, null, 2);
      }
      return error.message;
    }
    if (error instanceof Error) {
      return error.message;
    }
    return 'Errore sconosciuto';
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
          <EmailIcon size={20} />
          Contatti Email
        </h3>
        {!isAdding && !editingId && (
          <button onClick={handleAdd} className="btn btn-sm btn-primary">
            <AddIcon size={16} />
            <span>Nuovo Contatto</span>
          </button>
        )}
      </div>

      {/* Lista contatti */}
      {!isAdding && !editingId && (
        <div style={{ padding: '1rem' }}>
          {contatti.length === 0 ? (
            <p className="text-muted">Nessun contatto email inserito</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {contatti.map((contatto) => (
                <div 
                  key={contatto.id} 
                  className="card"
                  style={{ 
                    padding: '1rem', 
                    backgroundColor: contatto.is_preferito ? '#fff8e1' : 'white',
                    opacity: contatto.attivo ? 1 : 0.6
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <span className="badge badge-info">{contatto.tipo_display}</span>
                        {contatto.is_preferito && (
                          <span className="badge badge-warning" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <StarIcon size={12} />
                            Preferito
                          </span>
                        )}
                        {!contatto.attivo && <span className="badge badge-secondary">Non attivo</span>}
                      </div>
                      {contatto.nominativo && (
                        <p style={{ margin: '0.25rem 0', fontWeight: 'bold' }}>{contatto.nominativo}</p>
                      )}
                      <p style={{ 
                        margin: '0.25rem 0', 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '0.5rem',
                        minWidth: 0
                      }}>
                        <span style={{ flexShrink: 0 }}>
                          <EmailIcon size={16} />
                        </span>
                        <a 
                          href={`mailto:${contatto.email}`}
                          style={{ 
                            wordBreak: 'break-all',
                            overflowWrap: 'anywhere',
                            minWidth: 0
                          }}
                        >
                          {contatto.email}
                        </a>
                      </p>
                      {contatto.note && (
                        <p style={{ margin: '0.5rem 0 0', fontSize: '0.9em', color: '#666' }}>{contatto.note}</p>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button onClick={() => handleEdit(contatto)} className="btn btn-sm btn-secondary">
                        <EditIcon size={14} />
                      </button>
                      <button onClick={() => handleDelete(contatto.id!)} className="btn btn-sm btn-danger">
                        <DeleteIcon size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Form nuovo/modifica */}
      {(isAdding || editingId) && (
        <div style={{ padding: '1rem' }}>
          <div className="form-grid">
            <div className="form-group" style={{ gridColumn: 'span 2' }}>
              <label>Nominativo</label>
              <input
                type="text"
                className="form-control"
                value={formData.nominativo}
                onChange={(e) => setFormData({ ...formData, nominativo: e.target.value })}
                placeholder="Es: Mario Rossi"
              />
            </div>

            <div className="form-group" style={{ gridColumn: 'span 2' }}>
              <label>Email *</label>
              <input
                type="email"
                className="form-control"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="email@esempio.it"
              />
            </div>

            <div className="form-group">
              <label>Tipo *</label>
              <select
                className="form-control"
                value={formData.tipo}
                onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
              >
                {TIPI_CONTATTO.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ gridColumn: 'span 3' }}>
              <label>Note</label>
              <input
                type="text"
                className="form-control"
                value={formData.note}
                onChange={(e) => setFormData({ ...formData, note: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.is_preferito}
                  onChange={(e) => setFormData({ ...formData, is_preferito: e.target.checked })}
                  style={{ marginRight: '0.5rem' }}
                />
                Preferito
              </label>
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.attivo}
                  onChange={(e) => setFormData({ ...formData, attivo: e.target.checked })}
                  style={{ marginRight: '0.5rem' }}
                />
                Attivo
              </label>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
            <button onClick={handleSave} className="btn btn-primary">
              Salva
            </button>
            <button onClick={resetForm} className="btn btn-secondary">
              Annulla
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
