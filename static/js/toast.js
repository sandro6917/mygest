/**
 * Toast Notification System
 * Sistema di notifiche non invasive per feedback utente
 */

(function() {
  'use strict';

  class ToastManager {
    constructor() {
      this.container = null;
      this.toasts = [];
      this.maxToasts = 5;
      this.defaultDuration = 4000;
      this.init();
    }

    /**
     * Inizializza il container dei toast
     */
    init() {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.createContainer());
      } else {
        this.createContainer();
      }
    }

    /**
     * Crea il container per i toast
     */
    createContainer() {
      if (this.container) return;

      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.setAttribute('role', 'region');
      this.container.setAttribute('aria-label', 'Notifiche');
      document.body.appendChild(this.container);
    }

    /**
     * Mostra un toast
     * @param {Object} options - Opzioni del toast
     */
    show(options = {}) {
      const toast = this.createToast(options);
      
      // Limita numero toast visibili
      if (this.toasts.length >= this.maxToasts) {
        this.removeToast(this.toasts[0]);
      }

      this.toasts.push(toast);
      this.container.appendChild(toast.element);

      // Trigger reflow per animazione
      toast.element.offsetHeight;
      toast.element.classList.add('toast-show');

      // Auto-dismiss
      if (toast.duration > 0) {
        toast.timeoutId = setTimeout(() => {
          this.removeToast(toast);
        }, toast.duration);
      }

      return toast;
    }

    /**
     * Crea elemento toast
     */
    createToast(options) {
      const {
        message = 'Notifica',
        type = 'info', // info, success, warning, error
        duration = this.defaultDuration,
        closable = true,
        action = null
      } = options;

      const element = document.createElement('div');
      element.className = `toast toast-${type}`;
      element.setAttribute('role', 'alert');
      element.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');

      // Icona
      const icon = this.getIcon(type);
      const iconEl = document.createElement('div');
      iconEl.className = 'toast-icon';
      iconEl.innerHTML = icon;

      // Contenuto
      const content = document.createElement('div');
      content.className = 'toast-content';
      content.textContent = message;

      // Azioni
      const actionsEl = document.createElement('div');
      actionsEl.className = 'toast-actions';

      // Bottone azione custom
      if (action) {
        const actionBtn = document.createElement('button');
        actionBtn.className = 'toast-action-btn';
        actionBtn.textContent = action.label;
        actionBtn.onclick = (e) => {
          e.stopPropagation();
          action.onClick();
          this.removeToast(toast);
        };
        actionsEl.appendChild(actionBtn);
      }

      // Bottone chiusura
      if (closable) {
        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '×';
        closeBtn.setAttribute('aria-label', 'Chiudi notifica');
        closeBtn.onclick = (e) => {
          e.stopPropagation();
          this.removeToast(toast);
        };
        actionsEl.appendChild(closeBtn);
      }

      element.appendChild(iconEl);
      element.appendChild(content);
      element.appendChild(actionsEl);

      const toast = {
        element,
        duration,
        timeoutId: null
      };

      // Pausa timer al hover
      element.addEventListener('mouseenter', () => {
        if (toast.timeoutId) {
          clearTimeout(toast.timeoutId);
          toast.timeoutId = null;
        }
      });

      element.addEventListener('mouseleave', () => {
        if (duration > 0) {
          toast.timeoutId = setTimeout(() => {
            this.removeToast(toast);
          }, 2000); // Continua dopo 2s
        }
      });

      return toast;
    }

    /**
     * Rimuove un toast
     */
    removeToast(toast) {
      if (!toast || !toast.element) return;

      const index = this.toasts.indexOf(toast);
      if (index > -1) {
        this.toasts.splice(index, 1);
      }

      if (toast.timeoutId) {
        clearTimeout(toast.timeoutId);
      }

      toast.element.classList.remove('toast-show');
      toast.element.classList.add('toast-hide');

      setTimeout(() => {
        if (toast.element && toast.element.parentNode) {
          toast.element.parentNode.removeChild(toast.element);
        }
      }, 300);
    }

    /**
     * Ottiene l'icona SVG per tipo
     */
    getIcon(type) {
      const icons = {
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
      };
      return icons[type] || icons.info;
    }

    /**
     * Rimuove tutti i toast
     */
    clearAll() {
      const toastsCopy = [...this.toasts];
      toastsCopy.forEach(toast => this.removeToast(toast));
    }
  }

  // Inizializza il toast manager
  const toastManager = new ToastManager();

  // API pubblica semplificata
  window.showToast = (options) => {
    if (typeof options === 'string') {
      options = { message: options };
    }
    return toastManager.show(options);
  };

  window.toast = {
    info: (message) => toastManager.show({ message, type: 'info' }),
    success: (message) => toastManager.show({ message, type: 'success' }),
    warning: (message) => toastManager.show({ message, type: 'warning' }),
    error: (message) => toastManager.show({ message, type: 'error' }),
    clear: () => toastManager.clearAll()
  };

  // Intercetta messaggi Django per convertirli in toast
  document.addEventListener('DOMContentLoaded', () => {
    const djangoMessages = document.querySelectorAll('.messages .alert');
    djangoMessages.forEach((alert) => {
      const message = alert.textContent.trim();
      const classList = alert.className;
      
      let type = 'info';
      if (classList.includes('alert-success')) type = 'success';
      else if (classList.includes('alert-warning')) type = 'warning';
      else if (classList.includes('alert-danger') || classList.includes('alert-error')) type = 'error';
      
      toastManager.show({ message, type });
      
      // Nascondi alert Django originale
      alert.style.display = 'none';
    });
  });

})();
