/**
 * Test page per verificare il routing del popup
 */
import React from 'react';
import { useSearchParams } from 'react-router-dom';

const ProtocollazioneTestPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  
  return (
    <div style={{ padding: '2rem', fontFamily: 'Arial' }}>
      <h1>✅ Popup di Test Funziona!</h1>
      <p>Se vedi questa pagina, il routing funziona.</p>
      <hr />
      <h3>Parametri ricevuti:</h3>
      <ul>
        <li><strong>tipo:</strong> {searchParams.get('tipo') || 'non specificato'}</li>
        <li><strong>id:</strong> {searchParams.get('id') || 'non specificato'}</li>
        <li><strong>titolo:</strong> {searchParams.get('titolo') || 'non specificato'}</li>
      </ul>
    </div>
  );
};

export default ProtocollazioneTestPage;
