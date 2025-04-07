import React from 'react';
import styles from './BaseInput.module.css'; // We'll create this CSS module next

interface BaseInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'style' | 'className'> {
  inputClassName?: string;
  containerClassName?: string;
  error?: boolean;
  // We might not need label directly here if AuthInput handles it
}

export const BaseInput: React.FC<BaseInputProps> = ({
  inputClassName,
  containerClassName,
  error,
  ...props
}) => {
  // Basic error styling for now
  const errorStyle = error ? styles.inputError : '';

  return (
    <div className={`${styles.container} ${containerClassName || ''}`}>
      <input
        className={`${styles.input} ${errorStyle} ${inputClassName || ''}`}
        {...props}
      />
    </div>
  );
}; 