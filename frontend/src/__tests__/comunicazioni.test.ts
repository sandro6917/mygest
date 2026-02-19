/**
 * Test per verificare il setup della UI Comunicazioni
 * Esegui questo file per verificare che tutte le dipendenze siano corrette
 */

import { describe, it, expect } from '@jest/globals';

describe('Comunicazioni UI Setup', () => {
  it('dovrebbe importare correttamente i types', () => {
    const {
      TIPO_COMUNICAZIONE_CHOICES,
      DIREZIONE_CHOICES,
      STATO_CHOICES,
    } = require('../types/comunicazioni');

    expect(TIPO_COMUNICAZIONE_CHOICES).toHaveLength(3);
    expect(DIREZIONE_CHOICES).toHaveLength(2);
    expect(STATO_CHOICES).toHaveLength(3);
  });

  it('dovrebbe avere le route configurate', () => {
    const { router } = require('../routes');
    expect(router).toBeDefined();
  });

  it('dovrebbe avere il client API configurato', () => {
    const { comunicazioniApi } = require('../api/comunicazioni');
    expect(comunicazioniApi.list).toBeDefined();
    expect(comunicazioniApi.get).toBeDefined();
    expect(comunicazioniApi.create).toBeDefined();
    expect(comunicazioniApi.update).toBeDefined();
    expect(comunicazioniApi.delete).toBeDefined();
    expect(comunicazioniApi.send).toBeDefined();
  });
});

// Export per evitare errori TypeScript
export {};
