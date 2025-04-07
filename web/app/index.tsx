import React from 'react';
import { Redirect } from 'expo-router';

export default function RootIndex() {
  console.log('RootIndex');
  return <Redirect href="/auth" />;
}