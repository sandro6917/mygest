# 🔧 Fix Autocomplete - Selezione valore non salvata

## ✅ Problema Risolto

Quando si selezionava un'opzione dal dropdown autocomplete con Portal, il valore non veniva salvato correttamente. Il click veniva intercettato dal `handleClickOutside` prima che il `handleSelect` potesse essere eseguito.

## 🐛 Causa del Problema

1. Il Portal rende il dropdown nel `<body>`, fuori dal DOM del componente
2. Il `handleClickOutside` controlla se il click è dentro `wrapperRef`
3. Poiché il dropdown è nel `<body>`, il click viene considerato "fuori" e chiude il dropdown
4. Il dropdown si chiude **prima** che l'evento `onClick` di selezione venga processato

## 🔧 Soluzione Implementata

### 1. AutocompletePortal con forwardRef

Aggiunto `forwardRef` e `useImperativeHandle` per esporre il riferimento al DOM element del portal.

```tsx
export interface AutocompletePortalRef {
  portalElement: HTMLDivElement | null;
}

export const AutocompletePortal = forwardRef<AutocompletePortalRef, AutocompletePortalProps>((props, ref) => {
  const portalRef = useRef<HTMLDivElement>(null);
  
  useImperativeHandle(ref, () => ({
    portalElement: portalRef.current
  }));
  
  // ...
});
```

### 2. Aggiornato handleClickOutside

Modificato per escludere i click sul portal element:

```tsx
const portalRef = useRef<AutocompletePortalRef>(null);

useEffect(() => {
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as Node;
    
    // Non chiudere se il click è sul wrapper
    if (wrapperRef.current && wrapperRef.current.contains(target)) {
      return;
    }
    
    // Non chiudere se il click è sul portal dropdown
    if (portalRef.current?.portalElement?.contains(target)) {
      return;
    }
    
    setIsOpen(false);
  }
  // ...
}, []);
```

### 3. Aggiunto ref al Portal

```tsx
<AutocompletePortal ref={portalRef} isOpen={isOpen} anchorRef={wrapperRef}>
  {/* contenuto */}
</AutocompletePortal>
```

## 📦 File Modificati

```
frontend/src/components/
├── AutocompletePortal.tsx          [AGGIORNATO - forwardRef]
├── ClienteAutocomplete.tsx         [AGGIORNATO - handleClickOutside + ref]
├── PraticheTipoAutocomplete.tsx    [AGGIORNATO - handleClickOutside + ref]
└── FascicoloAutocomplete.tsx       [AGGIORNATO - handleClickOutside + ref]
```

## 🧪 Come Testare

1. Vai su `http://localhost:5173/pratiche/nuovo`
2. Clicca su "Tipo Pratica" e digita qualcosa (es. "IVA")
3. Clicca su un'opzione nel dropdown
4. ✅ Il valore dovrebbe essere selezionato e salvato
5. ✅ Il dropdown dovrebbe chiudersi
6. ✅ Il campo dovrebbe mostrare il tipo selezionato (con bordo blu)

## 🎯 Test Aggiuntivi

- ✅ Click fuori dal dropdown → chiude correttamente
- ✅ Click sull'input → riapre dropdown
- ✅ Selezione → salva valore e chiude
- ✅ Pulsante "✕" → cancella selezione
- ✅ Form submit → valore presente

## 💡 Spiegazione Tecnica

Il problema era una **race condition** tra:
1. `mousedown` event → `handleClickOutside` → `setIsOpen(false)`
2. `click` event → `handleSelect` → `onChange(value)`

Con il Portal renderizzato nel `<body>`, il `mousedown` arrivava prima e chiudeva il dropdown, impedendo al `click` di essere processato.

La soluzione verifica se il target del click è **dentro il portal element** prima di chiudere il dropdown.

## 🚀 Deploy

I file sono pronti per commit e deploy.

---

**Status**: ✅ COMPLETATO  
**Test**: ✅ Richiesto test manuale  
**Breaking Changes**: ❌ NESSUNO
