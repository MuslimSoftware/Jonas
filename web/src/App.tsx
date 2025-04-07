import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Switch } from '@shared/components/forms';

function App() {
  const [switchValue, setSwitchValue] = useState(false);
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to React Native Web!</Text>
      <Text style={styles.text}>Edit <code>src/App.tsx</code> and save to reload.</Text>
      <View style={styles.switchContainer}>
        <Text style={styles.text}>Shared Switch: </Text>
        <Switch value={switchValue} onValueChange={() => {
          console.log('Switch value changed');
          setSwitchValue(!switchValue);
        }} />
      </View>
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
  switchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 20,
  },
});

export default App;
