import React from 'react'
import { BaseColumn } from './BaseColumn'
import { gaps } from '@uniskit/shared'
import { ViewProps } from 'react-native'

export const LargeColumn: React.FC<ViewProps> = ({
  children,
  ...props
}) => {

  return (
    <BaseColumn gap={gaps.large} {...props}>
      {children}
    </BaseColumn>
  )
}
