/**
 * Tipi e helper condivisi per costruire/leggere la configurazione di un alert
 * scadenza (ScadenzaAlert), per canale (email/webhook/telegram/whatsapp).
 *
 * Condiviso tra AlertManager (gestione alert di una singola occorrenza) e
 * GeneraOccorrenzeWizard (template alert applicati in batch a più occorrenze).
 */
import type { ScadenzaAlert } from '@/types/scadenza';

export type MetodoAlert = 'email' | 'webhook' | 'telegram' | 'whatsapp';
export type PeriodoOffset = 'minutes' | 'hours' | 'days' | 'weeks';

export interface AlertFormData {
  offset_alert: number;
  offset_alert_periodo: PeriodoOffset;
  metodo_alert: MetodoAlert;
  // email
  destinatari: string;
  oggetto_custom: string;
  corpo_custom: string;
  // webhook
  webhook_url: string;
  webhook_payload: string;
  // telegram
  telegram_chat_ids: string;
  // whatsapp
  whatsapp_numeri: string;
}

export const initialAlertFormData: AlertFormData = {
  offset_alert: 1,
  offset_alert_periodo: 'days',
  metodo_alert: 'email',
  destinatari: '',
  oggetto_custom: '',
  corpo_custom: '',
  webhook_url: '',
  webhook_payload: '',
  telegram_chat_ids: '',
  whatsapp_numeri: '',
};

export function buildAlertConfig(form: AlertFormData): Record<string, unknown> {
  switch (form.metodo_alert) {
    case 'email': {
      const cfg: Record<string, unknown> = {};
      if (form.destinatari.trim()) cfg.destinatari = form.destinatari.trim();
      if (form.oggetto_custom.trim()) cfg.oggetto_custom = form.oggetto_custom.trim();
      if (form.corpo_custom.trim()) cfg.corpo_custom = form.corpo_custom.trim();
      return cfg;
    }
    case 'webhook': {
      const cfg: Record<string, unknown> = { url: form.webhook_url.trim() };
      if (form.webhook_payload.trim()) {
        try {
          cfg.payload = JSON.parse(form.webhook_payload);
        } catch {
          // lascia senza payload se JSON non valido
        }
      }
      if (form.corpo_custom.trim()) cfg.corpo_custom = form.corpo_custom.trim();
      return cfg;
    }
    case 'telegram': {
      const cfg: Record<string, unknown> = {};
      if (form.telegram_chat_ids.trim()) {
        cfg.chat_ids = form.telegram_chat_ids.split(',').map(s => s.trim()).filter(Boolean);
      }
      if (form.corpo_custom.trim()) cfg.corpo_custom = form.corpo_custom.trim();
      return cfg;
    }
    case 'whatsapp': {
      const cfg: Record<string, unknown> = {};
      if (form.whatsapp_numeri.trim()) {
        cfg.numeri_telefono = form.whatsapp_numeri.split(',').map(s => s.trim()).filter(Boolean);
      }
      if (form.corpo_custom.trim()) cfg.corpo_custom = form.corpo_custom.trim();
      return cfg;
    }
    default:
      return {};
  }
}

export function parseAlertConfig(alert: ScadenzaAlert): Partial<AlertFormData> {
  const cfg = (alert.alert_config as Record<string, unknown>) || {};
  const result: Partial<AlertFormData> = {
    metodo_alert: alert.metodo_alert as MetodoAlert,
    offset_alert: alert.offset_alert,
    offset_alert_periodo: (alert.offset_alert_periodo as PeriodoOffset) || 'days',
    corpo_custom: typeof cfg.corpo_custom === 'string' ? cfg.corpo_custom : '',
  };
  if (alert.metodo_alert === 'email') {
    result.destinatari = typeof cfg.destinatari === 'string' ? cfg.destinatari : '';
    result.oggetto_custom = typeof cfg.oggetto_custom === 'string' ? cfg.oggetto_custom : '';
  }
  if (alert.metodo_alert === 'webhook') {
    result.webhook_url = typeof cfg.url === 'string' ? cfg.url : '';
    result.webhook_payload = cfg.payload ? JSON.stringify(cfg.payload, null, 2) : '';
  }
  if (alert.metodo_alert === 'telegram') {
    const ids = Array.isArray(cfg.chat_ids) ? cfg.chat_ids.join(', ') : '';
    result.telegram_chat_ids = ids;
  }
  if (alert.metodo_alert === 'whatsapp') {
    const numeri = Array.isArray(cfg.numeri_telefono) ? cfg.numeri_telefono.join(', ') : '';
    result.whatsapp_numeri = numeri;
  }
  return result;
}
