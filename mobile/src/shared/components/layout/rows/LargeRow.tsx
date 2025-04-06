import React from 'react';
import { BaseRow, BaseRowProps } from './BaseRow';
import { gaps } from '@uniskit/shared';

export interface LargeRowProps extends BaseRowProps {}

/**
 * A row component applying a large gap by default.
 */
export function LargeRow({ style, ...props }: LargeRowProps) {
  return (
    <BaseRow 
      gap={gaps.large} // Apply default large gap
      style={style} 
      {...props} 
    />
  );
} 