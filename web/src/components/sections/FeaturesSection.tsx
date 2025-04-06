import React from 'react';
import styles from './FeaturesSection.module.css';
import { BRAND_NAME } from '@uniskit/shared';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism'; 

// Code snippets for features
const backendCode = `from fastapi import FastAPI
app = FastAPI()

@app.get("/api/hello")
async def read_root():
    return {"message": "Hello from Backend!"}
`;

const webCode = `import styles from './Button.module.css';

function Button({ label }) {
  return <button className={styles.button}>{label}</button>;
}

/* Button.module.css */
.button {
  background-color: var(--color-primary);
  color: white;
  padding: 10px 20px;
  border-radius: var(--border-radius-medium);
}
`;

const mobileCode = `import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '@react-navigation/native'; // Assuming theme context

function ThemedCard({ title }) {
  const { colors } = useTheme(); // Access shared theme
  return (
    <View style={[styles.card, { backgroundColor: colors.card }]}>
      <Text style={{ color: colors.text }}>{title}</Text>
    </View>
  );
}

const styles = StyleSheet.create({ 
  card: { padding: 15, borderRadius: 8 } 
});
`;

const features = [
  { 
    element: (
      <SyntaxHighlighter language="python" style={atomDark} customStyle={{ margin: 0, fontSize: '0.8rem', borderRadius: 'var(--border-radius-small)' }}>
        {backendCode}
      </SyntaxHighlighter>
    ), 
    title: 'FastAPI Backend Foundation', 
    description: 'Solid Python backend structure ready for your API logic. Skip the boilerplate.' 
  },
  { 
    element: (
       <SyntaxHighlighter language="jsx" style={atomDark} customStyle={{ margin: 0, fontSize: '0.8rem', borderRadius: 'var(--border-radius-small)' }}>
         {webCode}
       </SyntaxHighlighter>
    ), 
    title: 'React Web Frontend', 
    description: 'Vite-powered React setup with CSS Modules and pre-configured shared theme variables.' 
  },
    { 
    element: (
       <SyntaxHighlighter language="jsx" style={atomDark} customStyle={{ margin: 0, fontSize: '0.8rem', borderRadius: 'var(--border-radius-small)' }}>
         {mobileCode}
       </SyntaxHighlighter>
    ), 
    title: 'React Native Mobile App', 
    description: 'Cross-platform Expo foundation using React Native, structured for scalability and themed.' 
  },
];

const FeaturesSection = () => {
  return (
    <section className={styles.featuresSection}>
      <div className={styles.container}>
        {/* Updated Title and Subtitle */}
        <h2 className={styles.title}>Skip the Setup, Start Building Faster</h2>
        <p className={styles.subtitle}>
          {BRAND_NAME} provides pre-configured foundations for backend, web, and mobile, so you can focus on your features.
        </p>
        <div className={styles.grid}>
          {/* Map through the refactored features */}
          {features.map((feature) => (
            <div key={feature.title} className={styles.featureCard}>
              {/* Use a consistent div for the visual element */}
              <div className={styles.featureElementWrapper}> 
                {feature.element} 
              </div>
              <h3 className={styles.featureTitle}>{feature.title}</h3>
              <p className={styles.featureDescription}>{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection; 