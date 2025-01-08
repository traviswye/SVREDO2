// src/components/Navbar.js
import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
    return (
        <nav style={{ backgroundColor: '#282c34', padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Link to="/" style={{ color: 'white', textDecoration: 'none', margin: '0 1rem' }}>Home</Link>
            <Link to="/user-details" style={{ color: 'white', textDecoration: 'none', margin: '0 1rem' }}>User Details</Link>
            <Link to="/nrfi-model" style={{ color: 'white', textDecoration: 'none', margin: '0 1rem' }}>NRFI Model</Link>
          </div>
          <div>
            <button style={{ backgroundColor: 'transparent', border: '1px solid white', color: 'white', padding: '0.5rem 1rem', cursor: 'pointer' }}>
              Login
            </button>
          </div>
        </nav>
      );
}

export default Navbar;
