/**
 * Theme Manager - Dark/Light Mode Toggle
 * Gestisce il cambio tema con persistenza su localStorage
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'mygest-theme';
  const THEME_ATTR = 'data-theme';
  
  class ThemeManager {
    constructor() {
      this.currentTheme = this.getStoredTheme() || this.getPreferredTheme();
      this.init();
    }

    /**
     * Inizializza il tema e imposta i listener
     */
    init() {
      // Applica tema immediatamente per evitare flash
      this.applyTheme(this.currentTheme);
      
      // Setup toggle button
      document.addEventListener('DOMContentLoaded', () => {
        this.setupToggleButton();
        this.setupSystemThemeListener();
      });
    }

    /**
     * Ottiene il tema salvato in localStorage
     */
    getStoredTheme() {
      try {
        return localStorage.getItem(STORAGE_KEY);
      } catch (e) {
        console.warn('localStorage non disponibile:', e);
        return null;
      }
    }

    /**
     * Ottiene il tema preferito dal sistema operativo
     */
    getPreferredTheme() {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
      return 'light';
    }

    /**
     * Salva il tema in localStorage
     */
    saveTheme(theme) {
      try {
        localStorage.setItem(STORAGE_KEY, theme);
      } catch (e) {
        console.warn('Impossibile salvare tema:', e);
      }
    }

    /**
     * Applica il tema al documento
     */
    applyTheme(theme) {
      document.documentElement.setAttribute(THEME_ATTR, theme);
      this.currentTheme = theme;
      this.saveTheme(theme);
      
      // Emetti evento custom per altri componenti
      window.dispatchEvent(new CustomEvent('themechange', { 
        detail: { theme } 
      }));
    }

    /**
     * Toggle tra light e dark mode
     */
    toggleTheme() {
      const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
      this.applyTheme(newTheme);
      this.updateToggleButton();
      
      // Feedback visivo
      this.showThemeChangeFeedback(newTheme);
    }

    /**
     * Setup del bottone toggle
     */
    setupToggleButton() {
      const toggleBtn = document.getElementById('theme-toggle');
      if (!toggleBtn) {
        console.warn('Theme toggle button non trovato');
        return;
      }

      // Click listener
      toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleTheme();
      });

      // Keyboard accessibility
      toggleBtn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.toggleTheme();
        }
      });

      // Inizializza icona corretta
      this.updateToggleButton();
    }

    /**
     * Aggiorna l'icona del bottone toggle
     */
    updateToggleButton() {
      const toggleBtn = document.getElementById('theme-toggle');
      if (!toggleBtn) return;

      const isDark = this.currentTheme === 'dark';
      toggleBtn.setAttribute('aria-label', 
        isDark ? 'Passa al tema chiaro' : 'Passa al tema scuro'
      );
      toggleBtn.title = isDark ? 'Tema chiaro' : 'Tema scuro';
    }

    /**
     * Ascolta cambiamenti tema sistema operativo
     */
    setupSystemThemeListener() {
      if (!window.matchMedia) return;

      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      // Listener per cambiamenti
      const handleChange = (e) => {
        // Solo se l'utente non ha impostato preferenza esplicita
        if (!this.getStoredTheme()) {
          const newTheme = e.matches ? 'dark' : 'light';
          this.applyTheme(newTheme);
          this.updateToggleButton();
        }
      };

      // Modern API
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleChange);
      } else {
        // Fallback per browser vecchi
        mediaQuery.addListener(handleChange);
      }
    }

    /**
     * Mostra feedback visivo del cambio tema
     */
    showThemeChangeFeedback(theme) {
      // Toast notification se disponibile
      if (window.showToast) {
        window.showToast({
          message: `Tema ${theme === 'dark' ? 'scuro' : 'chiaro'} attivato`,
          type: 'info',
          duration: 2000
        });
      }
    }

    /**
     * Reset tema alle impostazioni di default
     */
    resetTheme() {
      const defaultTheme = this.getPreferredTheme();
      this.applyTheme(defaultTheme);
      this.updateToggleButton();
    }
  }

  // Inizializza il theme manager
  window.themeManager = new ThemeManager();

  // Esponi API pubblica
  window.setTheme = (theme) => {
    if (theme === 'dark' || theme === 'light') {
      window.themeManager.applyTheme(theme);
      window.themeManager.updateToggleButton();
    }
  };

  window.getTheme = () => {
    return window.themeManager.currentTheme;
  };

  window.toggleTheme = () => {
    window.themeManager.toggleTheme();
  };

})();
