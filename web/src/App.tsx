import React from 'react';

import Header from '@/components/layout/Header';
import HeroSection from '@/components/sections/HeroSection';
import FeaturesSection from '@/components/sections/FeaturesSection';
import Footer from '@/components/layout/Footer';

function App() {
  return (
    <>
      <Header /> 
      <main>
        <HeroSection />
        <FeaturesSection />
      </main>
      <Footer />
    </>
  );
}

export default App; 