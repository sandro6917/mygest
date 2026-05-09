/**
 * Custom hooks per AI Import
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { aiImportApi } from '@/api/aiImport';
import type {
  DocumentExtractionTemplate,
  UploadDocumentRequest,
  PredictTypeRequest,
  ExtractDataRequest,
  ConfirmPredictionRequest,
  SaveFeedbackRequest,
  CreateTemplateRequest,
  CreateTemplatePageRequest,
  CreateTemplateZoneRequest,
  CreateFieldMappingRequest,
} from '@/types/aiImport';

// ==================== QUERY KEYS ====================

export const aiImportKeys = {
  all: ['ai-import'] as const,
  templates: () => [...aiImportKeys.all, 'templates'] as const,
  template: (id: number) => [...aiImportKeys.templates(), id] as const,
  feedback: () => [...aiImportKeys.all, 'feedback'] as const,
  feedbackItem: (id: number) => [...aiImportKeys.feedback(), id] as const,
  feedbackStats: () => [...aiImportKeys.feedback(), 'stats'] as const,
};

// ==================== TEMPLATES ====================

/**
 * Hook per lista template
 */
export const useTemplates = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: [...aiImportKeys.templates(), params],
    queryFn: () => aiImportApi.listTemplates(params),
  });
};

/**
 * Hook per dettaglio template
 */
export const useTemplate = (id: number, enabled = true) => {
  return useQuery({
    queryKey: aiImportKeys.template(id),
    queryFn: () => aiImportApi.getTemplate(id),
    enabled: enabled && !!id,
  });
};

/**
 * Hook per creare template
 */
export const useCreateTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateTemplateRequest) => aiImportApi.createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.templates() });
    },
  });
};

/**
 * Hook per aggiornare template
 */
export const useUpdateTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateTemplateRequest> }) =>
      aiImportApi.updateTemplate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.template(variables.id) });
      queryClient.invalidateQueries({ queryKey: aiImportKeys.templates() });
    },
  });
};

/**
 * Hook per eliminare template
 */
export const useDeleteTemplate = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => aiImportApi.deleteTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.templates() });
    },
  });
};

/**
 * Hook per aggiungere pagina a template
 */
export const useAddTemplatePage = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ templateId, data }: { templateId: number; data: CreateTemplatePageRequest }) =>
      aiImportApi.addTemplatePage(templateId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.template(variables.templateId) });
    },
  });
};

/**
 * Hook per aggiungere zona estrazione
 */
export const useAddTemplateZone = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateTemplateZoneRequest) => aiImportApi.addTemplateZone(data),
    onSuccess: () => {
      // Invalida tutti i template perché non sappiamo quale template appartiene la pagina
      queryClient.invalidateQueries({ queryKey: aiImportKeys.templates() });
    },
  });
};

/**
 * Hook per eliminare zona estrazione
 */
export const useDeleteTemplateZone = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (zoneId: number) => aiImportApi.deleteTemplateZone(zoneId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.templates() });
    },
  });
};

/**
 * Hook per ottenere campi disponibili per tipo documento
 */
export const useAvailableFields = (tipoDocumentoId: number | undefined) => {
  return useQuery({
    queryKey: ['available-fields', tipoDocumentoId],
    queryFn: () => aiImportApi.getAvailableFields(tipoDocumentoId!),
    enabled: !!tipoDocumentoId,
  });
};

/**
 * Hook per ottenere trasformazioni disponibili
 */
export const useAvailableTransformations = () => {
  return useQuery({
    queryKey: ['available-transformations'],
    queryFn: () => aiImportApi.getAvailableTransformations(),
    staleTime: Infinity, // Le trasformazioni non cambiano
  });
};

/**
 * Hook per aggiungere field mapping
 */
export const useAddFieldMapping = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateFieldMappingRequest) => aiImportApi.addFieldMapping(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.templates() });
    },
  });
};

/**
 * Hook per eliminare field mapping
 */
export const useDeleteFieldMapping = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (mappingId: number) => aiImportApi.deleteFieldMapping(mappingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.templates() });
    },
  });
};

// ==================== AI IMPORT WORKFLOW ====================

/**
 * Hook per upload documento
 */
export const useUploadDocument = () => {
  return useMutation({
    mutationFn: (data: UploadDocumentRequest) => aiImportApi.upload(data),
  });
};

/**
 * Hook per predizione tipo documento
 */
export const usePredictType = () => {
  return useMutation({
    mutationFn: (data: PredictTypeRequest) => aiImportApi.predict(data),
  });
};

/**
 * Hook per estrazione dati
 */
export const useExtractData = () => {
  return useMutation({
    mutationFn: (data: ExtractDataRequest) => aiImportApi.extract(data),
  });
};

/**
 * Hook per conferma predizione
 */
export const useConfirmPrediction = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: ConfirmPredictionRequest) => aiImportApi.confirmPrediction(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.feedback() });
      queryClient.invalidateQueries({ queryKey: aiImportKeys.feedbackStats() });
    },
  });
};

/**
 * Hook per salvataggio feedback
 */
export const useSaveFeedback = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: SaveFeedbackRequest) => aiImportApi.saveFeedback(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiImportKeys.feedback() });
    },
  });
};

// ==================== FEEDBACK ====================

/**
 * Hook per lista feedback
 */
export const useFeedbackList = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: [...aiImportKeys.feedback(), params],
    queryFn: () => aiImportApi.listFeedback(params),
  });
};

/**
 * Hook per dettaglio feedback
 */
export const useFeedback = (id: number, enabled = true) => {
  return useQuery({
    queryKey: aiImportKeys.feedbackItem(id),
    queryFn: () => aiImportApi.getFeedback(id),
    enabled: enabled && !!id,
  });
};

/**
 * Hook per statistiche feedback
 */
export const useFeedbackStats = () => {
  return useQuery({
    queryKey: aiImportKeys.feedbackStats(),
    queryFn: () => aiImportApi.getFeedbackStats(),
  });
};
