import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import NavBar from './components/common/NavBar/NavBar';
import LoadingSpinner from './components/common/LoadingSpinner/LoadingSpinner';

// Lazy load pages
const Home = lazy(() => import('./features/home/Home'));
const MLBRoutes = lazy(() => import('./features/mlb/MLBRoutes'));
const NFLRoutes = lazy(() => import('./features/nfl/NFLRoutes'));
const Account = lazy(() => import('./features/account/Account'));
const Login = lazy(() => import('./features/auth/Login'));

const App = () => {
  return (
    <Router>
      <NavBar />
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/mlb/*" element={<MLBRoutes />} />
          <Route path="/nfl/*" element={<NFLRoutes />} />
          <Route path="/account/*" element={<Account />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </Suspense>
    </Router>

  );
};

export default App;
