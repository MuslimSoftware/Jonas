import React from 'react';
import { Link } from 'react-router-dom'; // Use Link for internal navigation
import styles from './Brand.module.css';
// Import directly from @shared package root
import { useTheme, Brand } from '@shared'; 
import { FaBreadSlice } from "react-icons/fa";

interface BrandProps {
  size?: number;
}

export const BrandLogo: React.FC<BrandProps> = ({ 
  size = 40,
}) => {
  const { theme } = useTheme();
  const fontSize = size * 0.8;
  const iconSize = size * 0.8;

  return (
    <Link 
      to="/" 
      className={`${styles.brandLink}`}
      aria-label={`${Brand.name} Home`}
    >
      <FaBreadSlice
        size={iconSize}
        color={theme.colors.brand.primary}
        className={styles.icon}
      />
      <span style={{ fontSize }}>{Brand.name}</span>
    </Link>
  );
};