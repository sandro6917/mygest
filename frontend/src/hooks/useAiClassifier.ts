/**
 * React Query Hooks per AI Classifier
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiClassifierApi } from '@/api/aiClassifier';
import type {
  CreateJobRequest,
  ImportDocumentsRequest,
} from '@/types/aiClassifier';
import { toast } from 'react-toastify';

// Query Keys
export const aiClassifierKeys = {
  all: ['aiClassifier'] as const,
  jobs: () => [...aiClassifierKeys.all, 'jobs'] as const,
  job: (id: number) => [...aiClassifierKeys.jobs(), id] as const,
  results: () => [...aiClassifierKeys.all, 'results'] as const,
  result: (id: number) => [...aiClassifierKeys.results(), id] as const,
  config: () => [...aiClassifierKeys.all, 'config'] as const,
  stats: () => [...aiClassifierKeys.all, 'stats'] as const,
};

// ==================== JOBS ====================

export const useJobs = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: [...aiClassifierKeys.jobs(), params],
    queryFn: () => aiClassifierApi.listJobs(params),
  });
};

export const useJob = (id: number) => {
  return useQuery({
    queryKey: aiClassifierKeys.job(id),
    queryFn: () => aiClassifierApi.getJob(id),
    enabled: !!id,
    refetchInterval: (query) => {
      // Auto-refresh se job in running
      if (query.state.data?.status === 'running') {
        return 2000; // 2 secondi
      }
      return false;
    },
  });
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateJobRequest) => aiClassifierApi.createJob(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.jobs() });
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.stats() });
      toast.success('Job creato con successo');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Errore creazione job');
    },
  });
};

export const useStartJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => aiClassifierApi.startJob(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.job(data.id) });
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.jobs() });
      toast.success('Job avviato');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Errore avvio job');
    },
  });
};

export const useDeleteJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => aiClassifierApi.deleteJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.jobs() });
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.stats() });
      toast.success('Job eliminato');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Errore eliminazione job');
    },
  });
};

export const useJobStats = () => {
  return useQuery({
    queryKey: aiClassifierKeys.stats(),
    queryFn: () => aiClassifierApi.getJobStats(),
  });
};

// ==================== RESULTS ====================

export const useResults = (params?: Record<string, any>) => {
  // Verifica che il parametro job (se presente) sia un numero valido
  const jobId = params?.job;
  const isValidJobId = jobId === undefined || (typeof jobId === 'number' && !isNaN(jobId));

  return useQuery({
    queryKey: [...aiClassifierKeys.results(), params],
    queryFn: () => aiClassifierApi.listResults(params),
    enabled: isValidJobId, // Disabilita query se job=NaN
  });
};

export const useResult = (id: number) => {
  return useQuery({
    queryKey: aiClassifierKeys.result(id),
    queryFn: () => aiClassifierApi.getResult(id),
    enabled: !!id,
  });
};

export const useUpdateResult = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: any }) =>
      aiClassifierApi.updateResult(id, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.result(data.id) });
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.results() });
      toast.success('Risultato aggiornato');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Errore aggiornamento');
    },
  });
};

export const useDeleteResult = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => aiClassifierApi.deleteResult(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.results() });
      toast.success('Risultato eliminato');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Errore eliminazione');
    },
  });
};

// ==================== CONFIG ====================

export const useConfig = () => {
  return useQuery({
    queryKey: aiClassifierKeys.config(),
    queryFn: () => aiClassifierApi.getConfig(),
  });
};

export const useUpdateConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (updates: any) => aiClassifierApi.updateConfig(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.config() });
      toast.success('Configurazione aggiornata');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Errore aggiornamento configurazione');
    },
  });
};

// ==================== IMPORT ====================

export const useImportDocuments = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ImportDocumentsRequest) =>
      aiClassifierApi.importDocuments(request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: aiClassifierKeys.results() });
      toast.success(`Importati ${data.imported_count} documenti`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Errore importazione documenti');
    },
  });
};
