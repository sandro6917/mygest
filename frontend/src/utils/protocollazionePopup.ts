/**
 * Utility per aprire finestra popup di protocollazione
 */

export interface OpenProtocollazionePopupOptions {
  tipo: 'documento' | 'fascicolo';
  id: number;
  titolo?: string;
  onSuccess?: () => void;
}

export function openProtocollazionePopup({
  tipo,
  id,
  titolo,
  onSuccess,
}: OpenProtocollazionePopupOptions): Window | null {
  // Costruisci URL con parametri
  const params = new URLSearchParams({
    tipo,
    id: id.toString(),
  });
  
  if (titolo) {
    params.append('titolo', titolo);
  }

  const url = `/protocollazione-popup?${params.toString()}`;
  
  // Apri popup centrata
  const width = 650;
  const height = 800;
  const left = window.screenX + (window.outerWidth - width) / 2;
  const top = window.screenY + (window.outerHeight - height) / 2;
  
  const popup = window.open(
    url,
    'protocollazione',
    `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
  );

  // Listener per messaggi dalla popup
  if (onSuccess) {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'protocollazione-success') {
        onSuccess();
        window.removeEventListener('message', handleMessage);
      }
    };
    
    window.addEventListener('message', handleMessage);
  }

  return popup;
}
