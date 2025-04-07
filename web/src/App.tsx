import React from 'react';
import styles from './App.module.css';

import { Brand } from '@/features/shared/components/brand/Brand';
import { AuthInput } from '@/features/auth/components/AuthInput';


function App() {
  return (
    <main className={styles.appContainer}>
      <Brand size={60} />
      <div className={styles.inputContainer}>
        <AuthInput
          id="auth-key"
          type="password"
          label="Enter access key"
        />
      </div>
    </main>
  );
}

export default App; 