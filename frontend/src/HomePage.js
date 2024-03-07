// HomePage.js
import React from 'react';
import { Link } from 'react-router-dom';

function HomePage() {
  return (
    <div className="home">
      <h1>Welcome to Dr. Walnut's Clinic</h1>
      <div className="navigation-buttons">
        <Link to="/user"><button>Patient</button></Link>
        <Link to="/admin"><button>Doctor</button></Link>
      </div>
    </div>
  );
}

export default HomePage;