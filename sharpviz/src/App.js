// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; // Updated import
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Footer from './components/Footer';
import UserDetails from './pages/UserDetails';
import NRFIModel from './pages/NRFIModel'; // Import the NRFIModel component

function App() {
  return (
    <Router>
      <Navbar />
      <Routes> {/* Replaced Switch with Routes */}
        <Route path="/" element={<Home />} /> {/* Updated Route syntax */}
        <Route path="/user-details" element={<UserDetails />} />
        <Route path="/nrfi-model" element={<NRFIModel />} />
      </Routes>
      <Footer />
    </Router>
  );
}

export default App;
