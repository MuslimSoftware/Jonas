import React from 'react';
import { Link } from 'react-router-dom'; // Use Link for internal navigation
import styles from './Brand.module.css';
import { BRAND_NAME } from '@uniskit/shared';
import { IoHeartCircle } from 'react-icons/io5';
import { useTheme } from '@/context/ThemeContext';
interface BrandProps {
  /** Optional additional class names */
  className?: string;
  /** Optional font size override for the link */
  fontSize?: string;
}

const Brand: React.FC<BrandProps> = ({ 
  className = '',
  fontSize
}) => {
  const linkStyle = fontSize ? { fontSize } : {};
  const { theme } = useTheme();

  return (
    <Link 
      to="/" 
      className={`${styles.brandLink} ${className}`}
      style={linkStyle}
      aria-label={`${BRAND_NAME} Home`}
    >
      <IoHeartCircle
        size={40}
        color={theme.colors.brand.primary}
      />
      <span>{BRAND_NAME.toUpperCase()}</span>
    </Link>
  );
};

export default Brand; 