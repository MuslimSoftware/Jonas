import React from 'react';
import { View } from 'react-native';
import { BaseRow, BaseLayoutComponentProps } from './BaseRow';
import { gaps } from '../../../theme';

export interface SmallRowProps extends Omit<BaseLayoutComponentProps, 'gap'> {}

export const SmallRow = React.forwardRef<View, SmallRowProps>((
  { style, ...props }, 
  ref
) => {
  return (
    <BaseRow 
      ref={ref} 
      gap={gaps.small}
      style={style} 
      {...props} 
    />
  );
});

SmallRow.displayName = 'SmallRow'; 