import React from 'react';
import { View } from 'react-native';
import { BaseColumn, BaseColumnProps } from './BaseColumn';
import { gaps } from '../../../theme/spacing';

export interface LargeColumnProps extends Omit<BaseColumnProps, 'gap'> {}

export const LargeColumn = React.forwardRef<View, LargeColumnProps>((
  { style, ...props },
  ref
) => {
  return (
    <BaseColumn
      ref={ref}
      gap={gaps.large}
      style={style}
      {...props}
    />
  );
});

LargeColumn.displayName = 'LargeColumn';