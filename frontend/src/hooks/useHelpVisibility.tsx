/**
 * Hook React per gestire la visibilità degli help in base ai permessi utente
 */
import { useMemo } from 'react';
import type { DocumentiTipo } from '@/types/documento';

export interface HelpVisibilityInfo {
  isVisible: boolean;
  status: 'completo' | 'parziale' | 'da_completare' | 'vuoto' | 'non_disponibile';
  message?: string;
}

/**
 * Determina se un help è visibile per l'utente corrente
 */
export function useHelpVisibility(
  tipo: DocumentiTipo | null,
  isAdmin: boolean
): HelpVisibilityInfo {
  return useMemo(() => {
    if (!tipo || !tipo.help_data) {
      return {
        isVisible: false,
        status: 'vuoto',
        message: 'Help non disponibile per questo tipo documento',
      };
    }

    const status = tipo.help_status || 'vuoto';
    const isPublic = tipo.help_visibile_pubblico ?? false;

    // Admin vedono sempre tutto
    if (isAdmin) {
      return {
        isVisible: true,
        status: status as any,
        message: status === 'da_completare' 
          ? '⚠️ Help in fase di completamento (visibile solo admin)'
          : undefined,
      };
    }

    // Non-admin vedono solo help pubblici
    if (!isPublic) {
      return {
        isVisible: false,
        status: 'non_disponibile',
        message: 'Help in fase di completamento. Contatta un amministratore per maggiori informazioni.',
      };
    }

    return {
      isVisible: true,
      status: status as any,
      message: status === 'parziale'
        ? 'ℹ️ Help parzialmente completato. Alcune sezioni potrebbero essere incomplete.'
        : undefined,
    };
  }, [tipo, isAdmin]);
}

/**
 * Filtra lista di tipi documento mostrando solo quelli con help visibile
 */
export function useFilteredTipiByHelpVisibility(
  tipi: DocumentiTipo[],
  isAdmin: boolean
): DocumentiTipo[] {
  return useMemo(() => {
    if (isAdmin) {
      // Admin vedono tutti i tipi
      return tipi;
    }

    // Non-admin vedono solo tipi con help pubblico
    return tipi.filter(tipo => {
      if (!tipo.help_data) return false;
      return tipo.help_visibile_pubblico ?? false;
    });
  }, [tipi, isAdmin]);
}

/**
 * Componente Badge per stato help
 */
export function HelpStatusBadge({ 
  status, 
  isAdmin 
}: { 
  status: string; 
  isAdmin: boolean;
}) {
  const config = {
    completo: {
      label: 'Completo',
      color: 'success' as const,
      icon: '✓',
    },
    parziale: {
      label: 'Parziale',
      color: 'warning' as const,
      icon: '⚠',
    },
    da_completare: {
      label: 'Da Completare',
      color: 'error' as const,
      icon: '⏳',
    },
    vuoto: {
      label: 'Non Disponibile',
      color: 'default' as const,
      icon: '✗',
    },
    non_disponibile: {
      label: 'Non Disponibile',
      color: 'default' as const,
      icon: '🔒',
    },
  };

  const statusConfig = config[status as keyof typeof config] || config.vuoto;

  // Non mostrare badge per help completi (default)
  if (status === 'completo' && !isAdmin) {
    return null;
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '2px 8px',
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: 600,
        backgroundColor: 
          statusConfig.color === 'success' ? '#e8f5e9' :
          statusConfig.color === 'warning' ? '#fff3e0' :
          statusConfig.color === 'error' ? '#ffebee' :
          '#f5f5f5',
        color:
          statusConfig.color === 'success' ? '#2e7d32' :
          statusConfig.color === 'warning' ? '#f57c00' :
          statusConfig.color === 'error' ? '#c62828' :
          '#757575',
      }}
    >
      <span>{statusConfig.icon}</span>
      <span>{statusConfig.label}</span>
      {isAdmin && status === 'da_completare' && (
        <span style={{ fontSize: '10px', opacity: 0.8 }}>(Admin)</span>
      )}
    </span>
  );
}
