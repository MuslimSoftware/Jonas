import React, { useCallback, useState } from 'react';
import styles from './Header.module.css';
import { useTheme } from '@/context/ThemeContext';
import { BrandLogo } from '@/features/shared/components/brand/BrandLogo'; 

const navLinks = [
  { label: "Company", href: "#company" },
  { label: "Features", href: "#features" },
  { label: "Support", href: "#support" }
];

const Header = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { setThemePreference, isDark } = useTheme(); 

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleThemeCycle = useCallback(() => {
    const nextPreference = isDark ? 'light' : 'dark';
    setThemePreference(nextPreference);
  }, [isDark, setThemePreference]);

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <BrandLogo /> 

        {/* Hamburger Button - Controls nav visibility on mobile */}
        <button 
          className={`${styles.hamburgerButton} ${isMobileMenuOpen ? styles.isOpen : ''}`}
          onClick={toggleMobileMenu}
          aria-label="Toggle menu"
          aria-expanded={isMobileMenuOpen}
          aria-controls="header-nav"
        >
          <span></span> 
          <span></span>
          <span></span>
        </button>

        {/* Navigation container - includes links and social icons */}
        <nav id="header-nav" className={`${styles.nav} ${isMobileMenuOpen ? styles.navMobileOpen : ''}`}>
          {/* Centered Navigation Links */}
          <div className={styles.navLinks}>
            {navLinks.map(link => (
              <a key={link.label} href={link.href}>{link.label}</a>
            ))}
          </div>
          
          {/* Social Icons & Theme Toggle (Right Aligned on Desktop) */}
          <div className={styles.socialIcons}>
            {/* Theme Toggle Switch */} 
            <label 
              className={styles.themeSwitch} 
              title={`Switch to ${isDark ? 'light' : 'dark'} theme`}
              aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
            >
              <input 
                type="checkbox" 
                checked={isDark} 
                onChange={handleThemeCycle} 
              />
              <span className={styles.slider}></span>
            </label>
          </div>
        </nav>

      </div>
    </header>
  );
};

export default Header; 