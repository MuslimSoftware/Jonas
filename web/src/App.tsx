import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

// Remove logo import and CSS import
// import logo from './logo.svg';
// import './App.css';

function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to React Native Web!</Text>
      <Text style={styles.text}>Edit <code>src/App.tsx</code> and save to reload.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  text: {
    fontSize: 16,
  },
});

export default App;
