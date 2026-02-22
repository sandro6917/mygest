import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

/**
 * Hook personalizzato per gestire i breakpoint responsive di Material-UI
 * 
 * @example
 * const { isMobile, isTablet, isDesktop } = useResponsive();
 * 
 * if (isMobile) {
 *   // Logica per mobile
 * }
 */
export function useResponsive() {
  const theme = useTheme();
  
  // xs: 0-599px (mobile)
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // sm: 600-899px (tablet portrait)
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  
  // md: 900-1199px (tablet landscape / small desktop)
  const isTabletLandscape = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  
  // lg: 1200-1535px (desktop)
  const isDesktop = useMediaQuery(theme.breakpoints.between('lg', 'xl'));
  
  // xl: 1536px+ (large desktop)
  const isLargeDesktop = useMediaQuery(theme.breakpoints.up('xl'));
  
  // Breakpoint specific checks
  const isXs = useMediaQuery(theme.breakpoints.only('xs'));
  const isSm = useMediaQuery(theme.breakpoints.only('sm'));
  const isMd = useMediaQuery(theme.breakpoints.only('md'));
  const isLg = useMediaQuery(theme.breakpoints.only('lg'));
  const isXl = useMediaQuery(theme.breakpoints.only('xl'));
  
  // Up/Down checks
  const isSmUp = useMediaQuery(theme.breakpoints.up('sm'));
  const isMdUp = useMediaQuery(theme.breakpoints.up('md'));
  const isLgUp = useMediaQuery(theme.breakpoints.up('lg'));
  
  const isSmDown = useMediaQuery(theme.breakpoints.down('sm'));
  const isMdDown = useMediaQuery(theme.breakpoints.down('md'));
  const isLgDown = useMediaQuery(theme.breakpoints.down('lg'));
  
  return {
    // Categorie principali
    isMobile,
    isTablet,
    isTabletLandscape,
    isDesktop,
    isLargeDesktop,
    
    // Breakpoint specifici
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    
    // Up/Down
    isSmUp,
    isMdUp,
    isLgUp,
    isSmDown,
    isMdDown,
    isLgDown,
    
    // Orientamento
    isPortrait: useMediaQuery('(orientation: portrait)'),
    isLandscape: useMediaQuery('(orientation: landscape)'),
    
    // Getter per il breakpoint corrente
    getCurrentBreakpoint: (): 'xs' | 'sm' | 'md' | 'lg' | 'xl' => {
      if (isXl) return 'xl';
      if (isLg) return 'lg';
      if (isMd) return 'md';
      if (isSm) return 'sm';
      return 'xs';
    },
  };
}
