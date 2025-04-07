import React from 'react';
import { View } from 'react-native'; 
import { BaseRow, BaseLayoutComponentProps } from './BaseRow';
import { gaps } from '../../../theme';

export interface LargeRowProps extends Omit<BaseLayoutComponentProps, 'gap'> {}

export const LargeRow = React.forwardRef<View, LargeRowProps>((
  { style, ...props }, 
  ref
) => {
  return (
    <BaseRow 
      ref={ref} 
      gap={gaps.large}
      style={style} 
      {...props} 
    />
  );
});

LargeRow.displayName = 'LargeRow'; 