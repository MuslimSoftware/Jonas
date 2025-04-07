import React from 'react';
import { View } from 'react-native';
import { BaseColumn, BaseColumnProps } from './BaseColumn';
import { gaps } from '../../../theme';

export interface MediumColumnProps extends Omit<BaseColumnProps, 'gap'> {}

export const MediumColumn = React.forwardRef<View, MediumColumnProps>((
  { style, ...props },
  ref
) => {
  return (
    <BaseColumn
      ref={ref}
      gap={gaps.medium}
      style={style}
      {...props}
    />
  );
});

MediumColumn.displayName = 'MediumColumn'; 