import { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { isAxiosError } from 'axios';
import { apiClient } from '../api/client';
import { 
  UploadIcon, 
  DownloadIcon, 
  CheckCircleIcon, 
  WarningIcon, 
  InfoIcon, 
  AnagraficheIcon,
  VisibilityIcon,
  ArrowBackIcon
} from '../components/icons/Icons';

interface ImportReport {
  totale: number;
  num_importate: number;
  num_scartate: number;
  importate: Array<{
    riga: number;
    nome: string;
    codice_fiscale: string;
    id: number;
  }>;
  scartate: Array<{
    riga: number;
    dati: string;
    motivi: string[];
  }>;
}

export function AnagraficheImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setReport(null);
      setError(null);
    }
  };

  const handleDownloadExample = async () => {
    try {
      const response = await apiClient.get('/anagrafiche/facsimile_csv/', {
        responseType: 'blob',
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'facsimile_anagrafiche.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading example:', err);
      setError('Errore durante il download del file di esempio');
    }
  };

  const handleImport = async () => {
    if (!file) {
      setError('Seleziona un file CSV da importare');
      return;
    }

    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post<ImportReport>(
        '/anagrafiche/import_csv/',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setReport(response.data);
      
      // Reset file input
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setError(err.response?.data?.error || 'Errore durante l\'importazione');
      } else {
        setError('Errore durante l\'importazione');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-fluid">
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex align-items-center justify-content-between">
            <div className="d-flex align-items-center gap-2">
              <AnagraficheIcon size={32} />
              <h1 className="mb-0">Importazione Anagrafiche da CSV</h1>
            </div>
            <Link to="/anagrafiche" className="btn btn-outline-secondary">
              <ArrowBackIcon className="me-2" />
              Torna alle Anagrafiche
            </Link>
          </div>
        </div>
      </div>

      {/* Istruzioni */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title d-flex align-items-center gap-2">
                <InfoIcon />
                Istruzioni
              </h5>
              <p>
                Scarica il file CSV di esempio, compilalo con i tuoi dati e caricalo per importare le anagrafiche.
              </p>
              <button
                onClick={handleDownloadExample}
                className="btn btn-outline-primary"
              >
                <DownloadIcon className="me-2" />
                Scarica Fac-simile CSV
              </button>

              <div className="alert alert-info mt-3 mb-0">
                <strong>Campi obbligatori:</strong>
                <ul className="mb-0 mt-2">
                  <li><strong>tipo</strong>: PF (Persona Fisica) o PG (Persona Giuridica)</li>
                  <li><strong>codice_fiscale</strong>: codice fiscale (16 caratteri per PF, 11 per PG)</li>
                  <li>Per <strong>PF</strong>: nome e cognome</li>
                  <li>Per <strong>PG</strong>: ragione_sociale</li>
                </ul>
              </div>

              <div className="alert alert-warning mt-3 mb-0">
                <strong>Note:</strong>
                <ul className="mb-0 mt-2">
                  <li>Il file deve essere in formato CSV con separatore <code>;</code> (punto e virgola)</li>
                  <li>Encoding: UTF-8 o Latin-1</li>
                  <li>Non verranno importate righe con codice fiscale, P.IVA o PEC già esistenti</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Form Upload */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Carica il file CSV</h5>
              <div className="mb-3">
                <label htmlFor="csvFile" className="form-label">
                  Seleziona file CSV
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="form-control"
                  id="csvFile"
                  accept=".csv"
                  onChange={handleFileChange}
                  disabled={loading}
                />
                {file && (
                  <div className="form-text text-success">
                    File selezionato: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                  </div>
                )}
              </div>
              <button
                onClick={handleImport}
                className="btn btn-primary"
                disabled={!file || loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Importazione in corso...
                  </>
                ) : (
                  <>
                    <UploadIcon className="me-2" />
                    Importa Anagrafiche
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Errori */}
      {error && (
        <div className="row mb-4">
          <div className="col-12">
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              <WarningIcon className="me-2" />
              {error}
              <button
                type="button"
                className="btn-close"
                onClick={() => setError(null)}
                aria-label="Close"
              ></button>
            </div>
          </div>
        </div>
      )}

      {/* Report */}
      {report && (
        <div className="row">
          <div className="col-12">
            <div className="card">
              <div className="card-header bg-primary text-white">
                <h5 className="mb-0">
                  <InfoIcon className="me-2" />
                  Report di Importazione
                </h5>
              </div>
              <div className="card-body">
                {/* Statistiche */}
                <div className="row text-center mb-4">
                  <div className="col-md-4">
                    <div className="card border-secondary">
                      <div className="card-body">
                        <h3 className="display-4">{report.totale}</h3>
                        <p className="text-muted mb-0">Righe totali</p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="card border-success">
                      <div className="card-body">
                        <h3 className="display-4 text-success">{report.num_importate}</h3>
                        <p className="text-muted mb-0">Importate</p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="card border-warning">
                      <div className="card-body">
                        <h3 className="display-4 text-warning">{report.num_scartate}</h3>
                        <p className="text-muted mb-0">Scartate</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Anagrafiche importate */}
                {report.importate.length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-success">
                      <CheckCircleIcon className="me-2" />
                      Anagrafiche importate con successo ({report.num_importate})
                    </h5>
                    <div className="table-responsive">
                      <table className="table table-sm table-striped table-hover">
                        <thead className="table-success">
                          <tr>
                            <th>Riga CSV</th>
                            <th>Nome/Ragione Sociale</th>
                            <th>Codice Fiscale</th>
                            <th>Azioni</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.importate.map((item) => (
                            <tr key={item.riga}>
                              <td>{item.riga}</td>
                              <td>{item.nome}</td>
                              <td><code>{item.codice_fiscale}</code></td>
                              <td>
                                <Link
                                  to={`/anagrafiche/${item.id}`}
                                  className="btn btn-sm btn-outline-primary"
                                  title="Visualizza anagrafica"
                                >
                                  <VisibilityIcon className="me-1" />
                                  Dettagli
                                </Link>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Righe scartate */}
                {report.scartate.length > 0 && (
                  <div>
                    <h5 className="text-warning">
                      <WarningIcon className="me-2" />
                      Righe scartate ({report.num_scartate})
                    </h5>
                    <div className="table-responsive">
                      <table className="table table-sm table-striped">
                        <thead className="table-warning">
                          <tr>
                            <th>Riga CSV</th>
                            <th>Dati</th>
                            <th>Motivi dello scarto</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.scartate.map((item, index) => (
                            <tr key={index}>
                              <td>{item.riga}</td>
                              <td>{item.dati}</td>
                              <td>
                                <ul className="mb-0 list-unstyled text-danger">
                                  {item.motivi.map((motivo, idx) => (
                                    <li key={idx}>
                                      ✗ {motivo}
                                    </li>
                                  ))}
                                </ul>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
