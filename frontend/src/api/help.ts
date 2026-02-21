import { apiClient } from './client';

export interface HelpTopic {
  slug: string;
  name: string;
  summary: string;
  order?: number;
}

export const helpApi = {
  /**
   * Ottieni lista di tutti i topic help disponibili
   */
  listTopics: async (): Promise<HelpTopic[]> => {
    const { data } = await apiClient.get<HelpTopic[]>('/help/topics/');
    return data;
  },
};
