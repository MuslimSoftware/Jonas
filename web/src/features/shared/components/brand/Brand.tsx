import React from 'react';
import { Link } from 'react-router-dom'; // Use Link for internal navigation
import styles from './Brand.module.css';
import { IoHeartCircle } from 'react-icons/io5';
import { useTheme } from '@/context/ThemeContext';
import { Brand as BrandConstant} from '@jonas/shared/src/constants/Brand';
import { FaBreadSlice } from "react-icons/fa";

interface BrandProps {
  size?: number;
}

export const Brand: React.FC<BrandProps> = ({ 
  size = 40,
}) => {
  const { theme } = useTheme();
  const fontSize = size * 0.8;
  const iconSize = size * 0.8;

  return (
    <Link 
      to="/" 
      className={`${styles.brandLink}`}
      aria-label={`${BrandConstant.name} Home`}
    >
      <FaBreadSlice
        size={iconSize}
        color={theme.colors.brand.primary}
        className={styles.icon}
      />
      <span style={{ fontSize }}>{BrandConstant.name}</span>
    </Link>
  );
};