import React, { useState } from 'react';

interface FileSourceInfoProps {
  onSourcePathChange?: (path: string, shouldDelete: boolean) => void;
}

/**
 * Componente per gestire le informazioni del file di origine.
 * 
 * Mostra un campo opzionale dove l'utente può inserire il percorso
 * del file originale e una checkbox per richiedere l'eliminazione
 * automatica tramite agent desktop.
 */
export const FileSourceInfo: React.FC<FileSourceInfoProps> = ({ 
  onSourcePathChange 
}) => {
  const [sourcePath, setSourcePath] = useState('');
  const [shouldDelete, setShouldDelete] = useState(false);
  
  /**
   * Converte path Windows in path WSL
   * C:\Users\... -> /mnt/c/Users/...
   * G:\... -> /mnt/g/...
   */
  const convertWindowsPathToWSL = (windowsPath: string): string => {
    if (!windowsPath) return '';
    
    // Rimuovi virgolette se presenti (da "Copia come percorso" Windows)
    let cleanPath = windowsPath.trim();
    if (cleanPath.startsWith('"') && cleanPath.endsWith('"')) {
      cleanPath = cleanPath.slice(1, -1);
    }
    if (cleanPath.startsWith("'") && cleanPath.endsWith("'")) {
      cleanPath = cleanPath.slice(1, -1);
    }
    
    // Già in formato WSL
    if (cleanPath.startsWith('/mnt/')) {
      return cleanPath;
    }
    
    // Già in formato Unix/Linux
    if (cleanPath.startsWith('/')) {
      return cleanPath;
    }
    
    // Converte path Windows (C:\... o G:\...)
    const driveMatch = cleanPath.match(/^([A-Za-z]):[/\\](.*)/);
    if (driveMatch) {
      const [, drive, restPath] = driveMatch;
      // Converte backslash in slash e costruisce path WSL
      const unixPath = restPath.replace(/\\/g, '/');
      return `/mnt/${drive.toLowerCase()}/${unixPath}`;
    }
    
    // Path UNC (\\server\share\...)
    if (cleanPath.startsWith('\\\\')) {
      // Per ora manteniamo invariato (richiede mount personalizzato)
      return cleanPath;
    }
    
    // Default: ritorna così com'è
    return cleanPath;
  };
  
  const handlePathChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputPath = e.target.value;
    setSourcePath(inputPath);
    
    // Converte automaticamente in path WSL
    const wslPath = convertWindowsPathToWSL(inputPath);
    onSourcePathChange?.(wslPath, shouldDelete);
  };
  
  const handleDeleteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newShouldDelete = e.target.checked;
    setShouldDelete(newShouldDelete);
    
    // Riconverti il path quando cambia lo stato della checkbox
    const wslPath = convertWindowsPathToWSL(sourcePath);
    onSourcePathChange?.(wslPath, newShouldDelete);
  };
  
  // Mostra preview del path convertito
  const wslPreviewPath = convertWindowsPathToWSL(sourcePath);
  const showConversionPreview = sourcePath && wslPreviewPath !== sourcePath;
  
  return (
    <div className="space-y-3">
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex items-start space-x-2">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-sm text-gray-700">
            <strong>Eliminazione automatica file originale</strong>
            <br />
            Se desideri eliminare automaticamente il file dal tuo computer dopo l'archiviazione,
            inserisci il percorso completo del file e spunta la casella sottostante.
            <br />
            <span className="text-xs text-gray-600 mt-1 block">
              Nota: È necessario che l'agent desktop MyGest sia in esecuzione sul tuo computer.
            </span>
          </div>
        </div>
      </div>
      
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Percorso file originale (opzionale)
        </label>
        <input
          type="text"
          value={sourcePath}
          onChange={handlePathChange}
          placeholder="Es: C:\Users\Nome\Downloads\documento.pdf oppure G:\Il mio Drive\file.pdf"
          className="w-full p-2 border border-gray-300 rounded-md text-sm"
        />
        <p className="text-xs text-gray-500">
          Inserisci il percorso Windows (es. C:\..., G:\...) - sarà convertito automaticamente
        </p>
        
        {/* Preview conversione path */}
        {showConversionPreview && (
          <div className="bg-green-50 border border-green-200 rounded p-2 mt-2">
            <div className="flex items-start space-x-2">
              <svg className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-xs">
                <div className="text-gray-600 font-medium">Path convertito per WSL:</div>
                <code className="text-green-700 break-all">{wslPreviewPath}</code>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {sourcePath && (
        <div className="flex items-start space-x-2">
          <input
            type="checkbox"
            id="delete-source"
            checked={shouldDelete}
            onChange={handleDeleteChange}
            className="mt-1"
          />
          <label htmlFor="delete-source" className="text-sm text-gray-700 cursor-pointer">
            <strong>Elimina automaticamente il file originale</strong> dopo l'archiviazione
            <br />
            <span className="text-xs text-gray-600">
              Il file verrà eliminato solo dopo che l'agent desktop avrà confermato
              il completamento dell'archiviazione
            </span>
          </label>
        </div>
      )}
      
      {shouldDelete && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="text-sm text-gray-700">
            ⚠️ <strong>Attenzione:</strong> Il file verrà eliminato definitivamente dal tuo computer.
            Assicurati che il percorso sia corretto prima di procedere.
          </div>
        </div>
      )}
    </div>
  );
};

export default FileSourceInfo;
