/**
 * Esempio di configurazione routes per Archivio Fisico
 * Aggiungi questo al tuo file di routing principale
 */
import type { RouteObject } from 'react-router-dom';
import {
  OperazioniArchivioList,
  OperazioneArchivioDetail,
  OperazioneArchivioForm,
} from '../pages/ArchivioFisico';

// Esempio con React Router v6
export const archivioFisicoRoutes: RouteObject[] = [
  {
    path: '/archivio-fisico',
    children: [
      {
        index: true,
        // Redirect alla lista operazioni
        element: <OperazioniArchivioList />,
      },
      {
        path: 'operazioni',
        children: [
          {
            index: true,
            element: <OperazioniArchivioList />,
          },
          {
            path: 'nuova',
            element: <OperazioneArchivioForm />,
          },
          {
            path: ':id',
            element: <OperazioneArchivioDetail />,
          },
          {
            path: ':id/modifica',
            element: <OperazioneArchivioForm />,
          },
        ],
      },
    ],
  },
];

// Come integrare nel router principale:
// 
// import { archivioFisicoRoutes } from './archivioFisicoRoutes';
// 
// const router = createBrowserRouter([
//   {
//     path: '/',
//     element: <Layout />,
//     children: [
//       ...otherRoutes,
//       ...archivioFisicoRoutes,
//     ],
//   },
// ]);

export default archivioFisicoRoutes;
