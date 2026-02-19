import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUnitaFisicheTree } from '@/api/archivioFisico';
import type { UnitaFisicaTreeNode } from '@/types/archivioFisico';
import { AddIcon } from '@/components/icons/Icons';
import './ArchivioPage.css';

interface TreeNodeProps {
  node: UnitaFisicaTreeNode;
  level: number;
  onNodeClick: (node: UnitaFisicaTreeNode) => void;
}

const TreeNode = ({ node, level, onNodeClick }: TreeNodeProps) => {
  const [isExpanded, setIsExpanded] = useState(level < 2); // Espandi i primi 2 livelli

  const hasChildren = node.children && node.children.length > 0;

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const handleClick = () => {
    onNodeClick(node);
  };

  const getTypeIcon = (tipo: string) => {
    const icons: Record<string, string> = {
      ufficio: '🏢',
      stanza: '🚪',
      scaffale: '📚',
      mobile: '🗄️',
      anta: '📂',
      ripiano: '📋',
      contenitore: '📦',
      cartellina: '📁',
    };
    return icons[tipo] || '📌';
  };

  return (
    <div className="tree-node">
      <div
        className={`tree-node-content ${!node.attivo ? 'inactive' : ''}`}
        style={{ paddingLeft: `${level * 20}px` }}
        onClick={handleClick}
      >
        {hasChildren && (
          <button
            className="expand-button"
            onClick={toggleExpand}
            aria-label={isExpanded ? 'Comprimi' : 'Espandi'}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        )}
        {!hasChildren && <span className="expand-placeholder"></span>}
        
        <span className="node-icon">{getTypeIcon(node.tipo)}</span>
        
        <div className="node-info">
          <div className="node-name">
            <span className="node-codice">{node.codice}</span>
            <span className="node-nome">{node.nome}</span>
          </div>
          <div className="node-meta">
            <span className="node-tipo">{node.tipo_display}</span>
            {node.archivio_fisso && (
              <span className="badge badge-archivio-fisso">Archivio Fisso</span>
            )}
            {!node.attivo && (
              <span className="badge badge-inactive">Non attivo</span>
            )}
          </div>
        </div>

        <div className="node-actions">
          <span className="node-path">{node.full_path}</span>
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div className="tree-node-children">
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onNodeClick={onNodeClick}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export function ArchivioPage() {
  const navigate = useNavigate();
  const [tree, setTree] = useState<UnitaFisicaTreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadTree();
  }, []);

  const loadTree = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getUnitaFisicheTree();
      setTree(data);
    } catch (err) {
      console.error('Error loading archivio tree:', err);
      setError('Errore nel caricamento della struttura archivio');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (node: UnitaFisicaTreeNode) => {
    // Naviga alla pagina di dettaglio dell'unità fisica
    navigate(`/archivio/unita/${node.id}`);
  };

  const filterTree = (nodes: UnitaFisicaTreeNode[], query: string): UnitaFisicaTreeNode[] => {
    if (!query.trim()) return nodes;

    const lowerQuery = query.toLowerCase();
    
    return nodes.reduce<UnitaFisicaTreeNode[]>((acc, node) => {
      const matchesSearch = 
        node.codice.toLowerCase().includes(lowerQuery) ||
        node.nome.toLowerCase().includes(lowerQuery) ||
        node.full_path.toLowerCase().includes(lowerQuery) ||
        node.tipo_display.toLowerCase().includes(lowerQuery);

      const filteredChildren = filterTree(node.children, query);

      if (matchesSearch || filteredChildren.length > 0) {
        acc.push({
          ...node,
          children: filteredChildren,
        });
      }

      return acc;
    }, []);
  };

  const filteredTree = filterTree(tree, searchQuery);

  if (loading) {
    return (
      <div className="archivio-page">
        <div className="page-header">
          <h1>Archivio Fisico</h1>
        </div>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Caricamento struttura archivio...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="archivio-page">
        <div className="page-header">
          <h1>Archivio Fisico</h1>
        </div>
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={loadTree} className="btn btn-primary">
            Riprova
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="archivio-page">
      <div className="page-header">
        <div className="header-left">
          <h1>Archivio Fisico</h1>
          <p className="subtitle">Struttura gerarchica delle unità di archiviazione</p>
        </div>
        <div className="header-right">
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/archivio-fisico/operazioni')}
          >
            Operazioni Archivio
          </button>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/archivio/unita/nuovo')}
          >
            <AddIcon size={18} />
            <span>Nuova Unità</span>
          </button>
        </div>
      </div>

      <div className="archivio-content">
        <div className="search-section">
          <input
            type="text"
            className="search-input"
            placeholder="Cerca per codice, nome, percorso o tipo..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button
              className="btn-clear-search"
              onClick={() => setSearchQuery('')}
              aria-label="Cancella ricerca"
            >
              ✕
            </button>
          )}
        </div>

        {filteredTree.length === 0 ? (
          <div className="empty-state">
            <p>
              {searchQuery
                ? 'Nessuna unità trovata con i criteri di ricerca'
                : 'Nessuna unità fisica configurata'}
            </p>
            {!searchQuery && (
              <button
                className="btn btn-primary"
                onClick={() => navigate('/archivio/unita/nuovo')}
              >
                <AddIcon size={18} />
                <span>Crea prima unità</span>
              </button>
            )}
          </div>
        ) : (
          <div className="tree-container">
            {filteredTree.map((node) => (
              <TreeNode
                key={node.id}
                node={node}
                level={0}
                onNodeClick={handleNodeClick}
              />
            ))}
          </div>
        )}
      </div>

      <div className="page-info">
        <div className="info-card">
          <h3>Legenda Tipi di Unità</h3>
          <div className="legend-items">
            <div className="legend-item">
              <span className="legend-icon">🏢</span>
              <span>Ufficio</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">🚪</span>
              <span>Stanza</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">📚</span>
              <span>Scaffale</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">🗄️</span>
              <span>Mobile</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">📂</span>
              <span>Anta</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">📋</span>
              <span>Ripiano</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">📦</span>
              <span>Contenitore</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon">📁</span>
              <span>Cartellina</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
