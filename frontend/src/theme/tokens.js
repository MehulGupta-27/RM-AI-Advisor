/**
 * Design Tokens - Extracted from spec §6.1
 * Single source of truth for all colors, spacing, typography
 */

export const colors = {
  // Backgrounds
  appBackground: '#0d0e11',
  panelBackground: '#14161b',
  cardBackground: '#1c1f26',
  
  // Borders
  border: 'rgba(255, 255, 255, 0.07)',
  borderHover: 'rgba(255, 255, 255, 0.12)',
  
  // Accents
  primaryAccent: '#7b9cff',      // Periwinkle blue
  primaryAccentHover: '#8faeff',
  secondaryAccent: '#a78bfa',    // Violet
  
  // Status
  success: '#4ade80',
  warning: '#fbbf24',
  danger: '#f87171',
  info: '#3b82f6',
  
  // Text
  textPrimary: '#f0f1f4',
  textSecondary: '#8a8f9e',
  textMuted: '#545966',
  
  // Avatar gradients
  avatarGradientStart: '#7b9cff',
  avatarGradientEnd: '#a78bfa',
  
  // Risk colors
  riskLow: '#4ade80',
  riskMedium: '#fbbf24',
  riskHigh: '#f87171',
  riskVeryHigh: '#dc2626',
};

export const typography = {
  fontFamily: '"DM Sans", sans-serif',
  fontSize: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

export const spacing = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
  '3xl': '4rem',   // 64px
};

export const borderRadius = {
  sm: '0.25rem',   // 4px
  md: '0.5rem',    // 8px
  lg: '0.75rem',   // 12px
  xl: '1rem',      // 16px
  '2xl': '1.25rem', // 20px
  full: '9999px',
};

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  glow: '0 0 20px rgba(123, 156, 255, 0.3)',
};

export const transitions = {
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  base: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '500ms cubic-bezier(0.4, 0, 0.2, 1)',
};

export const layout = {
  headerHeight: '58px',
  sidebarWidth: '260px',
  maxWidth: '1440px',
};

// Helper function to get risk color
export function getRiskColor(riskLevel) {
  if (!riskLevel) return colors.textMuted;
  
  const level = riskLevel.toLowerCase();
  if (level === 'low') return colors.riskLow;
  if (level === 'medium' || level === 'moderate') return colors.riskMedium;
  if (level === 'high') return colors.riskHigh;
  if (level === 'very_high' || level === 'very high') return colors.riskVeryHigh;
  
  return colors.textMuted;
}

// Helper function to format currency
export function formatCurrency(value) {
  if (!value && value !== 0) return '₹0';
  return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

// Helper function to format percentage
export function formatPercentage(value) {
  if (!value && value !== 0) return '0%';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export default {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  transitions,
  layout,
  getRiskColor,
  formatCurrency,
  formatPercentage,
};
