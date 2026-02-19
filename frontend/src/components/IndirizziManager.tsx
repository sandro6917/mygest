import { useState } from 'react';
import { isAxiosError } from 'axios';
import { AddIcon, EditIcon, DeleteIcon, LocationIcon } from './icons/Icons';
import { apiClient } from '../api/client';
import { ComuneAutocomplete } from './ComuneAutocomplete';

interface ComuneItaliano {
  id: number;
  nome: string;
  provincia: string;
  cap: string;
  denominazione_completa: string;
}

interface Indirizzo {
  id?: number;
  tipo_indirizzo: string;
  tipo_indirizzo_display?: string;
  toponimo: string;
  indirizzo: string;
  numero_civico: string;
  frazione: string;
  cap: string;
  comune: string;
  provincia: string;
  nazione: string;
  principale: boolean;
  note: string;
  comune_italiano?: number;
  comune_italiano_display?: ComuneItaliano;
}

interface IndirizziManagerProps {
  anagraficaId: number;
  indirizzi: Indirizzo[];
  onUpdate: () => void;
}

const TIPI_INDIRIZZO = [
  { value: 'RES', label: 'Residenza' },
  { value: 'DOM', label: 'Domicilio' },
  { value: 'SLE', label: 'Sede legale' },
  { value: 'SAM', label: 'Sede amministrativa' },
  { value: 'UFI', label: 'Ufficio' },
  { value: 'ALT', label: 'Altro' },
];

export function IndirizziManager({ anagraficaId, indirizzi, onUpdate }: IndirizziManagerProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedComune, setSelectedComune] = useState<ComuneItaliano | null>(null);
  const [formData, setFormData] = useState<Indirizzo>({
    tipo_indirizzo: 'RES',
    toponimo: 'Via',
    indirizzo: '',
    numero_civico: '',
    frazione: '',
    cap: '',
    comune: '',
    provincia: '',
    nazione: 'IT',
    principale: false,
    note: '',
  });

  const resetForm = () => {
    setFormData({
      tipo_indirizzo: 'RES',
      toponimo: 'Via',
      indirizzo: '',
      numero_civico: '',
      frazione: '',
      cap: '',
      comune: '',
      provincia: '',
      nazione: 'IT',
      principale: false,
      note: '',
    });
    setSelectedComune(null);
    setIsAdding(false);
    setEditingId(null);
  };

  const handleAdd = () => {
    resetForm();
    setIsAdding(true);
  };

  const handleEdit = (indirizzo: Indirizzo) => {
    setFormData(indirizzo);
    setSelectedComune(indirizzo.comune_italiano_display || null);
    setEditingId(indirizzo.id!);
    setIsAdding(false);
  };

  const handleComuneChange = (comune: ComuneItaliano | null) => {
    setSelectedComune(comune);
    if (comune) {
      setFormData({
        ...formData,
        comune_italiano: comune.id,
        cap: comune.cap,
        comune: comune.nome,
        provincia: comune.provincia,
        nazione: 'IT'
      });
    } else {
      // Reset to manual entry
      const { comune_italiano: comuneItalianoId, ...rest } = formData;
      void comuneItalianoId;
      setFormData(rest);
    }
  };

  const handleSave = async () => {
    try {
      if (editingId) {
        // Update
        await apiClient.put(`/anagrafiche/${anagraficaId}/indirizzi/${editingId}/`, formData);
        alert('Indirizzo aggiornato!');
      } else {
        // Create
        await apiClient.post(`/anagrafiche/${anagraficaId}/indirizzi/`, formData);
        alert('Indirizzo aggiunto!');
      }
      resetForm();
      onUpdate();
    } catch (error: unknown) {
      alert('Errore: ' + extractErrorMessage(error));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Eliminare questo indirizzo?')) return;
    
    try {
      await apiClient.delete(`/anagrafiche/${anagraficaId}/indirizzi/${id}/`);
      alert('Indirizzo eliminato!');
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
          <LocationIcon size={20} />
          Indirizzi
        </h3>
        {!isAdding && !editingId && (
          <button onClick={handleAdd} className="btn btn-sm btn-primary">
            <AddIcon size={16} />
            <span>Nuovo Indirizzo</span>
          </button>
        )}
      </div>

      {/* Lista indirizzi */}
      {!isAdding && !editingId && (
        <div style={{ padding: '1rem' }}>
          {indirizzi.length === 0 ? (
            <p className="text-muted">Nessun indirizzo inserito</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {indirizzi.map((ind) => (
                <div 
                  key={ind.id} 
                  className="card"
                  style={{ padding: '1rem', backgroundColor: ind.principale ? '#f0f8ff' : 'white' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <span className="badge badge-info">{ind.tipo_indirizzo_display}</span>
                        {ind.principale && <span className="badge badge-success">Principale</span>}
                      </div>
                      <p style={{ margin: '0.25rem 0', fontWeight: 'bold' }}>
                        {ind.toponimo} {ind.indirizzo} {ind.numero_civico}
                      </p>
                      {ind.frazione && <p style={{ margin: '0.25rem 0' }}>Frazione: {ind.frazione}</p>}
                      <p style={{ margin: '0.25rem 0' }}>
                        {ind.cap} {ind.comune} ({ind.provincia}) - {ind.nazione}
                      </p>
                      {ind.note && <p style={{ margin: '0.5rem 0 0', fontSize: '0.9em', color: '#666' }}>{ind.note}</p>}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button onClick={() => handleEdit(ind)} className="btn btn-sm btn-secondary">
                        <EditIcon size={14} />
                      </button>
                      <button onClick={() => handleDelete(ind.id!)} className="btn btn-sm btn-danger">
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
            <div className="form-group">
              <label>Tipo indirizzo *</label>
              <select
                className="form-control"
                value={formData.tipo_indirizzo}
                onChange={(e) => setFormData({ ...formData, tipo_indirizzo: e.target.value })}
              >
                {TIPI_INDIRIZZO.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.principale}
                  onChange={(e) => setFormData({ ...formData, principale: e.target.checked })}
                  style={{ marginRight: '0.5rem' }}
                />
                Principale
              </label>
            </div>

            {/* Autocomplete Comune Italiano */}
            <div className="form-group" style={{ gridColumn: 'span 3' }}>
              <label>Comune Italiano (opzionale)</label>
              <ComuneAutocomplete
                value={selectedComune}
                onChange={handleComuneChange}
                placeholder="Cerca comune italiano..."
              />
              <small style={{ color: '#666', display: 'block', marginTop: '0.25rem' }}>
                {selectedComune 
                  ? 'CAP, Comune e Provincia verranno compilati automaticamente'
                  : 'Lascia vuoto per indirizzi esteri o per compilazione manuale'}
              </small>
            </div>

            <div className="form-group">
              <label>Toponimo</label>
              <select
                className="form-control"
                value={formData.toponimo}
                onChange={(e) => setFormData({ ...formData, toponimo: e.target.value })}
              >
                <option>Via</option>
                <option>Viale</option>
                <option>Piazza</option>
                <option>Corso</option>
                <option>Vicolo</option>
                <option>Contrada</option>
                <option>Strada</option>
                <option>Località</option>
              </select>
            </div>

            <div className="form-group" style={{ gridColumn: 'span 2' }}>
              <label>Indirizzo *</label>
              <input
                type="text"
                className="form-control"
                value={formData.indirizzo}
                onChange={(e) => setFormData({ ...formData, indirizzo: e.target.value })}
                placeholder="Nome strada"
              />
            </div>

            <div className="form-group">
              <label>N. Civico</label>
              <input
                type="text"
                className="form-control"
                value={formData.numero_civico}
                onChange={(e) => setFormData({ ...formData, numero_civico: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Frazione</label>
              <input
                type="text"
                className="form-control"
                value={formData.frazione}
                onChange={(e) => setFormData({ ...formData, frazione: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>CAP *</label>
              <input
                type="text"
                className="form-control"
                value={formData.cap}
                onChange={(e) => setFormData({ ...formData, cap: e.target.value })}
                maxLength={5}
                disabled={!!selectedComune}
                style={{ backgroundColor: selectedComune ? '#f5f5f5' : 'white' }}
              />
            </div>

            <div className="form-group">
              <label>Comune *</label>
              <input
                type="text"
                className="form-control"
                value={formData.comune}
                onChange={(e) => setFormData({ ...formData, comune: e.target.value })}
                disabled={!!selectedComune}
                style={{ backgroundColor: selectedComune ? '#f5f5f5' : 'white' }}
              />
            </div>

            <div className="form-group">
              <label>Provincia *</label>
              <input
                type="text"
                className="form-control"
                value={formData.provincia}
                onChange={(e) => setFormData({ ...formData, provincia: e.target.value.toUpperCase() })}
                maxLength={3}
                placeholder="MI"
                disabled={!!selectedComune}
                style={{ backgroundColor: selectedComune ? '#f5f5f5' : 'white' }}
              />
            </div>

            <div className="form-group">
              <label>Nazione</label>
              <input
                type="text"
                className="form-control"
                value={formData.nazione}
                onChange={(e) => setFormData({ ...formData, nazione: e.target.value.toUpperCase() })}
                maxLength={2}
                disabled={!!selectedComune}
                style={{ backgroundColor: selectedComune ? '#f5f5f5' : 'white' }}
              />
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
