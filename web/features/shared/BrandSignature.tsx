import React from 'react';
import { StyleSheet } from 'react-native';
import { useTheme, Brand } from '@shared'; 
import { Link } from 'expo-router';
import { FaBreadSlice } from "react-icons/fa";
import { Text } from 'react-native';

interface BrandSignatureProps {
  size?: number;
}

export const BrandSignature: React.FC<BrandSignatureProps> = ({ 
  size = 40,
}) => {
  const { theme } = useTheme();
  const fontSize = size * 0.8;
  const iconSize = size * 0.8;

  return (
    <Link 
      href="/"
      aria-label={`${Brand.name} Home`}
    >
      <FaBreadSlice
        size={iconSize}
        color={theme.colors.brand.primary}
        style={styles.icon}
      />
      <Text style={{ fontSize }}>{Brand.name}</Text>
    </Link>
  );
};

const styles = StyleSheet.create({
  brandLink: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  icon: {
  },
});