/**
 * AutocompletePortal Component
 * Wrapper per dropdown autocomplete che usa React Portal per evitare overflow issues
 */
import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { createPortal } from 'react-dom';

interface AutocompletePortalProps {
  isOpen: boolean;
  children: React.ReactNode;
  anchorRef: React.RefObject<HTMLDivElement | null>;
  maxHeight?: string;
}

export interface AutocompletePortalRef {
  portalElement: HTMLDivElement | null;
}

export const AutocompletePortal = forwardRef<AutocompletePortalRef, AutocompletePortalProps>(({
  isOpen,
  children,
  anchorRef,
  maxHeight = '300px'
}, ref) => {
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0 });
  const portalRef = useRef<HTMLDivElement>(null);

  // Esponi il ref del portal element
  useImperativeHandle(ref, () => ({
    portalElement: portalRef.current
  }));

  useEffect(() => {
    if (!isOpen || !anchorRef.current) return;

    const updatePosition = () => {
      const rect = anchorRef.current?.getBoundingClientRect();
      if (rect) {
        setPosition({
          top: rect.bottom + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width
        });
      }
    };

    updatePosition();

    // Aggiorna posizione su scroll e resize
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);

    return () => {
      window.removeEventListener('scroll', updatePosition, true);
      window.removeEventListener('resize', updatePosition);
    };
  }, [isOpen, anchorRef]);

  if (!isOpen) return null;

  return createPortal(
    <div
      ref={portalRef}
      style={{
        position: 'absolute',
        top: `${position.top}px`,
        left: `${position.left}px`,
        width: `${position.width}px`,
        marginTop: '0.25rem',
        backgroundColor: 'white',
        border: '1px solid #d1d5db',
        borderRadius: '4px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1), 0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        maxHeight,
        overflowY: 'auto',
        zIndex: 9999
      }}
    >
      {children}
    </div>,
    document.body
  );
});

// Aggiungi display name per il debugging
AutocompletePortal.displayName = 'AutocompletePortal';
