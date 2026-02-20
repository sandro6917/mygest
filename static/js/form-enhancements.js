/**
 * Form Enhancements
 * Migliora l'esperienza utente nei form con validazione, feedback e funzionalità aggiuntive
 */

(function() {
  'use strict';

  class FormEnhancer {
    constructor() {
      this.forms = [];
      this.init();
    }

    init() {
      document.addEventListener('DOMContentLoaded', () => {
        this.enhanceAllForms();
        this.setupAutoSave();
      });
    }

    /**
     * Migliora tutti i form nella pagina
     */
    enhanceAllForms() {
      const forms = document.querySelectorAll('form[data-enhance="true"]');
      forms.forEach(form => this.enhanceForm(form));
    }

    /**
     * Migliora un singolo form
     */
    enhanceForm(form) {
      // Validazione real-time
      this.setupRealTimeValidation(form);
      
      // Loading state su submit
      this.setupSubmitLoading(form);
      
      // Conferma prima di lasciare se modificato
      this.setupUnsavedWarning(form);
      
      // Caratteri rimanenti per textarea
      this.setupCharacterCount(form);
      
      this.forms.push(form);
    }

    /**
     * Setup validazione real-time
     */
    setupRealTimeValidation(form) {
      const inputs = form.querySelectorAll('input, textarea, select');
      
      inputs.forEach(input => {
        // Validazione su blur
        input.addEventListener('blur', () => {
          this.validateField(input);
        });

        // Validazione su input per alcuni tipi
        if (['email', 'tel', 'url'].includes(input.type)) {
          let debounceTimer;
          input.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
              this.validateField(input);
            }, 500);
          });
        }

        // Rimuovi errore su focus
        input.addEventListener('focus', () => {
          this.clearFieldError(input);
        });
      });
    }

    /**
     * Valida un singolo campo
     */
    validateField(field) {
      let isValid = true;
      let message = '';

      // Required
      if (field.hasAttribute('required') && !field.value.trim()) {
        isValid = false;
        message = 'Campo obbligatorio';
      }

      // Email
      if (field.type === 'email' && field.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(field.value)) {
          isValid = false;
          message = 'Email non valida';
        }
      }

      // Codice Fiscale
      if (field.name === 'codice_fiscale' && field.value) {
        const cfRegex = /^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$/i;
        if (!cfRegex.test(field.value)) {
          isValid = false;
          message = 'Codice fiscale non valido';
        }
      }

      // Partita IVA
      if (field.name === 'partita_iva' && field.value) {
        const pivaRegex = /^[0-9]{11}$/;
        if (!pivaRegex.test(field.value)) {
          isValid = false;
          message = 'Partita IVA non valida (11 cifre)';
        }
      }

      // Telefono
      if (field.type === 'tel' && field.value) {
        const telRegex = /^[\d\s\+\-\(\)]+$/;
        if (!telRegex.test(field.value)) {
          isValid = false;
          message = 'Numero di telefono non valido';
        }
      }

      // Min/Max length
      if (field.minLength && field.value.length < field.minLength) {
        isValid = false;
        message = `Minimo ${field.minLength} caratteri`;
      }
      if (field.maxLength && field.value.length > field.maxLength) {
        isValid = false;
        message = `Massimo ${field.maxLength} caratteri`;
      }

      // Mostra risultato
      if (!isValid) {
        this.showFieldError(field, message);
      } else if (field.value) {
        this.showFieldSuccess(field);
      }

      return isValid;
    }

    /**
     * Mostra errore su campo
     */
    showFieldError(field, message) {
      this.clearFieldFeedback(field);
      
      field.classList.add('field-error');
      field.classList.remove('field-success');
      
      const feedback = document.createElement('div');
      feedback.className = 'field-feedback field-feedback-error';
      feedback.textContent = message;
      feedback.setAttribute('role', 'alert');
      
      field.parentNode.appendChild(feedback);
    }

    /**
     * Mostra successo su campo
     */
    showFieldSuccess(field) {
      this.clearFieldFeedback(field);
      
      field.classList.remove('field-error');
      field.classList.add('field-success');
      
      const feedback = document.createElement('div');
      feedback.className = 'field-feedback field-feedback-success';
      feedback.innerHTML = '✓ Valido';
      
      field.parentNode.appendChild(feedback);
    }

    /**
     * Pulisce errori campo
     */
    clearFieldError(field) {
      field.classList.remove('field-error');
      this.clearFieldFeedback(field);
    }

    /**
     * Pulisce feedback campo
     */
    clearFieldFeedback(field) {
      const existingFeedback = field.parentNode.querySelector('.field-feedback');
      if (existingFeedback) {
        existingFeedback.remove();
      }
    }

    /**
     * Setup loading state su submit
     */
    setupSubmitLoading(form) {
      form.addEventListener('submit', (e) => {
        const submitBtn = form.querySelector('[type="submit"]');
        if (!submitBtn) return;

        // Disabilita button e mostra loading
        submitBtn.disabled = true;
        const originalText = submitBtn.textContent;
        
        submitBtn.innerHTML = `
          <span class="spinner spinner-sm"></span>
          <span style="margin-left:8px">Salvataggio...</span>
        `;

        // Ripristina dopo 10 secondi (fallback)
        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }, 10000);
      });
    }

    /**
     * Avvisa se ci sono modifiche non salvate
     */
    setupUnsavedWarning(form) {
      let formModified = false;
      
      form.addEventListener('input', () => {
        formModified = true;
      });

      form.addEventListener('submit', () => {
        formModified = false;
      });

      window.addEventListener('beforeunload', (e) => {
        if (formModified) {
          e.preventDefault();
          e.returnValue = 'Ci sono modifiche non salvate. Vuoi davvero uscire?';
          return e.returnValue;
        }
      });
    }

    /**
     * Contatore caratteri per textarea
     */
    setupCharacterCount(form) {
      const textareas = form.querySelectorAll('textarea[maxlength]');
      
      textareas.forEach(textarea => {
        const maxLength = textarea.maxLength;
        const counter = document.createElement('div');
        counter.className = 'character-count';
        
        const updateCounter = () => {
          const remaining = maxLength - textarea.value.length;
          counter.textContent = `${remaining} caratteri rimanenti`;
          
          if (remaining < 20) {
            counter.style.color = '#f44336';
          } else if (remaining < 50) {
            counter.style.color = '#ff9800';
          } else {
            counter.style.color = 'var(--text-secondary)';
          }
        };
        
        textarea.parentNode.appendChild(counter);
        textarea.addEventListener('input', updateCounter);
        updateCounter();
      });
    }

    /**
     * Setup auto-save bozze (se abilitato)
     */
    setupAutoSave() {
      const autoSaveForms = document.querySelectorAll('form[data-autosave="true"]');
      
      autoSaveForms.forEach(form => {
        const formId = form.id || 'form-' + Date.now();
        let saveTimer;

        form.addEventListener('input', () => {
          clearTimeout(saveTimer);
          saveTimer = setTimeout(() => {
            this.autoSaveForm(form, formId);
          }, 2000);
        });

        // Ripristina dati salvati
        this.restoreFormData(form, formId);
      });
    }

    /**
     * Salva form in localStorage
     */
    autoSaveForm(form, formId) {
      const formData = new FormData(form);
      const data = {};
      
      formData.forEach((value, key) => {
        data[key] = value;
      });

      try {
        localStorage.setItem(`form_draft_${formId}`, JSON.stringify(data));
        
        if (window.toast) {
          window.toast.info('Bozza salvata automaticamente');
        }
      } catch (e) {
        console.warn('Impossibile salvare bozza:', e);
      }
    }

    /**
     * Ripristina dati form da localStorage
     */
    restoreFormData(form, formId) {
      try {
        const savedData = localStorage.getItem(`form_draft_${formId}`);
        if (!savedData) return;

        const data = JSON.parse(savedData);
        
        Object.keys(data).forEach(key => {
          const field = form.querySelector(`[name="${key}"]`);
          if (field) {
            field.value = data[key];
          }
        });

        if (window.toast) {
          window.toast.info('Bozza ripristinata', {
            action: {
              label: 'Elimina',
              onClick: () => {
                localStorage.removeItem(`form_draft_${formId}`);
                form.reset();
              }
            }
          });
        }
      } catch (e) {
        console.warn('Impossibile ripristinare bozza:', e);
      }
    }

    /**
     * Pulisce bozza salvata
     */
    static clearDraft(formId) {
      localStorage.removeItem(`form_draft_${formId}`);
    }
  }

  // Inizializza
  window.formEnhancer = new FormEnhancer();

  // API pubblica
  window.validateForm = (formElement) => {
    const enhancer = window.formEnhancer;
    let isValid = true;
    
    const inputs = formElement.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      if (!enhancer.validateField(input)) {
        isValid = false;
      }
    });
    
    return isValid;
  };

})();
