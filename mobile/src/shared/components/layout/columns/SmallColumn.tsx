import React from 'react'
import { ViewProps } from 'react-native'
import { BaseColumn } from './BaseColumn'
import { gaps } from '@uniskit/shared'

// Rename component to SmallColumn
export const SmallColumn: React.FC<ViewProps> = ({
  children,
  style,
  ...props
}) => {
  return (
    <BaseColumn gap={gaps.small} style={style} {...props}>
      {children}
    </BaseColumn>
  )
} 