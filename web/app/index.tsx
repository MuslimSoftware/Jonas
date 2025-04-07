import React from 'react';
import { StyleSheet, View, Text } from 'react-native';
import { Redirect } from 'expo-router';
import { BgView } from '@shared/components';
import { BrandSignature } from '../features/shared/BrandSignature';
// Example using shared components - adjust imports as needed
// import { BgView, TextHeader } from '@shared'; 

export default function App() {
  // Example: Redirect to a specific route or render a basic view
  // return <Redirect href="/(tabs)/home" />;

  return (
    <BgView style={styles.container}>
      <BrandSignature size={60} />
    </BgView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
}); 