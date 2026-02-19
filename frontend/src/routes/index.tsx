import { createBrowserRouter, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { AnagraficheListPage } from '@/pages/AnagraficheListPage';
import { AnagraficaDetailPage } from '@/pages/AnagraficaDetailPage';
import { AnagraficaFormPage } from '@/pages/AnagraficaFormPage';
import { AnagraficheImportPage } from '@/pages/AnagraficheImportPage';
import { DocumentiListPage } from '@/pages/DocumentiListPage';
import { DocumentoDetailPage } from '@/pages/DocumentoDetailPage';
import { DocumentoFormPage } from '@/pages/DocumentoFormPage';
// import { ImportaCedoliniPage } from '@/pages/ImportaCedoliniPage'; // ✅ DEPRECATO - Usare ImportSelectionPage
import { ImportaUnilavPage } from '@/pages/ImportaUnilavPage';
import { ImportSelectionPage } from '@/pages/ImportSelectionPage';
import { ImportDocumentsListPage } from '@/pages/ImportDocumentsListPage';
import { ImportDocumentPreviewPage } from '@/pages/ImportDocumentPreviewPage';
import PraticheListPage from '@/pages/PraticheListPage';
import PraticaDetailPage from '@/pages/PraticaDetailPage';
import PraticaFormPage from '@/pages/PraticaFormPage';
import FascicoliListPage from '@/pages/FascicoliListPage';
import FascicoloDetailPage from '@/pages/FascicoloDetailPage';
import FascicoloFormPage from '@/pages/FascicoloFormPage';
import ScadenzeListPage from '@/pages/ScadenzeListPage';
import ScadenzaDetailPage from '@/pages/ScadenzaDetailPage';
import ScadenzaFormPage from '@/pages/ScadenzaFormPage';
import ScadenziarioPage from '@/pages/ScadenziarioPage';
import CalendarioPage from '@/pages/CalendarioPage';
import StatistichePage from '@/pages/StatistichePage';
import ProtocollazionePopupPage from '@/pages/ProtocollazionePopupPage';
// import ProtocollazioneTestPage from '@/pages/ProtocollazioneTestPage'; // ✅ TEST DEBUG - Commentato
import ComunicazioniListPage from '@/pages/ComunicazioniListPage';
import ComunicazioneDetailPage from '@/pages/ComunicazioneDetailPage';
import ComunicazioneFormPage from '@/pages/ComunicazioneFormPage';
import MovimentoProtocolloListPage from '@/pages/MovimentoProtocolloListPage';
import MovimentoProtocolloDetailPage from '@/pages/MovimentoProtocolloDetailPage';
import {
  OperazioniArchivioList,
  OperazioneArchivioDetail,
  OperazioneArchivioForm,
} from '@/pages/ArchivioFisico';
import { ArchivioPage } from '@/pages/ArchivioPage';
import { UnitaFisicaDetailPage } from '@/pages/UnitaFisicaDetailPage';
import { HelpDocumentiPage, HelpDocumentoTipoDetailPage } from '@/pages/help';
import { JobsListPage, JobDetailPage } from '@/pages/aiClassifier';
import { ProtectedRoute } from '@/routes/ProtectedRoute';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'pratiche',
        element: <PraticheListPage />,
      },
      {
        path: 'pratiche/nuovo',
        element: <PraticaFormPage />,
      },
      {
        path: 'pratiche/:id',
        element: <PraticaDetailPage />,
      },
      {
        path: 'pratiche/:id/modifica',
        element: <PraticaFormPage />,
      },
      {
        path: 'fascicoli',
        element: <FascicoliListPage />,
      },
      {
        path: 'fascicoli/nuovo',
        element: <FascicoloFormPage />,
      },
      {
        path: 'fascicoli/:id',
        element: <FascicoloDetailPage />,
      },
      {
        path: 'fascicoli/:id/modifica',
        element: <FascicoloFormPage />,
      },
      {
        path: 'documenti',
        element: <DocumentiListPage />,
      },
      // ✅ DEPRECATO - Route vecchia, redirect a nuovo workflow
      // {
      //   path: 'documenti/importa-cedolini',
      //   element: <ImportaCedoliniPage />,
      // },
      {
        path: 'documenti/importa-cedolini',
        element: <Navigate to="/import" replace />,
      },
      {
        path: 'documenti/importa-unilav',
        element: <ImportaUnilavPage />,
      },
      // Nuovo workflow importazione standardizzato
      {
        path: 'import',
        element: <ImportSelectionPage />,
      },
      {
        path: 'import/:sessionUuid/documents',
        element: <ImportDocumentsListPage />,
      },
      {
        path: 'import/:sessionUuid/documents/:docUuid',
        element: <ImportDocumentPreviewPage />,
      },
      {
        path: 'documenti/new',
        element: <DocumentoFormPage />,
      },
      {
        path: 'documenti/:id',
        element: <DocumentoDetailPage />,
      },
      {
        path: 'documenti/:id/edit',
        element: <DocumentoFormPage />,
      },
      {
        path: 'anagrafiche',
        element: <AnagraficheListPage />,
      },
      {
        path: 'anagrafiche/import',
        element: <AnagraficheImportPage />,
      },
      {
        path: 'anagrafiche/new',
        element: <AnagraficaFormPage />,
      },
      {
        path: 'anagrafiche/:id',
        element: <AnagraficaDetailPage />,
      },
      {
        path: 'anagrafiche/:id/edit',
        element: <AnagraficaFormPage />,
      },
      {
        path: 'scadenze',
        element: <ScadenzeListPage />,
      },
      {
        path: 'scadenze/nuovo',
        element: <ScadenzaFormPage />,
      },
      {
        path: 'scadenze/scadenziario',
        element: <ScadenziarioPage />,
      },
      {
        path: 'scadenze/calendario',
        element: <CalendarioPage />,
      },
      {
        path: 'scadenze/statistiche',
        element: <StatistichePage />,
      },
      {
        path: 'scadenze/:id',
        element: <ScadenzaDetailPage />,
      },
      {
        path: 'scadenze/:id/modifica',
        element: <ScadenzaFormPage />,
      },
      {
        path: 'comunicazioni',
        element: <ComunicazioniListPage />,
      },
      {
        path: 'comunicazioni/create',
        element: <ComunicazioneFormPage />,
      },
      {
        path: 'comunicazioni/:id',
        element: <ComunicazioneDetailPage />,
      },
      {
        path: 'comunicazioni/:id/modifica',
        element: <ComunicazioneFormPage />,
      },
      {
        path: 'archivio',
        element: <ArchivioPage />,
      },
      {
        path: 'archivio/unita/:id',
        element: <UnitaFisicaDetailPage />,
      },
      {
        path: 'archivio-fisico/operazioni',
        element: <OperazioniArchivioList />,
      },
      {
        path: 'archivio-fisico/operazioni/nuova',
        element: <OperazioneArchivioForm />,
      },
      {
        path: 'archivio-fisico/operazioni/:id',
        element: <OperazioneArchivioDetail />,
      },
      {
        path: 'archivio-fisico/operazioni/:id/modifica',
        element: <OperazioneArchivioForm />,
      },
      {
        path: 'protocollo/movimenti',
        element: <MovimentoProtocolloListPage />,
      },
      {
        path: 'protocollo/movimenti/:id',
        element: <MovimentoProtocolloDetailPage />,
      },
      // Help Routes
      {
        path: 'help/documenti',
        element: <HelpDocumentiPage />,
      },
      {
        path: 'help/documenti/:codice',
        element: <HelpDocumentoTipoDetailPage />,
      },
      // AI Classifier Routes
      {
        path: 'ai-classifier/jobs',
        element: <JobsListPage />,
      },
      {
        path: 'ai-classifier/jobs/:id',
        element: <JobDetailPage />,
      },
    ],
  },
  {
    path: '/protocollazione-popup',
    element: <ProtocollazionePopupPage />, // Ripristinato componente originale
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
