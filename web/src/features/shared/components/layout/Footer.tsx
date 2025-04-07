import React from 'react';
import styles from './Footer.module.css';
import { Brand as BrandConstant} from '@jonas/shared/src/constants/Brand';
import { FaGithub, FaTwitter, FaLinkedin } from 'react-icons/fa'; // Example icons
import { Brand } from '@/features/shared/components/brand/Brand';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        {/* Top Section: Logo/Brand and Social Links */}
        <div className={styles.topSection}>
          <div className={styles.brandInfo}>
            <Brand />
            <p className={styles.brandSlogan}>Build faster, together.</p>
          </div>
          <div className={styles.socialLinks}>
            <a href="#" aria-label="GitHub" className={styles.socialIconLink}><FaGithub /></a>
            <a href="#" aria-label="Twitter" className={styles.socialIconLink}><FaTwitter /></a>
            <a href="#" aria-label="LinkedIn" className={styles.socialIconLink}><FaLinkedin /></a>
          </div>
        </div>

        {/* Middle Section: Link Columns */}
        <div className={styles.linksGrid}>
          <div className={styles.linkColumn}>
            <h4 className={styles.linkColumnTitle}>Product</h4>
            <a href="#" className={styles.link}>Features</a>
            <a href="#" className={styles.link}>Pricing</a>
            <a href="#" className={styles.link}>Docs</a>
            <a href="#" className={styles.link}>Updates</a>
          </div>
          <div className={styles.linkColumn}>
            <h4 className={styles.linkColumnTitle}>Company</h4>
            <a href="#" className={styles.link}>About Us</a>
            <a href="#" className={styles.link}>Careers</a>
            <a href="#" className={styles.link}>Blog</a>
            <a href="#" className={styles.link}>Contact</a>
          </div>
          <div className={styles.linkColumn}>
            <h4 className={styles.linkColumnTitle}>Resources</h4>
            <a href="#" className={styles.link}>Support</a>
            <a href="#" className={styles.link}>Privacy Policy</a>
            <a href="#" className={styles.link}>Terms of Service</a>
          </div>
          {/* Add more columns as needed */}
        </div>

        {/* Bottom Section: Copyright */}
        <div className={styles.bottomSection}>
          <p className={styles.copyright}>
            &copy; {currentYear} {BrandConstant.name}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 