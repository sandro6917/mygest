/**
 * Componente per visualizzare l'albero delle unità fisiche
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Typography,
  Chip,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Archive as ArchiveIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { toast } from 'react-toastify';

import { getUnitaFisicheTree } from '../../api/archivioFisico';
import type { UnitaFisicaTreeNode } from '../../types/archivioFisico';

interface TreeNodeProps {
  node: UnitaFisicaTreeNode;
  level: number;
  onSelect?: (node: UnitaFisicaTreeNode) => void;
  selectedId?: number;
}

const TreeNode: React.FC<TreeNodeProps> = ({ node, level, onSelect, selectedId }) => {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedId === node.id;

  const handleToggle = () => {
    if (hasChildren) {
      setExpanded(!expanded);
    }
  };

  const handleSelect = () => {
    if (onSelect) {
      onSelect(node);
    }
  };

  return (
    <>
      <ListItem
        sx={{
          pl: level * 3,
          cursor: 'pointer',
          bgcolor: isSelected ? 'action.selected' : 'transparent',
          '&:hover': {
            bgcolor: 'action.hover',
          },
        }}
      >
        <ListItemIcon sx={{ minWidth: 36 }}>
          {hasChildren ? (
            <IconButton size="small" onClick={handleToggle}>
              {expanded ? <ExpandMoreIcon /> : <ChevronRightIcon />}
            </IconButton>
          ) : (
            <Box sx={{ width: 24, height: 24 }} />
          )}
        </ListItemIcon>
        
        <ListItemIcon sx={{ minWidth: 40 }}>
          {hasChildren ? (
            expanded ? <FolderOpenIcon color="primary" /> : <FolderIcon />
          ) : (
            <ArchiveIcon color="action" />
          )}
        </ListItemIcon>
        
        <ListItemText
          primary={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} onClick={handleSelect}>
              <Typography variant="body1" component="span">
                {node.nome}
              </Typography>
              <Chip label={node.codice} size="small" variant="outlined" />
              <Chip label={node.tipo_display} size="small" color="default" />
              {node.archivio_fisso && (
                <Chip label="Fisso" size="small" color="warning" />
              )}
            </Box>
          }
          secondary={node.full_path}
        />
      </ListItem>
      
      {hasChildren && (
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {node.children.map((child) => (
              <TreeNode
                key={child.id}
                node={child}
                level={level + 1}
                onSelect={onSelect}
                selectedId={selectedId}
              />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
};

interface UnitaFisicaTreeViewProps {
  onSelectNode?: (node: UnitaFisicaTreeNode) => void;
  selectedNodeId?: number;
  showAddButton?: boolean;
  onAdd?: () => void;
}

const UnitaFisicaTreeView: React.FC<UnitaFisicaTreeViewProps> = ({
  onSelectNode,
  selectedNodeId,
  showAddButton = false,
  onAdd,
}) => {
  const [tree, setTree] = useState<UnitaFisicaTreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTree = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getUnitaFisicheTree();
      setTree(data);
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento dell\'albero');
      toast.error('Errore nel caricamento dell\'albero');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTree();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Struttura Archivio Fisico
          </Typography>
          {showAddButton && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<AddIcon />}
              onClick={onAdd}
            >
              Nuova Unità
            </Button>
          )}
        </Box>
        
        {tree.length === 0 ? (
          <Alert severity="info">Nessuna unità fisica trovata</Alert>
        ) : (
          <List>
            {tree.map((node) => (
              <TreeNode
                key={node.id}
                node={node}
                level={0}
                onSelect={onSelectNode}
                selectedId={selectedNodeId}
              />
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default UnitaFisicaTreeView;
