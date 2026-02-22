# Sistema Responsive MyGest

## Panoramica

MyGest utilizza un sistema responsive basato su **Material-UI (MUI)** con breakpoint standard e supporto completo per dispositivi mobili, tablet e desktop.

## Breakpoint

Il sistema utilizza i breakpoint standard di Material-UI:

| Nome | Dimensione | Dispositivo Tipico |
|------|------------|-------------------|
| `xs` | 0px - 599px | Mobile portrait |
| `sm` | 600px - 899px | Mobile landscape / Tablet portrait |
| `md` | 900px - 1199px | Tablet landscape / Small desktop |
| `lg` | 1200px - 1535px | Desktop |
| `xl` | 1536px+ | Large desktop |

## Configurazione

### Tema Material-UI

Il tema responsive è configurato in `/frontend/src/theme/index.ts` e include:

- **Typography responsive**: Font sizes che si adattano automaticamente ai breakpoint
- **Spacing adattivo**: Padding e margin che si riducono su mobile
- **Component overrides**: Personalizzazioni per Button, Card, Table, Dialog, etc.
- **responsiveFontSizes()**: Scaling automatico dei font

### Viewport Meta Tag

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes" />
```

## Utilizzo

### 1. Hook useResponsive (Consigliato)

Usa il custom hook per logica condizionale basata sul dispositivo:

```typescript
import { useResponsive } from '@/hooks/useResponsive';

function MyComponent() {
  const { isMobile, isTablet, isDesktop } = useResponsive();
  
  return (
    <Box>
      {isMobile && <MobileView />}
      {isTablet && <TabletView />}
      {isDesktop && <DesktopView />}
    </Box>
  );
}
```

**API completa del hook:**

```typescript
const {
  // Categorie principali
  isMobile,        // xs (0-599px)
  isTablet,        // sm (600-899px)
  isTabletLandscape, // md (900-1199px)
  isDesktop,       // lg (1200-1535px)
  isLargeDesktop,  // xl (1536px+)
  
  // Breakpoint specifici
  isXs, isSm, isMd, isLg, isXl,
  
  // Up/Down
  isSmUp, isMdUp, isLgUp,
  isSmDown, isMdDown, isLgDown,
  
  // Orientamento
  isPortrait,
  isLandscape,
  
  // Getter
  getCurrentBreakpoint, // () => 'xs' | 'sm' | 'md' | 'lg' | 'xl'
} = useResponsive();
```

### 2. MUI useMediaQuery (Avanzato)

Per query più specifiche:

```typescript
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

function MyComponent() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  
  return <Box>{/* ... */}</Box>;
}
```

### 3. MUI Grid System

Usa il Grid responsive di Material-UI:

```typescript
import { Grid } from '@mui/material';

function DashboardPage() {
  return (
    <Grid container spacing={3}>
      {/* 12 colonne su mobile, 6 su tablet, 3 su desktop */}
      <Grid item xs={12} sm={6} lg={3}>
        <StatCard title="Pratiche" value={120} />
      </Grid>
      <Grid item xs={12} sm={6} lg={3}>
        <StatCard title="Documenti" value={450} />
      </Grid>
      <Grid item xs={12} sm={6} lg={3}>
        <StatCard title="Clienti" value={85} />
      </Grid>
      <Grid item xs={12} sm={6} lg={3}>
        <StatCard title="Scadenze" value={12} />
      </Grid>
    </Grid>
  );
}
```

### 4. MUI Box con sx prop

Usa la prop `sx` per styling responsive inline:

```typescript
import { Box, Typography } from '@mui/material';

function MyComponent() {
  return (
    <Box
      sx={{
        padding: { xs: 2, sm: 3, md: 4 }, // 16px, 24px, 32px
        fontSize: { xs: '0.875rem', md: '1rem' },
        display: { xs: 'block', md: 'flex' },
        flexDirection: { md: 'row', lg: 'column' },
      }}
    >
      <Typography
        variant="h4"
        sx={{
          fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
        }}
      >
        Titolo Responsive
      </Typography>
    </Box>
  );
}
```

### 5. Container con maxWidth

```typescript
import { Container } from '@mui/material';

function PageLayout() {
  return (
    <Container maxWidth="xl"> {/* false | 'xs' | 'sm' | 'md' | 'lg' | 'xl' */}
      {/* Content with max-width constraint */}
    </Container>
  );
}
```

### 6. CSS Media Queries

Nel file `global.css` sono definite media query personalizzate:

```css
/* Mobile (xs) */
@media (max-width: 599px) {
  .hide-on-mobile {
    display: none !important;
  }
  
  :root {
    --font-size-base: 0.875rem;
  }
}

/* Tablet (sm) */
@media (min-width: 600px) and (max-width: 899px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop (md+) */
@media (min-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

## Best Practices

### 1. Mobile-First Approach

Progetta prima per mobile, poi aggiungi feature per schermi più grandi:

```typescript
<Box
  sx={{
    // Default: mobile
    display: 'block',
    padding: 2,
    
    // Tablet e superiori
    sm: {
      display: 'flex',
      padding: 3,
    },
    
    // Desktop
    md: {
      padding: 4,
    },
  }}
>
```

### 2. Nascondi Colonne Non Essenziali su Mobile

```typescript
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useResponsive } from '@/hooks/useResponsive';

function MyTable() {
  const { isMobile } = useResponsive();
  
  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'nome', headerName: 'Nome', flex: 1 },
    { 
      field: 'descrizione', 
      headerName: 'Descrizione', 
      flex: 1,
      hide: isMobile, // Nascondi su mobile
    },
    { 
      field: 'data', 
      headerName: 'Data', 
      width: 120,
      hide: isMobile,
    },
  ];
  
  return <DataGrid columns={columns} rows={rows} />;
}
```

### 3. Dialog/Modal Responsive

```typescript
import { Dialog, useMediaQuery, useTheme } from '@mui/material';

function MyDialog({ open, onClose }) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  
  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullScreen} // Full screen su mobile
      maxWidth="md"
    >
      {/* Content */}
    </Dialog>
  );
}
```

### 4. Stack vs Grid

- **Stack**: Per layout semplici 1D (verticale/orizzontale)
- **Grid**: Per layout complessi 2D

```typescript
import { Stack, Grid } from '@mui/material';

// Stack - layout semplice
<Stack 
  direction={{ xs: 'column', sm: 'row' }} 
  spacing={2}
>
  <Button>Azione 1</Button>
  <Button>Azione 2</Button>
</Stack>

// Grid - layout complesso
<Grid container spacing={2}>
  <Grid item xs={12} md={6}>...</Grid>
  <Grid item xs={12} md={6}>...</Grid>
</Grid>
```

### 5. Tipografia Responsive

Usa le varianti MUI che sono già responsive:

```typescript
<Typography variant="h1">Titolo Grande</Typography>
<Typography variant="h4">Sottotitolo</Typography>
<Typography variant="body1">Testo normale</Typography>
```

Oppure personalizza:

```typescript
<Typography
  sx={{
    fontSize: { xs: '1rem', sm: '1.25rem', md: '1.5rem' },
    fontWeight: { xs: 400, md: 600 },
  }}
>
  Testo personalizzato
</Typography>
```

## Test Responsive

### Browser DevTools

1. Apri DevTools (F12)
2. Attiva "Toggle device toolbar" (Ctrl+Shift+M)
3. Seleziona dispositivi preset o dimensioni personalizzate
4. Testa tutte le breakpoint:
   - iPhone SE (375px)
   - iPad (768px)
   - Desktop (1024px, 1440px)

### Test Reali

- **Mobile**: iPhone, Android phones
- **Tablet**: iPad, Android tablets
- **Desktop**: 1920x1080, 2560x1440, 4K

## Troubleshooting

### Il layout non si adatta

1. Verifica che il viewport meta tag sia presente
2. Usa le Developer Tools per ispezionare gli stili applicati
3. Controlla che il ThemeProvider avvolga l'app
4. Verifica che i breakpoint siano corretti

### Font troppo piccoli/grandi

Usa `responsiveFontSizes()` nel tema (già configurato) o personalizza:

```typescript
<Typography
  sx={{
    fontSize: 'clamp(0.875rem, 2vw, 1.5rem)', // Min, preferito, max
  }}
>
```

### Performance su mobile

- Usa lazy loading per componenti pesanti
- Riduci bundle size con code splitting
- Ottimizza immagini (WebP, lazy loading)
- Usa virtualization per liste lunghe (react-window)

## Esempi Pratici

### Dashboard Responsive

```typescript
function DashboardPage() {
  const { isMobile } = useResponsive();
  
  return (
    <Container maxWidth="xl">
      <Stack spacing={3}>
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            justifyContent: 'space-between',
            alignItems: { xs: 'stretch', sm: 'center' },
            gap: 2,
          }}
        >
          <Typography variant="h4">Dashboard</Typography>
          <Button
            variant="contained"
            fullWidth={isMobile}
            startIcon={<AddIcon />}
          >
            Nuova Pratica
          </Button>
        </Box>
        
        {/* Stats Grid */}
        <Grid container spacing={3}>
          {stats.map((stat) => (
            <Grid item xs={12} sm={6} lg={3} key={stat.id}>
              <StatCard {...stat} />
            </Grid>
          ))}
        </Grid>
        
        {/* Charts */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <ChartCard />
          </Grid>
          <Grid item xs={12} md={4}>
            <RecentActivity />
          </Grid>
        </Grid>
      </Stack>
    </Container>
  );
}
```

## Risorse

- [Material-UI Breakpoints](https://mui.com/material-ui/customization/breakpoints/)
- [Material-UI useMediaQuery](https://mui.com/material-ui/react-use-media-query/)
- [Material-UI Grid](https://mui.com/material-ui/react-grid/)
- [Responsive Font Sizes](https://mui.com/material-ui/customization/theming/#responsivefontsizes-theme-options-theme)
