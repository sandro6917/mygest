import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProtectedRoute } from '@/routes/ProtectedRoute';

// Queste tre rimangono eager: servono subito al primo render
import { LoginPage } from '@/pages/LoginPage';

// ---------------------------------------------------------------------------
// Lazy imports — ogni import diventa un chunk separato nel build
// ---------------------------------------------------------------------------

const DashboardPage = lazy(() => import('@/pages/DashboardPage').then(m => ({ default: m.DashboardPage })));

// Anagrafiche
const AnagraficheListPage   = lazy(() => import('@/pages/AnagraficheListPage').then(m => ({ default: m.AnagraficheListPage })));
const AnagraficaDetailPage  = lazy(() => import('@/pages/AnagraficaDetailPage').then(m => ({ default: m.AnagraficaDetailPage })));
const AnagraficaFormPage    = lazy(() => import('@/pages/AnagraficaFormPage').then(m => ({ default: m.AnagraficaFormPage })));
const AnagraficheImportPage = lazy(() => import('@/pages/AnagraficheImportPage').then(m => ({ default: m.AnagraficheImportPage })));

// Documenti
const DocumentiListPage      = lazy(() => import('@/pages/DocumentiListPage').then(m => ({ default: m.DocumentiListPage })));
const DocumentoDetailPage    = lazy(() => import('@/pages/DocumentoDetailPage').then(m => ({ default: m.DocumentoDetailPage })));
const DocumentoFormPage      = lazy(() => import('@/pages/DocumentoFormPage').then(m => ({ default: m.DocumentoFormPage })));
const DocumentiTipiListPage  = lazy(() => import('@/pages/DocumentiTipiListPage'));
const DocumentiTipoDetailPage = lazy(() => import('@/pages/DocumentiTipoDetailPage'));
const ImportaUnilavPage      = lazy(() => import('@/pages/ImportaUnilavPage').then(m => ({ default: m.ImportaUnilavPage })));
const ImportSelectionPage    = lazy(() => import('@/pages/ImportSelectionPage').then(m => ({ default: m.ImportSelectionPage })));
const ImportDocumentsListPage   = lazy(() => import('@/pages/ImportDocumentsListPage').then(m => ({ default: m.ImportDocumentsListPage })));
const ImportDocumentPreviewPage = lazy(() => import('@/pages/ImportDocumentPreviewPage').then(m => ({ default: m.ImportDocumentPreviewPage })));
const ImportaArchivioCUPage     = lazy(() => import('@/pages/ImportaArchivioCUPage').then(m => ({ default: m.ImportaArchivioCUPage })));

// Pratiche
const PraticheListPage  = lazy(() => import('@/pages/PraticheListPage'));
const PraticaDetailPage = lazy(() => import('@/pages/PraticaDetailPage'));
const PraticaFormPage   = lazy(() => import('@/pages/PraticaFormPage'));

// Fascicoli
const FascicoliListPage  = lazy(() => import('@/pages/FascicoliListPage'));
const FascicoloDetailPage = lazy(() => import('@/pages/FascicoloDetailPage'));
const FascicoloFormPage  = lazy(() => import('@/pages/FascicoloFormPage'));

// Scadenze
const ScadenzeListPage  = lazy(() => import('@/pages/ScadenzeListPage'));
const ScadenzaDetailPage = lazy(() => import('@/pages/ScadenzaDetailPage'));
const ScadenzaFormPage  = lazy(() => import('@/pages/ScadenzaFormPage'));
const ScadenziarioPage  = lazy(() => import('@/pages/ScadenziarioPage'));
const CalendarioPage    = lazy(() => import('@/pages/CalendarioPage'));
const StatistichePage   = lazy(() => import('@/pages/StatistichePage'));

// Comunicazioni
const ComunicazioniListPage   = lazy(() => import('@/pages/ComunicazioniListPage'));
const ComunicazioneDetailPage = lazy(() => import('@/pages/ComunicazioneDetailPage'));
const ComunicazioneFormPage   = lazy(() => import('@/pages/ComunicazioneFormPage'));

// Archivio fisico
const ArchivioPage          = lazy(() => import('@/pages/ArchivioPage').then(m => ({ default: m.ArchivioPage })));
const UnitaFisicaDetailPage = lazy(() => import('@/pages/UnitaFisicaDetailPage').then(m => ({ default: m.UnitaFisicaDetailPage })));
const UnitaFisicaFormPage   = lazy(() => import('@/pages/UnitaFisicaFormPage'));
const OperazioniArchivioList   = lazy(() => import('@/pages/ArchivioFisico').then(m => ({ default: m.OperazioniArchivioList })));
const OperazioneArchivioDetail = lazy(() => import('@/pages/ArchivioFisico').then(m => ({ default: m.OperazioneArchivioDetail })));
const OperazioneArchivioForm   = lazy(() => import('@/pages/ArchivioFisico').then(m => ({ default: m.OperazioneArchivioForm })));

// Protocollo
const MovimentoProtocolloListPage   = lazy(() => import('@/pages/MovimentoProtocolloListPage'));
const MovimentoProtocolloDetailPage = lazy(() => import('@/pages/MovimentoProtocolloDetailPage'));
const ProtocollazionePopupPage      = lazy(() => import('@/pages/ProtocollazionePopupPage'));

// AI Classifier
const JobsListPage  = lazy(() => import('@/pages/aiClassifier').then(m => ({ default: m.JobsListPage })));
const JobDetailPage = lazy(() => import('@/pages/aiClassifier').then(m => ({ default: m.JobDetailPage })));

// AI Import templates
const TemplateListPage   = lazy(() => import('@/pages/aiImport/TemplateListPage').then(m => ({ default: m.TemplateListPage })));
const TemplateEditorPage = lazy(() => import('@/pages/aiImport/TemplateEditorPage').then(m => ({ default: m.TemplateEditorPage })));

// Help — raggruppato in un unico chunk (pagine raramente visitate)
const HelpIndexPage             = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpIndexPage })));
const HelpPrincipiantiPage      = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpPrincipiantiPage })));
const HelpScadenzePage          = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpScadenzePage })));
const HelpDeploymentPage        = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpDeploymentPage })));
const HelpAnagrafichePage       = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpAnagrafichePage })));
const HelpDocumentiPage         = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpDocumentiPage })));
const HelpDocumentoTipoDetailPage = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpDocumentoTipoDetailPage })));
const HelpComunicazioniPage     = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpComunicazioniPage })));
const HelpFascicoliPage         = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpFascicoliPage })));
const HelpPratichePage          = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpPratichePage })));
const HelpArchivioFisicoPage    = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpArchivioFisicoPage })));
const HelpProtocolloPage        = lazy(() => import('@/pages/help').then(m => ({ default: m.HelpProtocolloPage })));

// ---------------------------------------------------------------------------
// Fallback di caricamento
// ---------------------------------------------------------------------------

const PageLoader = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
    <CircularProgress />
  </Box>
);

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

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
        element: <Suspense fallback={<PageLoader />}><DashboardPage /></Suspense>,
      },
      // Pratiche
      { path: 'pratiche',              element: <Suspense fallback={<PageLoader />}><PraticheListPage /></Suspense> },
      { path: 'pratiche/nuovo',        element: <Suspense fallback={<PageLoader />}><PraticaFormPage /></Suspense> },
      { path: 'pratiche/:id',          element: <Suspense fallback={<PageLoader />}><PraticaDetailPage /></Suspense> },
      { path: 'pratiche/:id/modifica', element: <Suspense fallback={<PageLoader />}><PraticaFormPage /></Suspense> },
      // Fascicoli
      { path: 'fascicoli',              element: <Suspense fallback={<PageLoader />}><FascicoliListPage /></Suspense> },
      { path: 'fascicoli/nuovo',        element: <Suspense fallback={<PageLoader />}><FascicoloFormPage /></Suspense> },
      { path: 'fascicoli/:id',          element: <Suspense fallback={<PageLoader />}><FascicoloDetailPage /></Suspense> },
      { path: 'fascicoli/:id/modifica', element: <Suspense fallback={<PageLoader />}><FascicoloFormPage /></Suspense> },
      // Documenti
      { path: 'documenti',                           element: <Suspense fallback={<PageLoader />}><DocumentiListPage /></Suspense> },
      { path: 'documenti/importa-cedolini',          element: <Navigate to="/import" replace /> },
      { path: 'documenti/importa-unilav',            element: <Suspense fallback={<PageLoader />}><ImportaUnilavPage /></Suspense> },
      { path: 'documenti/new',                       element: <Suspense fallback={<PageLoader />}><DocumentoFormPage /></Suspense> },
      { path: 'documenti/tipi',                      element: <Suspense fallback={<PageLoader />}><DocumentiTipiListPage /></Suspense> },
      { path: 'documenti/tipi/:codice',               element: <Suspense fallback={<PageLoader />}><DocumentiTipoDetailPage /></Suspense> },
      { path: 'documenti/:id',                       element: <Suspense fallback={<PageLoader />}><DocumentoDetailPage /></Suspense> },
      { path: 'documenti/:id/edit',                  element: <Suspense fallback={<PageLoader />}><DocumentoFormPage /></Suspense> },
      { path: 'import',                              element: <Suspense fallback={<PageLoader />}><ImportSelectionPage /></Suspense> },
      { path: 'import/:sessionUuid/documents',       element: <Suspense fallback={<PageLoader />}><ImportDocumentsListPage /></Suspense> },
      { path: 'import/:sessionUuid/documents/:docUuid', element: <Suspense fallback={<PageLoader />}><ImportDocumentPreviewPage /></Suspense> },
      { path: 'import-archivio-cu',                    element: <Suspense fallback={<PageLoader />}><ImportaArchivioCUPage /></Suspense> },
      // Anagrafiche
      { path: 'anagrafiche',           element: <Suspense fallback={<PageLoader />}><AnagraficheListPage /></Suspense> },
      { path: 'anagrafiche/import',    element: <Suspense fallback={<PageLoader />}><AnagraficheImportPage /></Suspense> },
      { path: 'anagrafiche/new',       element: <Suspense fallback={<PageLoader />}><AnagraficaFormPage /></Suspense> },
      { path: 'anagrafiche/:id',       element: <Suspense fallback={<PageLoader />}><AnagraficaDetailPage /></Suspense> },
      { path: 'anagrafiche/:id/edit',  element: <Suspense fallback={<PageLoader />}><AnagraficaFormPage /></Suspense> },
      // Scadenze
      { path: 'scadenze',              element: <Suspense fallback={<PageLoader />}><ScadenzeListPage /></Suspense> },
      { path: 'scadenze/nuovo',        element: <Suspense fallback={<PageLoader />}><ScadenzaFormPage /></Suspense> },
      { path: 'scadenze/scadenziario', element: <Suspense fallback={<PageLoader />}><ScadenziarioPage /></Suspense> },
      { path: 'scadenze/calendario',   element: <Suspense fallback={<PageLoader />}><CalendarioPage /></Suspense> },
      { path: 'scadenze/statistiche',  element: <Suspense fallback={<PageLoader />}><StatistichePage /></Suspense> },
      { path: 'scadenze/:id',          element: <Suspense fallback={<PageLoader />}><ScadenzaDetailPage /></Suspense> },
      { path: 'scadenze/:id/modifica', element: <Suspense fallback={<PageLoader />}><ScadenzaFormPage /></Suspense> },
      // Comunicazioni
      { path: 'comunicazioni',              element: <Suspense fallback={<PageLoader />}><ComunicazioniListPage /></Suspense> },
      { path: 'comunicazioni/create',       element: <Suspense fallback={<PageLoader />}><ComunicazioneFormPage /></Suspense> },
      { path: 'comunicazioni/:id',          element: <Suspense fallback={<PageLoader />}><ComunicazioneDetailPage /></Suspense> },
      { path: 'comunicazioni/:id/modifica', element: <Suspense fallback={<PageLoader />}><ComunicazioneFormPage /></Suspense> },
      // Archivio fisico
      { path: 'archivio',                             element: <Suspense fallback={<PageLoader />}><ArchivioPage /></Suspense> },
      { path: 'archivio/unita/nuovo',                 element: <Suspense fallback={<PageLoader />}><UnitaFisicaFormPage /></Suspense> },
      { path: 'archivio/unita/:id/modifica',          element: <Suspense fallback={<PageLoader />}><UnitaFisicaFormPage /></Suspense> },
      { path: 'archivio/unita/:id',                   element: <Suspense fallback={<PageLoader />}><UnitaFisicaDetailPage /></Suspense> },
      { path: 'archivio-fisico/operazioni',           element: <Suspense fallback={<PageLoader />}><OperazioniArchivioList /></Suspense> },
      { path: 'archivio-fisico/operazioni/nuova',     element: <Suspense fallback={<PageLoader />}><OperazioneArchivioForm /></Suspense> },
      { path: 'archivio-fisico/operazioni/:id',       element: <Suspense fallback={<PageLoader />}><OperazioneArchivioDetail /></Suspense> },
      { path: 'archivio-fisico/operazioni/:id/modifica', element: <Suspense fallback={<PageLoader />}><OperazioneArchivioForm /></Suspense> },
      // Protocollo
      { path: 'protocollo/movimenti',     element: <Suspense fallback={<PageLoader />}><MovimentoProtocolloListPage /></Suspense> },
      { path: 'protocollo/movimenti/:id', element: <Suspense fallback={<PageLoader />}><MovimentoProtocolloDetailPage /></Suspense> },
      // Help
      { path: 'help',                   element: <Suspense fallback={<PageLoader />}><HelpIndexPage /></Suspense> },
      { path: 'help/guida-principianti', element: <Suspense fallback={<PageLoader />}><HelpPrincipiantiPage /></Suspense> },
      { path: 'help/guida-scadenze',    element: <Suspense fallback={<PageLoader />}><HelpScadenzePage /></Suspense> },
      { path: 'help/guida-deployment',  element: <Suspense fallback={<PageLoader />}><HelpDeploymentPage /></Suspense> },
      { path: 'help/anagrafiche',       element: <Suspense fallback={<PageLoader />}><HelpAnagrafichePage /></Suspense> },
      { path: 'help/documenti',         element: <Suspense fallback={<PageLoader />}><HelpDocumentiPage /></Suspense> },
      { path: 'help/documenti/:codice', element: <Suspense fallback={<PageLoader />}><HelpDocumentoTipoDetailPage /></Suspense> },
      { path: 'help/comunicazioni',     element: <Suspense fallback={<PageLoader />}><HelpComunicazioniPage /></Suspense> },
      { path: 'help/fascicoli',         element: <Suspense fallback={<PageLoader />}><HelpFascicoliPage /></Suspense> },
      { path: 'help/pratiche',          element: <Suspense fallback={<PageLoader />}><HelpPratichePage /></Suspense> },
      { path: 'help/archivio_fisico',   element: <Suspense fallback={<PageLoader />}><HelpArchivioFisicoPage /></Suspense> },
      { path: 'help/protocollo',        element: <Suspense fallback={<PageLoader />}><HelpProtocolloPage /></Suspense> },
      // AI Classifier
      { path: 'ai-classifier/jobs',     element: <Suspense fallback={<PageLoader />}><JobsListPage /></Suspense> },
      { path: 'ai-classifier/jobs/:id', element: <Suspense fallback={<PageLoader />}><JobDetailPage /></Suspense> },
      // AI Import templates
      { path: 'admin/templates',     element: <Suspense fallback={<PageLoader />}><TemplateListPage /></Suspense> },
      { path: 'admin/templates/:id', element: <Suspense fallback={<PageLoader />}><TemplateEditorPage /></Suspense> },
    ],
  },
  {
    path: '/protocollazione-popup',
    element: <Suspense fallback={<PageLoader />}><ProtocollazionePopupPage /></Suspense>,
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
