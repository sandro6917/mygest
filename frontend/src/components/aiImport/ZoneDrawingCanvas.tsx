/**
 * Componente Canvas per disegno zone di estrazione
 */
import React, { useRef, useState, useEffect } from 'react';
import { Box, Paper, IconButton, Tooltip, Typography } from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  RestartAlt as ResetIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import type { ExtractionTemplateZone } from '@/types/aiImport';

interface ZoneDrawingCanvasProps {
  imageUrl: string;
  imageWidth: number;
  imageHeight: number;
  zones: ExtractionTemplateZone[];
  selectedZoneId?: number;
  onZoneCreate?: (zone: Omit<ExtractionTemplateZone, 'id' | 'absolute_coordinates'>) => void;
  onZoneSelect?: (zoneId: number | null) => void;
  onZoneDelete?: (zoneId: number) => void;
  readOnly?: boolean;
}

interface DrawingRect {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

export const ZoneDrawingCanvas: React.FC<ZoneDrawingCanvasProps> = ({
  imageUrl,
  imageWidth,
  imageHeight,
  zones,
  selectedZoneId,
  onZoneCreate,
  onZoneSelect,
  onZoneDelete,
  readOnly = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [zoom, setZoom] = useState(1);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentRect, setCurrentRect] = useState<DrawingRect | null>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);

  // Carica immagine
  useEffect(() => {
    console.log('🖼️ ZoneDrawingCanvas: Caricamento immagine', { imageUrl });
    const img = new Image();
    img.crossOrigin = 'anonymous'; // Per CORS
    img.src = imageUrl;
    img.onload = () => {
      console.log('✅ Immagine caricata con successo', { width: img.width, height: img.height });
      setImage(img);
    };
    img.onerror = (error) => {
      console.error('❌ Errore caricamento immagine:', error, { imageUrl });
    };
  }, [imageUrl]);

  // Disegna canvas
  useEffect(() => {
    if (!canvasRef.current || !image) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Disegna immagine
    ctx.drawImage(image, 0, 0, imageWidth * zoom, imageHeight * zoom);

    // Disegna zone esistenti
    zones.forEach((zone) => {
      // Converti percentuali in coordinate assolute
      const xPercent = Number(zone.x_percent);
      const yPercent = Number(zone.y_percent);
      const widthPercent = Number(zone.width_percent);
      const heightPercent = Number(zone.height_percent);
      
      const x = (xPercent / 100) * canvas.width;
      const y = (yPercent / 100) * canvas.height;
      const width = (widthPercent / 100) * canvas.width;
      const height = (heightPercent / 100) * canvas.height;

      // Evidenzia zona selezionata
      const isSelected = zone.id === selectedZoneId;
      
      ctx.strokeStyle = isSelected ? '#1976d2' : zone.obbligatorio ? '#f44336' : '#4caf50';
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.strokeRect(x, y, width, height);

      // Background semi-trasparente
      ctx.fillStyle = isSelected ? 'rgba(25, 118, 210, 0.1)' : 'rgba(76, 175, 80, 0.05)';
      ctx.fillRect(x, y, width, height);

      // Label
      ctx.fillStyle = '#000';
      ctx.font = '12px Arial';
      ctx.fillText(zone.etichetta, x + 5, y + 15);
    });

    // Disegna rettangolo corrente (durante disegno)
    if (currentRect && !readOnly) {
      const { startX, startY, endX, endY } = currentRect;
      const x = Math.min(startX, endX);
      const y = Math.min(startY, endY);
      const width = Math.abs(endX - startX);
      const height = Math.abs(endY - startY);

      ctx.strokeStyle = '#ff9800';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(x, y, width, height);
      ctx.setLineDash([]);

      ctx.fillStyle = 'rgba(255, 152, 0, 0.1)';
      ctx.fillRect(x, y, width, height);
    }
  }, [image, imageWidth, imageHeight, zoom, zones, selectedZoneId, currentRect, readOnly]);

  // Mouse handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (readOnly) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Verifica se click su zona esistente
    const clickedZone = zones.find((zone) => {
      // Converti percentuali in coordinate assolute
      const xPercent = Number(zone.x_percent);
      const yPercent = Number(zone.y_percent);
      const widthPercent = Number(zone.width_percent);
      const heightPercent = Number(zone.height_percent);
      
      const zoneX = (xPercent / 100) * canvas.width;
      const zoneY = (yPercent / 100) * canvas.height;
      const zoneWidth = (widthPercent / 100) * canvas.width;
      const zoneHeight = (heightPercent / 100) * canvas.height;

      return x >= zoneX && x <= zoneX + zoneWidth && y >= zoneY && y <= zoneY + zoneHeight;
    });

    if (clickedZone) {
      onZoneSelect?.(clickedZone.id);
    } else {
      onZoneSelect?.(null);
      setIsDrawing(true);
      setCurrentRect({ startX: x, startY: y, endX: x, endY: y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || readOnly) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setCurrentRect((prev) => (prev ? { ...prev, endX: x, endY: y } : null));
  };

  const handleMouseUp = () => {
    if (!isDrawing || !currentRect || readOnly) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const { startX, startY, endX, endY } = currentRect;
    const x = Math.min(startX, endX);
    const y = Math.min(startY, endY);
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);

    // Ignora zone troppo piccole
    if (width < 20 || height < 10) {
      setIsDrawing(false);
      setCurrentRect(null);
      return;
    }

    // Converti in percentuali
    const xPercent = (x / canvas.width) * 100;
    const yPercent = (y / canvas.height) * 100;
    const widthPercent = (width / canvas.width) * 100;
    const heightPercent = (height / canvas.height) * 100;

    // Crea nuova zona (prompt utente per dettagli)
    if (onZoneCreate) {
      const nomeCampo = prompt('Nome campo (es. "codice_fiscale_datore"):');
      if (!nomeCampo) {
        setIsDrawing(false);
        setCurrentRect(null);
        return;
      }

      const etichetta = prompt('Etichetta (es. "Codice Fiscale Datore di Lavoro"):') || nomeCampo;
      const tipoDato = prompt('Tipo dato (text, codice_fiscale, date, etc.):', 'text') || 'text';
      const obbligatorio = confirm('Campo obbligatorio?');

      onZoneCreate({
        nome_campo: nomeCampo,
        etichetta: etichetta,
        x_percent: parseFloat(xPercent.toFixed(2)),
        y_percent: parseFloat(yPercent.toFixed(2)),
        width_percent: parseFloat(widthPercent.toFixed(2)),
        height_percent: parseFloat(heightPercent.toFixed(2)),
        tipo_dato: tipoDato as any,
        obbligatorio: obbligatorio,
        ordine: zones.length + 1,
      });
    }

    setIsDrawing(false);
    setCurrentRect(null);
  };

  // Zoom handlers
  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.2, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.2, 0.5));
  const handleResetZoom = () => setZoom(1);

  const canvasWidth = imageWidth * zoom;
  const canvasHeight = imageHeight * zoom;

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">
          Disegna Zone di Estrazione {readOnly && '(Solo Lettura)'}
        </Typography>
        
        <Box display="flex" gap={1}>
          <Tooltip title="Zoom In">
            <IconButton size="small" onClick={handleZoomIn}>
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom Out">
            <IconButton size="small" onClick={handleZoomOut}>
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Reset Zoom">
            <IconButton size="small" onClick={handleResetZoom}>
              <ResetIcon />
            </IconButton>
          </Tooltip>
          {selectedZoneId && !readOnly && (
            <Tooltip title="Elimina Zona Selezionata">
              <IconButton
                size="small"
                color="error"
                onClick={() => onZoneDelete?.(selectedZoneId)}
              >
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      <Box
        ref={containerRef}
        sx={{
          border: '2px solid #ccc',
          borderRadius: 1,
          overflow: 'auto',
          maxHeight: '600px',
          cursor: readOnly ? 'default' : 'crosshair',
        }}
      >
        <canvas
          ref={canvasRef}
          width={canvasWidth}
          height={canvasHeight}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => {
            setIsDrawing(false);
            setCurrentRect(null);
          }}
          style={{ display: 'block' }}
        />
      </Box>

      <Box mt={2}>
        <Typography variant="caption" color="text.secondary">
          {readOnly
            ? 'Clicca su una zona per selezionarla'
            : 'Clicca e trascina per creare una nuova zona. Clicca su zona esistente per selezionarla.'}
        </Typography>
      </Box>
    </Paper>
  );
};
