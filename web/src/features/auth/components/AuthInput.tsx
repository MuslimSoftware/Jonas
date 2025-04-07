import React from 'react';
import { BaseInput } from '@/features/shared/components/inputs/BaseInput';
import styles from './AuthInput.module.css'; // Create this CSS module next

interface AuthInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'style' | 'className'> {
  label?: string;
  inputClassName?: string;
  containerClassName?: string;
  error?: boolean;
  errorMessage?: string;
}

export const AuthInput: React.FC<AuthInputProps> = ({
  label,
  inputClassName,
  containerClassName,
  error,
  errorMessage,
  ...props
}) => {
  return (
    <div className={`${styles.outerContainer} ${containerClassName || ''}`}>
      <BaseInput
        inputClassName={inputClassName}
        error={error}
        placeholder={label} // Use label as placeholder for web
        aria-label={label} // Good practice for accessibility
        aria-invalid={error} // Accessibility for error state
        aria-describedby={errorMessage ? `${props.id}-error` : undefined} // Link error message
        {...props}
      />
      {error && errorMessage && (
        <p id={`${props.id}-error`} className={styles.errorText}>
          {errorMessage}
        </p>
      )}
    </div>
  );
}; 