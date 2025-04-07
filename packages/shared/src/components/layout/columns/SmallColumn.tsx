import React from 'react';
import { View } from 'react-native';
import { BaseColumn, BaseColumnProps } from './BaseColumn';
import { gaps } from '../../../theme';

export interface SmallColumnProps extends Omit<BaseColumnProps, 'gap'> {}

export const SmallColumn = React.forwardRef<View, SmallColumnProps>((
  { style, ...props },
  ref
) => {
  return (
    <BaseColumn
      ref={ref}
      gap={gaps.small}
      style={style}
      {...props}
    />
  );
});

SmallColumn.displayName = 'SmallColumn'; 