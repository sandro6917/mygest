/**
 * JavaScript per Help Admin Form
 */

(function() {
    'use strict';
    
    // Aggiungi badge alle sezioni
    document.addEventListener('DOMContentLoaded', function() {
        
        // Badge per sezioni auto-generate
        const autoSections = [
            'Pattern e Nomi File',
            'Dati Tecnici (Non Modificare)'
        ];
        
        autoSections.forEach(function(sectionTitle) {
            const h2Elements = document.querySelectorAll('h2');
            h2Elements.forEach(function(h2) {
                if (h2.textContent.trim() === sectionTitle) {
                    const badge = document.createElement('span');
                    badge.className = 'auto-generated-badge';
                    badge.textContent = '🤖 AUTO';
                    badge.title = 'Questa sezione viene generata automaticamente';
                    h2.appendChild(badge);
                }
            });
        });
        
        // Badge per sezioni manuali
        const manualSections = [
            'Help - Descrizione',
            'Help - Quando Usare',
            'Help - Relazione Fascicoli',
            'Help - Workflow',
            'Help - Note Speciali',
            'Help - FAQ'
        ];
        
        manualSections.forEach(function(sectionTitle) {
            const h2Elements = document.querySelectorAll('h2');
            h2Elements.forEach(function(h2) {
                if (h2.textContent.trim() === sectionTitle) {
                    const badge = document.createElement('span');
                    badge.className = 'manual-badge';
                    badge.textContent = '📝 MANUALE';
                    badge.title = 'Questa sezione richiede input manuale';
                    h2.appendChild(badge);
                }
            });
        });
        
        // Validazione FAQ JSON real-time
        const faqField = document.querySelector('#id_help_faq_json');
        if (faqField) {
            faqField.addEventListener('blur', function() {
                try {
                    if (this.value.trim()) {
                        const json = JSON.parse(this.value);
                        if (!Array.isArray(json)) {
                            alert('FAQ deve essere una lista (array JSON)');
                            this.style.borderColor = 'red';
                        } else {
                            // Valida struttura
                            let valid = true;
                            json.forEach(function(item) {
                                if (!item.domanda || !item.risposta) {
                                    valid = false;
                                }
                            });
                            
                            if (!valid) {
                                alert('Ogni FAQ deve avere "domanda" e "risposta"');
                                this.style.borderColor = 'red';
                            } else {
                                this.style.borderColor = 'green';
                            }
                        }
                    }
                } catch (e) {
                    alert('JSON non valido: ' + e.message);
                    this.style.borderColor = 'red';
                }
            });
        }
        
        // Aggiungi helper per liste multilinea
        const multilineFields = [
            'help_quando_usare_casi',
            'help_quando_usare_non_usare',
            'help_relazione_fascicoli_best_practices',
            'help_workflow_stati',
            'help_note_attenzioni',
            'help_note_suggerimenti',
            'help_note_vincoli'
        ];
        
        multilineFields.forEach(function(fieldId) {
            const field = document.querySelector('#id_' + fieldId);
            if (field) {
                const helpText = field.parentElement.querySelector('.help');
                if (helpText) {
                    helpText.innerHTML += '<br><em>Suggerimento: scrivi un elemento per riga. Il carattere "- " iniziale è opzionale.</em>';
                }
            }
        });
        
        // Aggiungi link wizard
        const faqFieldset = document.querySelector('.module:has(#id_help_faq_json)');
        if (faqFieldset) {
            const wizardButton = document.createElement('a');
            wizardButton.className = 'wizard-link';
            wizardButton.href = '#';
            wizardButton.innerHTML = '🧙‍♂️ Apri Wizard CLI per editing avanzato';
            wizardButton.onclick = function(e) {
                e.preventDefault();
                
                // Ottieni il codice tipo documento
                const codiceField = document.querySelector('#id_codice');
                const codice = codiceField ? codiceField.value : '';
                
                const command = codice 
                    ? `python manage.py configure_help_wizard --tipo ${codice}`
                    : 'python manage.py configure_help_wizard';
                
                const message = `Per editing avanzato dell'help, usa il wizard CLI:\n\n${command}\n\nDa eseguire nel terminale del server.`;
                
                alert(message);
                
                // Copia negli appunti (se supportato)
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(command);
                    alert('Comando copiato negli appunti!');
                }
            };
            
            const description = faqFieldset.querySelector('.description');
            if (description) {
                description.appendChild(document.createElement('br'));
                description.appendChild(wizardButton);
            }
        }
        
    });
    
})();
