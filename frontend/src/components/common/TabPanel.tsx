/**
 * TabPanel Component
 * Componente riutilizzabile per gestire il contenuto delle tab
 */
import React from 'react';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

export function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
      style={{ display: value === index ? 'block' : 'none' }}
    >
      {value === index && children}
    </div>
  );
}

export function a11yProps(index: number) {
  return {
    id: `tab-${index}`,
    'aria-controls': `tabpanel-${index}`,
  };
}
