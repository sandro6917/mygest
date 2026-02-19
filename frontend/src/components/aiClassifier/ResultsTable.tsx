/**
 * Tabella risultati classificazione con selezione per import
 */
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Checkbox,
  IconButton,
  Tooltip,
  Typography,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircle as ImportedIcon,
  OpenInNew as ViewDocIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useResults } from '@/hooks/useAiClassifier';
import type { ClassificationResult, ConfidenceLevel } from '@/types/aiClassifier';

const getConfidenceColor = (level: ConfidenceLevel) => {
  switch (level) {
    case 'high':
      return 'success';
    case 'medium':
      return 'warning';
    case 'low':
      return 'error';
    default:
      return 'default';
  }
};

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

interface ResultsTableProps {
  jobId?: number;
  onSelectionChange?: (selectedIds: number[]) => void;
  selectable?: boolean;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({
  jobId,
  onSelectionChange,
  selectable = false,
}) => {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const { data, isLoading } = useResults(jobId ? { job: jobId } : undefined);

  const handleSelectAll = (checked: boolean) => {
    if (!data) return;
    
    const newSelection = checked
      ? data.results.filter((r) => !r.imported).map((r) => r.id)
      : [];
    
    setSelectedIds(newSelection);
    onSelectionChange?.(newSelection);
  };

  const handleSelectOne = (id: number, checked: boolean) => {
    const newSelection = checked
      ? [...selectedIds, id]
      : selectedIds.filter((selectedId) => selectedId !== id);
    
    setSelectedIds(newSelection);
    onSelectionChange?.(newSelection);
  };

  if (isLoading) {
    return <LinearProgress />;
  }

  if (!data || data.results.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          Nessun risultato trovato
        </Typography>
      </Paper>
    );
  }

  const selectableResults = data.results.filter((r) => !r.imported);
  const allSelected =
    selectableResults.length > 0 &&
    selectableResults.every((r) => selectedIds.includes(r.id));
  const someSelected =
    selectedIds.length > 0 && !allSelected;

  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            {selectable && (
              <TableCell padding="checkbox">
                <Checkbox
                  checked={allSelected}
                  indeterminate={someSelected}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  disabled={selectableResults.length === 0}
                />
              </TableCell>
            )}
            <TableCell>File</TableCell>
            <TableCell align="center">Tipo</TableCell>
            <TableCell align="center">Confidenza</TableCell>
            <TableCell align="center">Metodo</TableCell>
            <TableCell>Cliente Suggerito</TableCell>
            <TableCell align="right">Dimensione</TableCell>
            <TableCell align="center">Stato</TableCell>
            <TableCell align="center">Azioni</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.results.map((result: ClassificationResult) => (
            <TableRow
              key={result.id}
              hover
              selected={selectedIds.includes(result.id)}
            >
              {selectable && (
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedIds.includes(result.id)}
                    onChange={(e) => handleSelectOne(result.id, e.target.checked)}
                    disabled={result.imported}
                  />
                </TableCell>
              )}

              <TableCell>
                <Tooltip title={result.file_path}>
                  <Typography variant="body2" noWrap maxWidth={250}>
                    {result.file_name}
                  </Typography>
                </Tooltip>
              </TableCell>

              <TableCell align="center">
                <Chip
                  label={result.predicted_type_display}
                  size="small"
                  variant="outlined"
                />
              </TableCell>

              <TableCell align="center">
                <Chip
                  label={`${(result.confidence_score * 100).toFixed(0)}%`}
                  color={getConfidenceColor(result.confidence_level)}
                  size="small"
                />
              </TableCell>

              <TableCell align="center">
                <Chip
                  label={result.classification_method === 'llm' ? 'AI' : 'Regole'}
                  size="small"
                  color={result.classification_method === 'llm' ? 'primary' : 'default'}
                />
              </TableCell>

              <TableCell>
                {result.suggested_cliente_nome ? (
                  <Typography variant="body2" noWrap maxWidth={200}>
                    {result.suggested_cliente_nome}
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    -
                  </Typography>
                )}
              </TableCell>

              <TableCell align="right">
                <Typography variant="body2">
                  {formatFileSize(result.file_size)}
                </Typography>
              </TableCell>

              <TableCell align="center">
                {result.imported ? (
                  <Tooltip title={`Documento: ${result.documento_codice}`}>
                    <Chip
                      icon={<ImportedIcon />}
                      label="Importato"
                      color="success"
                      size="small"
                    />
                  </Tooltip>
                ) : (
                  <Chip label="Non importato" size="small" variant="outlined" />
                )}
              </TableCell>

              <TableCell align="center">
                <Box display="flex" gap={0.5} justifyContent="center">
                  <Tooltip title="Metadata estratti">
                    <IconButton size="small" color="info">
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>

                  {result.imported && result.documento && (
                    <Tooltip title="Apri documento">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() =>
                          window.open(`/documenti/${result.documento}`, '_blank')
                        }
                      >
                        <ViewDocIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selectable && selectedIds.length > 0 && (
        <Box
          sx={{
            p: 2,
            borderTop: 1,
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            backgroundColor: 'action.hover',
          }}
        >
          <Typography variant="body2" fontWeight="bold">
            {selectedIds.length} risultati selezionati
          </Typography>
        </Box>
      )}
    </TableContainer>
  );
};
