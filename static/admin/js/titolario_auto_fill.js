/**
 * Auto-fill per voci titolario intestate ad anagrafiche
 * 
 * Funzionalità:
 * A) Quando si seleziona un'anagrafica:
 *    - Codice → anagrafica.codice
 *    - Titolo → "Dossier {anagrafica.display_name}"
 *    - Pattern → {CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}
 * 
 * B) Quando si deseleziona anagrafica:
 *    - Pattern torna a default {CLI}-{TIT}-{ANNO}-{SEQ:03d}
 */

// Aspetta che django.jQuery sia disponibile
(function() {
    'use strict';

    // Costanti
    const PATTERN_CON_ANA = '{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}';
    const PATTERN_DEFAULT = '{CLI}-{TIT}-{ANNO}-{SEQ:03d}';

    // Aspetta che django.jQuery sia disponibile
    function waitForJQuery() {
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
            var $ = django.jQuery;
            
            $(document).ready(function() {
                // Verifica se siamo nella pagina corretta (add/change con form)
                // Skip per: lista, bulk creation, altre pagine senza form
                
                // 1. Check pagina bulk creation
                var isBulkCreationPage = window.location.pathname.includes('/bulk_creation/') ||
                                        (document.querySelector('h1') && 
                                         document.querySelector('h1').textContent.includes('Bulk Creation'));
                
                if (isBulkCreationPage) {
                    console.log('[TitolarioAutoFill] Pagina bulk creation rilevata, skip inizializzazione');
                    return;
                }
                
                // 2. Check se esiste il form di add/change (presenza campo anagrafica)
                var hasAnagraficaField = document.getElementById('id_anagrafica') !== null;
                
                if (!hasAnagraficaField) {
                    console.log('[TitolarioAutoFill] Form non presente (pagina lista o altra), skip inizializzazione');
                    return;
                }
                
                console.log('[TitolarioAutoFill] Pagina add/change rilevata, inizializzazione...');
                // Aspetta che Select2 sia pronto
                setTimeout(function() { initAutoFill($); }, 500);
            });
        } else {
            setTimeout(waitForJQuery, 100);
        }
    }

    waitForJQuery();

    function initAutoFill($) {
        // Selettori
        const $anagraficaField = $('#id_anagrafica');
        const $codiceField = $('#id_codice');
        const $titoloField = $('#id_titolo');
        const $patternField = $('#id_pattern_codice');

        if (!$anagraficaField.length) {
            // Questo non dovrebbe più accadere grazie al check precedente
            console.warn('[TitolarioAutoFill] WARN: Campo anagrafica non trovato (non dovrebbe accadere)');
            return;
        }

        console.log('[TitolarioAutoFill] Setup listeners per auto-fill');

        /**
         * Fetch dati anagrafica via AJAX
         */
        function fetchAnagraficaData(anagraficaId) {
            if (!anagraficaId) {
                return Promise.resolve(null);
            }

            console.log('[TitolarioAutoFill] Fetching anagrafica ID:', anagraficaId);

            return $.ajax({
                url: '/api/v1/anagrafiche/' + anagraficaId + '/',
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                xhrFields: {
                    withCredentials: true
                }
            }).then(function(data) {
                console.log('[TitolarioAutoFill] Dati ricevuti:', data);
                return data;
            }).catch(function(error) {
                console.error('[TitolarioAutoFill] Errore fetch:', error);
                return null;
            });
        }

        /**
         * Auto-fill campi quando anagrafica selezionata
         */
        function autoFillFields(anagraficaData) {
            console.log('[TitolarioAutoFill] Auto-fill con dati:', anagraficaData);

            if (!anagraficaData) {
                // Deselezionata: ripristina pattern default
                if ($patternField.val() === PATTERN_CON_ANA) {
                    $patternField.val(PATTERN_DEFAULT);
                    console.log('[TitolarioAutoFill] Pattern ripristinato a default');
                }
                return;
            }

            // Determina se siamo in modalità creazione (campi vuoti o già pre-compilati)
            const isNewRecord = !window.location.pathname.match(/\/\d+\/change\//);
            const codiceEmpty = !$codiceField.val() || $codiceField.val().trim() === '';
            const titoloEmpty = !$titoloField.val() || $titoloField.val().trim() === '';

            console.log('[TitolarioAutoFill] isNewRecord:', isNewRecord, 'codiceEmpty:', codiceEmpty, 'titoloEmpty:', titoloEmpty);

            // AUTO-FILL CODICE (solo se vuoto o nuovo record)
            if (codiceEmpty || isNewRecord) {
                if (anagraficaData.codice) {
                    $codiceField.val(anagraficaData.codice);
                    $codiceField.addClass('autofilled');
                    setTimeout(function() {
                        $codiceField.removeClass('autofilled');
                    }, 2000);
                    console.log('[TitolarioAutoFill] Codice auto-compilato:', anagraficaData.codice);
                }
            }

            // AUTO-FILL TITOLO (solo se vuoto o nuovo record)
            if (titoloEmpty || isNewRecord) {
                let displayName = '';
                
                // Costruisci display_name in base al tipo
                if (anagraficaData.tipo === 'PF') {
                    // Persona fisica
                    displayName = anagraficaData.cognome + ' ' + anagraficaData.nome;
                } else {
                    // Persona giuridica
                    displayName = anagraficaData.ragione_sociale || anagraficaData.nome || '';
                }

                if (displayName.trim()) {
                    const titolo = 'Dossier ' + displayName.trim();
                    $titoloField.val(titolo);
                    $titoloField.addClass('autofilled');
                    setTimeout(function() {
                        $titoloField.removeClass('autofilled');
                    }, 2000);
                    console.log('[TitolarioAutoFill] Titolo auto-compilato:', titolo);
                }
            }

            // AUTO-UPDATE PATTERN (sempre, se è ancora al default)
            if (!$patternField.val() || $patternField.val() === PATTERN_DEFAULT) {
                $patternField.val(PATTERN_CON_ANA);
                $patternField.addClass('autofilled');
                setTimeout(function() {
                    $patternField.removeClass('autofilled');
                }, 2000);
                console.log('[TitolarioAutoFill] Pattern aggiornato a:', PATTERN_CON_ANA);
            }
        }

        /**
         * Handler cambio anagrafica
         * Supporta sia change normale che select2:select
         */
        function handleAnagraficaChange() {
            const anagraficaId = $anagraficaField.val();
            console.log('[TitolarioAutoFill] Anagrafica cambiata:', anagraficaId);

            if (anagraficaId) {
                fetchAnagraficaData(anagraficaId).then(autoFillFields);
            } else {
                autoFillFields(null);
            }
        }

        // Event listeners
        // Per Select2 (Django admin default)
        $anagraficaField.on('select2:select', handleAnagraficaChange);
        $anagraficaField.on('select2:clear', function() {
            autoFillFields(null);
        });

        // Fallback per change normale (se Select2 non attivo)
        $anagraficaField.on('change', handleAnagraficaChange);

        // Aggiungi stile per feedback visivo
        if (!$('#titolario-autofill-style').length) {
            $('<style id="titolario-autofill-style">')
                .text(`.autofilled {
                    background-color: #e8f5e9 !important;
                    transition: background-color 0.3s ease;
                }`)
                .appendTo('head');
        }

        console.log('[TitolarioAutoFill] Setup completato');
    }

})();
