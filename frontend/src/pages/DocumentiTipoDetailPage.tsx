/**
 * Tipo Documento Detail Page
 * Mostra il dettaglio di un tipo documento con filtri dinamici basati sui suoi attributi
 */
import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { documentiApi } from '@/api/documenti';
import type { DocumentiTipo, AttributoDefinizione, Documento, DocumentoFilters } from '@/types/documento';
import { ArrowBackIcon, VisibilityIcon, DescriptionIcon } from '@/components/icons/Icons';
import { ClienteAutocomplete } from '@/components/ClienteAutocomplete';

const PAGE_SIZE = 20;

function parseScelte(scelte?: string): Array<{ value: string; label: string }> {
  if (!scelte) return [];
  return scelte
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => {
      const [value, label] = s.includes('|') ? s.split('|') : [s, s];
      return { value: value.trim(), label: label.trim() };
    });
}

function AttributoFiltro({
  attr,
  value,
  onChange,
}: {
  attr: AttributoDefinizione;
  value: string;
  onChange: (value: string) => void;
}) {
  if (attr.tipo_dato === 'bool') {
    return (
      <select className="form-control" value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Tutti</option>
        <option value="true">Sì</option>
        <option value="false">No</option>
      </select>
    );
  }
  if (attr.tipo_dato === 'choice') {
    return (
      <select className="form-control" value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Tutti</option>
        {parseScelte(attr.scelte).map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>
    );
  }
  if (attr.tipo_dato === 'date' || attr.tipo_dato === 'datetime') {
    return (
      <input
        type="date"
        className="form-control"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  if (attr.tipo_dato === 'int' || attr.tipo_dato === 'decimal') {
    return (
      <input
        type="number"
        className="form-control"
        value={value}
        step={attr.tipo_dato === 'decimal' ? '0.01' : '1'}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  return (
    <input
      type="text"
      className="form-control"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Valore esatto"
    />
  );
}

export default function DocumentiTipoDetailPage() {
  const { codice } = useParams<{ codice: string }>();
  const navigate = useNavigate();

  const [tipo, setTipo] = useState<DocumentiTipo | null>(null);
  const [loadingTipo, setLoadingTipo] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [documenti, setDocumenti] = useState<Documento[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loadingDocumenti, setLoadingDocumenti] = useState(false);
  const [page, setPage] = useState(1);

  // Filtri standard
  const [clienteId, setClienteId] = useState<number | null>(null);
  const [stato, setStato] = useState('');
  const [digitale, setDigitale] = useState('');
  const [dataDa, setDataDa] = useState('');
  const [dataA, setDataA] = useState('');

  // Filtri dinamici per attributo (codice -> valore testuale)
  const [attrFiltri, setAttrFiltri] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!codice) return;
    let cancelled = false;
    setLoadingTipo(true);
    documentiApi.listTipi()
      .then((tipi) => {
        if (cancelled) return;
        const found = tipi.find((t) => t.codice === codice) || null;
        setTipo(found);
        setNotFound(!found);
      })
      .catch((err) => {
        console.error('Errore nel caricamento del tipo documento:', err);
        setNotFound(true);
      })
      .finally(() => { if (!cancelled) setLoadingTipo(false); });
    return () => { cancelled = true; };
  }, [codice]);

  const attributi = useMemo(
    () => [...(tipo?.attributi || [])].sort((a, b) => a.ordine - b.ordine),
    [tipo]
  );

  const handleAttrChange = (attrCodice: string, value: string) => {
    setAttrFiltri((prev) => ({ ...prev, [attrCodice]: value }));
    setPage(1);
  };

  const resetFiltri = () => {
    setClienteId(null);
    setStato('');
    setDigitale('');
    setDataDa('');
    setDataA('');
    setAttrFiltri({});
    setPage(1);
  };

  const filtriAttivi =
    clienteId || stato || digitale || dataDa || dataA || Object.values(attrFiltri).some((v) => v);

  const filters: DocumentoFilters = useMemo(() => ({
    tipo: tipo?.id,
    cliente: clienteId || undefined,
    stato: stato || undefined,
    digitale: digitale === '' ? undefined : digitale === 'true',
    data_da: dataDa || undefined,
    data_a: dataA || undefined,
    ordering: '-data_documento',
    attributi: attrFiltri,
  }), [tipo, clienteId, stato, digitale, dataDa, dataA, attrFiltri]);
  const filtersKey = JSON.stringify(filters);

  useEffect(() => {
    if (!tipo) return;
    let cancelled = false;
    setLoadingDocumenti(true);
    documentiApi.list(filters, page, PAGE_SIZE)
      .then((res) => {
        if (cancelled) return;
        setDocumenti(res.results);
        setTotalCount(res.count);
      })
      .catch((err) => console.error('Errore nel caricamento dei documenti del tipo:', err))
      .finally(() => { if (!cancelled) setLoadingDocumenti(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tipo, filtersKey, page]);

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  const getAttrValue = (doc: Documento, attrCodice: string) => {
    const found = doc.attributi?.find((a) => a.definizione_detail?.codice === attrCodice);
    if (!found || found.valore === null || found.valore === undefined) return '-';
    if (typeof found.valore === 'boolean') return found.valore ? 'Sì' : 'No';
    return String(found.valore);
  };

  if (loadingTipo) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p>Caricamento tipo documento...</p>
        </div>
      </div>
    );
  }

  if (notFound || !tipo) {
    return (
      <div className="page-container">
        <div className="alert alert-error">Tipo documento non trovato.</div>
        <button onClick={() => navigate('/documenti/tipi')} className="btn-secondary">
          <ArrowBackIcon size={18} />
          <span>Torna ai tipi documento</span>
        </button>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <DescriptionIcon size={28} />
            {tipo.nome}
          </h1>
          <p style={{ color: '#6c757d', marginTop: '0.25rem' }}>
            Codice: <code>{tipo.codice}</code>
            {tipo.estensioni_permesse && <> · Estensioni permesse: {tipo.estensioni_permesse}</>}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link to={`/help/documenti/${tipo.codice}`} className="btn-secondary">
            Guida
          </Link>
          <button onClick={() => navigate('/documenti/tipi')} className="btn-secondary">
            <ArrowBackIcon size={18} />
            <span>Tipi Documento</span>
          </button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>Filtri</h2>
        <div className="filters-grid">
          <div className="form-group">
            <label>Cliente</label>
            <ClienteAutocomplete
              value={clienteId}
              onChange={(id) => { setClienteId(id); setPage(1); }}
              placeholder="Tutti i clienti"
            />
          </div>
          <div className="form-group">
            <label>Stato</label>
            <select className="form-control" value={stato} onChange={(e) => { setStato(e.target.value); setPage(1); }}>
              <option value="">Tutti gli stati</option>
              <option value="bozza">Bozza</option>
              <option value="definitivo">Definitivo</option>
              <option value="archiviato">Archiviato</option>
              <option value="uscito">Uscito</option>
              <option value="consegnato">Consegnato</option>
              <option value="scaricato">Scaricato</option>
            </select>
          </div>
          <div className="form-group">
            <label>Formato</label>
            <select className="form-control" value={digitale} onChange={(e) => { setDigitale(e.target.value); setPage(1); }}>
              <option value="">Tutti i formati</option>
              <option value="true">Digitale</option>
              <option value="false">Cartaceo</option>
            </select>
          </div>
          <div className="form-group">
            <label>Data Da</label>
            <input type="date" className="form-control" value={dataDa} onChange={(e) => { setDataDa(e.target.value); setPage(1); }} />
          </div>
          <div className="form-group">
            <label>Data A</label>
            <input type="date" className="form-control" value={dataA} onChange={(e) => { setDataA(e.target.value); setPage(1); }} />
          </div>

          {attributi.map((attr) => (
            <div className="form-group" key={attr.id}>
              <label>{attr.nome}</label>
              <AttributoFiltro
                attr={attr}
                value={attrFiltri[attr.codice] || ''}
                onChange={(value) => handleAttrChange(attr.codice, value)}
              />
            </div>
          ))}
        </div>

        {filtriAttivi && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
            <button onClick={resetFiltri} className="btn-secondary">Reset Filtri</button>
          </div>
        )}
      </div>

      <div className="card">
        <div style={{ marginBottom: '1rem', color: '#6c757d' }}>
          {loadingDocumenti ? 'Caricamento...' : `Totale: ${totalCount} documenti`}
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Codice</th>
                <th>Descrizione</th>
                <th>Cliente</th>
                <th>Data</th>
                <th>Stato</th>
                {attributi.map((attr) => (
                  <th key={attr.id}>{attr.nome}</th>
                ))}
                <th style={{ width: '80px' }}>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {documenti.length === 0 ? (
                <tr>
                  <td colSpan={5 + attributi.length + 1} style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
                    Nessun documento trovato
                  </td>
                </tr>
              ) : (
                documenti.map((doc) => (
                  <tr key={doc.id}>
                    <td><strong>{doc.codice}</strong></td>
                    <td>{doc.descrizione}</td>
                    <td>{doc.cliente_detail?.anagrafica_display || '-'}</td>
                    <td>{new Date(doc.data_documento).toLocaleDateString('it-IT')}</td>
                    <td><span className="badge">{doc.stato}</span></td>
                    {attributi.map((attr) => (
                      <td key={attr.id}>{getAttrValue(doc, attr.codice)}</td>
                    ))}
                    <td>
                      <button
                        onClick={() => navigate(`/documenti/${doc.id}`)}
                        className="btn-icon"
                        title="Visualizza documento"
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
        {totalPages > 1 && (
          <div className="pagination">
            <button onClick={() => setPage((p) => p - 1)} disabled={page === 1} className="btn-secondary">
              Precedente
            </button>
            <span>Pagina {page} di {totalPages}</span>
            <button onClick={() => setPage((p) => p + 1)} disabled={page === totalPages} className="btn-secondary">
              Successiva
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
