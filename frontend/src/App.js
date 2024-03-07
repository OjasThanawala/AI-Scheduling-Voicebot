import React from 'react';
import { BrowserRouter as Router, Route, Link, Routes } from 'react-router-dom';
import UserPage from './UserPage';
import AdminPage from './AdminPage';
import HomePage from './HomePage';
import './App.css';

function App() {
  return (
    <Router>
      <div>
        <header>
          <Link to="/" className="header-link"><h1>Dr. Walnut's Clinic</h1></Link>
        </header>
        <div className="content">
          <Routes>
            <Route path="/" element={<HomePage />} exact />
            <Route path="/user" element={<UserPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
