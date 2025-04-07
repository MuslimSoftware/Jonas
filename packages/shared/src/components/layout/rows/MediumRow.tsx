import React from 'react';
import { View } from 'react-native'; 
import { BaseRow, BaseLayoutComponentProps } from './BaseRow';
import { gaps } from '../../../theme';

export interface MediumRowProps extends Omit<BaseLayoutComponentProps, 'gap'> {}

export const MediumRow = React.forwardRef<View, MediumRowProps>((
  { style, ...props }, 
  ref
) => {
  return (
    <BaseRow 
      ref={ref} 
      gap={gaps.medium}
      style={style} 
      {...props} 
    />
  );
});

MediumRow.displayName = 'MediumRow'; 