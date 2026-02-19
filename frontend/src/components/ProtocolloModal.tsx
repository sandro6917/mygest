/**
 * Modal per protocollazione documenti e fascicoli
 */
import React, { useState, useEffect, useCallback } from 'react';
import { isAxiosError } from 'axios';
import type { ProtocollazioneInput } from '@/api/protocolloApi';
import { protocollaDocumento, protocollaFascicolo, protocollaTarget } from '@/api/protocolloApi';
import { fascicoliApi } from '@/api/fascicoli';
import { UbicazioneAutocomplete } from '@/components/UbicazioneAutocomplete';
import type { UbicazioneOption } from '@/components/UbicazioneAutocomplete';
import { AnagraficaAutocomplete } from '@/components/AnagraficaAutocomplete';
import type { AnagraficaOption } from '@/components/AnagraficaAutocomplete';

export interface ProtocolloModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  tipo: 'documento' | 'fascicolo' | 'generico';
  id?: number;
  targetType?: string;
  targetId?: number | string;
  titolo?: string;
}

const ProtocolloModal: React.FC<ProtocolloModalProps> = ({
  visible,
  onClose,
  onSuccess,
  tipo,
  id,
  targetType,
  targetId,
  titolo,
}) => {
  const [loading, setLoading] = useState(false);
  const [direzione, setDirezione] = useState<'IN' | 'OUT'>('IN');
  const [quando, setQuando] = useState<string>('');
  const [daChiAChi, setDaChiAChi] = useState('');
  const [dataRientroPrevista, setDataRientroPrevista] = useState('');
  const [ubicazioneId, setUbicazioneId] = useState<number | undefined>();
  const [causale, setCausale] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState<string>('');
  const [daChiAnagrafica, setDaChiAnagrafica] = useState<AnagraficaOption | null>(null);
  const [aChiAnagrafica, setAChiAnagrafica] = useState<AnagraficaOption | null>(null);
  const [unitaFisiche, setUnitaFisiche] = useState<UbicazioneOption[]>([]);
  const [ubicazioniLoading, setUbicazioniLoading] = useState(false);
  const [ubicazioniError, setUbicazioniError] = useState<string | null>(null);

  const loadUbicazioni = useCallback(async () => {
    setUbicazioniLoading(true);
    setUbicazioniError(null);
    try {
      const data = await fascicoliApi.listUnitaFisiche();
      setUnitaFisiche(data);
    } catch (err) {
      console.error('Errore caricamento ubicazioni:', err);
      setUbicazioniError('Impossibile caricare le unità fisiche');
    } finally {
      setUbicazioniLoading(false);
    }
  }, []);

  useEffect(() => {
    if (visible) {
      // Reset form
      setDirezione('IN');
      const now = new Date();
      const localDatetime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
      setQuando(localDatetime);
      setDaChiAChi('');
      setDataRientroPrevista('');
      setUbicazioneId(undefined);
      setCausale('');
      setNote('');
      setError('');
      setDaChiAnagrafica(null);
      setAChiAnagrafica(null);
    }
  }, [visible]);

  useEffect(() => {
    if (!visible) {
      return;
    }
    if (unitaFisiche.length > 0) {
      return;
    }
    void loadUbicazioni();
  }, [visible, unitaFisiche.length, loadUbicazioni]);

  const handleDirezioneChange = (value: 'IN' | 'OUT') => {
    setDirezione(value);
    setDaChiAChi('');
    setDaChiAnagrafica(null);
    setAChiAnagrafica(null);
    if (value === 'IN') {
      setDataRientroPrevista('');
    }
  };

  const handleAnagraficaSelection = (option: AnagraficaOption | null) => {
    if (direzione === 'IN') {
      setDaChiAnagrafica(option);
    } else {
      setAChiAnagrafica(option);
    }
    if (option) {
      setDaChiAChi(option.display_name);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const hasFreeText = Boolean(daChiAChi.trim());
    const hasAnagrafica = direzione === 'IN' ? Boolean(daChiAnagrafica) : Boolean(aChiAnagrafica);

    if (!hasFreeText && !hasAnagrafica) {
      setError(
        direzione === 'IN'
          ? 'Specificare il mittente oppure selezionare un\'anagrafica registrata'
          : 'Specificare il destinatario oppure selezionare un\'anagrafica registrata'
      );
      return;
    }

    try {
      setLoading(true);

      const data: ProtocollazioneInput = {
        direzione,
        quando: quando || undefined,
        da_chi:
          direzione === 'IN'
            ? (hasFreeText ? daChiAChi : daChiAnagrafica?.display_name || undefined)
            : undefined,
        a_chi:
          direzione === 'OUT'
            ? (hasFreeText ? daChiAChi : aChiAnagrafica?.display_name || undefined)
            : undefined,
        da_chi_anagrafica: direzione === 'IN' ? daChiAnagrafica?.id : undefined,
        a_chi_anagrafica: direzione === 'OUT' ? aChiAnagrafica?.id : undefined,
        data_rientro_prevista:
          direzione === 'OUT' ? (dataRientroPrevista || undefined) : undefined,
        ubicazione_id: ubicazioneId ?? undefined,
        causale: causale || undefined,
        note: note || undefined,
      };

      let response;
      if (tipo === 'documento' && typeof id === 'number') {
        response = await protocollaDocumento(id, data);
      } else if (tipo === 'fascicolo' && typeof id === 'number') {
        response = await protocollaFascicolo(id, data);
      } else if (tipo === 'generico' && targetType && targetId !== undefined) {
        response = await protocollaTarget({
          ...data,
          target_type: targetType,
          target_id: typeof targetId === 'number' ? targetId.toString() : targetId,
        });
      } else {
        setError('Configurazione target non valida');
        setLoading(false);
        return;
      }

      if (response.success) {
        alert(response.message || 'Protocollazione completata con successo');
        onClose();
        if (onSuccess) {
          onSuccess();
        }
      } else {
        setError(response.error || 'Errore durante la protocollazione');
      }
    } catch (err: unknown) {
      console.error('Errore protocollazione:', err);
      setError(extractProtocolError(err));
    } finally {
      setLoading(false);
    }
  };

  const extractProtocolError = (err: unknown): string => {
    if (isAxiosError(err)) {
      const data = err.response?.data as { error?: string } | undefined;
      if (data?.error) {
        return data.error;
      }
      return err.message;
    }
    if (err instanceof Error) {
      return err.message;
    }
    return 'Errore durante la protocollazione';
  };

  if (!visible) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="border-b px-6 py-4 bg-gray-50">
          <h2 className="text-xl font-semibold text-gray-900">
            Protocolla {tipo === 'documento' ? 'Documento' : 'Fascicolo'}
            {titolo && (
              <span className="block text-sm font-normal text-gray-600 mt-1">{titolo}</span>
            )}
          </h2>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              ⚠️ {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 mb-4">
            {/* Direzione */}
            <div className="form-group">
              <label className="form-label">Direzione *</label>
              <select
                value={direzione}
                onChange={(e) => handleDirezioneChange(e.target.value as 'IN' | 'OUT')}
                className="form-control"
                required
              >
                <option value="IN">Entrata (IN)</option>
                <option value="OUT">Uscita (OUT)</option>
              </select>
            </div>

            {/* Data e ora */}
            <div className="form-group">
              <label className="form-label">Data e ora</label>
              <input
                type="datetime-local"
                value={quando}
                onChange={(e) => setQuando(e.target.value)}
                className="form-control"
              />
              <small className="form-help">Se non specificata, verrà usata la data/ora attuale</small>
            </div>
          </div>

          {/* Da chi / A chi */}
          <div className="form-group mb-4">
            <label className="form-label">
              {direzione === 'IN' ? 'Da chi' : 'A chi'} *
            </label>
            <div className="flex flex-col gap-3">
              <input
                type="text"
                value={daChiAChi}
                onChange={(e) => setDaChiAChi(e.target.value)}
                placeholder={
                  direzione === 'IN'
                    ? 'Indica mittente manualmente (facoltativo se selezioni un\'anagrafica)'
                    : 'Indica destinatario manualmente (facoltativo se selezioni un\'anagrafica)'
                }
                className="form-control"
                required={false}
                disabled={loading}
              />
              <AnagraficaAutocomplete
                value={direzione === 'IN' ? daChiAnagrafica : aChiAnagrafica}
                onChange={handleAnagraficaSelection}
                disabled={loading}
                helperText="Oppure seleziona un'anagrafica esistente"
              />
            </div>
            <small className="form-help">
              {direzione === 'IN'
                ? 'Persona o ente da cui proviene (testo libero o anagrafica)'
                : 'Persona o ente a cui viene consegnato (testo libero o anagrafica)'}
            </small>
          </div>

          {/* Data rientro prevista (solo per OUT) */}
          {direzione === 'OUT' && (
            <div className="form-group mb-4">
              <label className="form-label">Data rientro prevista</label>
              <input
                type="date"
                value={dataRientroPrevista}
                onChange={(e) => setDataRientroPrevista(e.target.value)}
                className="form-control"
              />
              <small className="form-help">Quando è previsto il rientro</small>
            </div>
          )}

          {/* Ubicazione */}
          <div className="form-group mb-4">
            <label className="form-label">Ubicazione</label>
            {ubicazioniError && (
              <div className="flex items-center justify-between gap-3 text-sm text-red-600 mb-2">
                <span>{ubicazioniError}</span>
                <button
                  type="button"
                  className="btn-secondary btn-sm"
                  onClick={() => void loadUbicazioni()}
                  disabled={ubicazioniLoading}
                >
                  {ubicazioniLoading ? 'Caricamento...' : 'Riprova'}
                </button>
              </div>
            )}
            <UbicazioneAutocomplete
              value={ubicazioneId ?? null}
              unitaFisiche={unitaFisiche}
              onChange={(value) => setUbicazioneId(value ?? undefined)}
              disabled={loading || ubicazioniLoading}
              placeholder={ubicazioniLoading ? 'Caricamento ubicazioni...' : 'Cerca per codice o percorso...'}
            />
            <small className="form-help">
              {ubicazioniLoading ? 'Caricamento unità fisiche...' : 'Unità fisica di archiviazione'}
            </small>
          </div>

          {/* Causale */}
          <div className="form-group mb-4">
            <label className="form-label">Causale</label>
            <input
              type="text"
              value={causale}
              onChange={(e) => setCausale(e.target.value)}
              placeholder="Es: Consegna documenti, Richiesta informazioni..."
              className="form-control"
            />
            <small className="form-help">Motivo della protocollazione</small>
          </div>

          {/* Note */}
          <div className="form-group mb-4">
            <label className="form-label">Note</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              placeholder="Note aggiuntive..."
              className="form-control"
            />
          </div>
        </form>

        {/* Footer */}
        <div className="border-t px-6 py-4 flex justify-end gap-3 bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            className="btn-secondary"
            disabled={loading}
          >
            Annulla
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Protocollazione in corso...' : 'Protocolla'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProtocolloModal;
