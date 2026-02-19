/**
 * Dialog per collegare documenti non fascicolati a un fascicolo
 */
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  Paper,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import { documentiApi } from '@/api/documenti';
import type { Documento } from '@/types/documento';

interface CollegaDocumentiDialogProps {
  open: boolean;
  onClose: () => void;
  fascicoloId: number;
  clienteId: number;
  onSuccess: () => void;
}

export default function CollegaDocumentiDialog({
  open,
  onClose,
  fascicoloId,
  clienteId,
  onSuccess,
}: CollegaDocumentiDialogProps) {
  const [documentiDisponibili, setDocumentiDisponibili] = useState<Documento[]>([]);
  const [selectedDocumenti, setSelectedDocumenti] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Carica documenti non fascicolati dello stesso cliente
  useEffect(() => {
    if (!open) return;

    const loadDocumenti = async () => {
      setLoading(true);
      setError(null);
      try {
        // Filtro per cliente e fascicolo null (non fascicolati)
        const response = await documentiApi.list({
          cliente: clienteId,
          fascicolo__isnull: true, // Documenti senza fascicolo
        });
        setDocumentiDisponibili(response.results);
        setSelectedDocumenti(new Set()); // Reset selezione
      } catch (err) {
        console.error('Errore nel caricamento dei documenti:', err);
        setError('Errore nel caricamento dei documenti disponibili');
      } finally {
        setLoading(false);
      }
    };

    loadDocumenti();
  }, [open, clienteId]);

  const handleToggleDocumento = (documentoId: number) => {
    setSelectedDocumenti((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(documentoId)) {
        newSet.delete(documentoId);
      } else {
        newSet.add(documentoId);
      }
      return newSet;
    });
  };

  const handleToggleAll = () => {
    if (selectedDocumenti.size === documentiDisponibili.length) {
      // Deseleziona tutto
      setSelectedDocumenti(new Set());
    } else {
      // Seleziona tutto
      setSelectedDocumenti(new Set(documentiDisponibili.map((d) => d.id)));
    }
  };

  const handleCollega = async () => {
    if (selectedDocumenti.size === 0) {
      setError('Seleziona almeno un documento');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Aggiorna ogni documento selezionato collegandolo al fascicolo
      const promises = Array.from(selectedDocumenti).map((docId) =>
        documentiApi.update(docId, { fascicolo: fascicoloId })
      );

      await Promise.all(promises);

      // Chiudi il dialog e notifica il successo
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Errore nel collegamento dei documenti:', err);
      setError('Errore nel collegamento dei documenti al fascicolo');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (!saving) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>Collega Documenti al Fascicolo</DialogTitle>
      <DialogContent>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
            <CircularProgress />
          </div>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : documentiDisponibili.length === 0 ? (
          <Typography color="text.secondary" sx={{ py: 3, textAlign: 'center' }}>
            Nessun documento non fascicolato disponibile per questo cliente.
          </Typography>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Seleziona i documenti da collegare al fascicolo. Sono mostrati solo i
              documenti dello stesso cliente che non sono già collegati a un fascicolo.
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={
                          documentiDisponibili.length > 0 &&
                          selectedDocumenti.size === documentiDisponibili.length
                        }
                        indeterminate={
                          selectedDocumenti.size > 0 &&
                          selectedDocumenti.size < documentiDisponibili.length
                        }
                        onChange={handleToggleAll}
                      />
                    </TableCell>
                    <TableCell>Codice</TableCell>
                    <TableCell>Descrizione</TableCell>
                    <TableCell>Tipo</TableCell>
                    <TableCell>Data</TableCell>
                    <TableCell>Stato</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {documentiDisponibili.map((doc) => (
                    <TableRow
                      key={doc.id}
                      hover
                      onClick={() => handleToggleDocumento(doc.id)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell padding="checkbox">
                        <Checkbox checked={selectedDocumenti.has(doc.id)} />
                      </TableCell>
                      <TableCell>{doc.codice}</TableCell>
                      <TableCell>{doc.descrizione}</TableCell>
                      <TableCell>
                        {doc.tipo_detail?.nome || doc.tipo || '-'}
                      </TableCell>
                      <TableCell>
                        {new Date(doc.data_documento).toLocaleDateString('it-IT')}
                      </TableCell>
                      <TableCell>
                        <span
                          style={{
                            padding: '0.25rem 0.5rem',
                            borderRadius: '0.25rem',
                            fontSize: '0.75rem',
                            backgroundColor:
                              doc.stato === 'definitivo' ? '#d4edda' : '#fff3cd',
                            color: doc.stato === 'definitivo' ? '#155724' : '#856404',
                          }}
                        >
                          {doc.stato}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {selectedDocumenti.size > 0 && (
              <Typography variant="body2" sx={{ mt: 2 }}>
                {selectedDocumenti.size} documento/i selezionato/i
              </Typography>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={saving}>
          Annulla
        </Button>
        <Button
          onClick={handleCollega}
          variant="contained"
          disabled={
            saving || selectedDocumenti.size === 0 || documentiDisponibili.length === 0
          }
        >
          {saving ? <CircularProgress size={20} /> : 'Collega'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
