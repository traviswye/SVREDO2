import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import NavBar from "./components/NavBar";
import Home from "./pages/Home";
import DailyDataMLB from "./pages/MLB/DailyDataMLB";
import DFSOptimizerMLB from "./pages/MLB/DFSOptimizerMLB";
import BettingModelsMLB from "./pages/MLB/BettingModelsMLB";
import DailyDataNFL from "./pages/NFL/DailyDataNFL";
import DFSOptimizerNFL from "./pages/NFL/DFSOptimizerNFL";
import BettingModelsNFL from "./pages/NFL/BettingModelsNFL";
import PartnerSharpsHome from "./pages/PartnerPages/PartnerSharpsHome";
import AccountHome from "./pages/Account/AccountHome";
import Login from "./pages/Login";

const App = () => {
  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/mlb/daily-data" element={<DailyDataMLB />} />
        <Route path="/mlb/dfs-optimizer" element={<DFSOptimizerMLB />} />
        <Route path="/mlb/betting-models" element={<BettingModelsMLB />} />
        <Route path="/nfl/daily-data" element={<DailyDataNFL />} />
        <Route path="/nfl/dfs-optimizer" element={<DFSOptimizerNFL />} />
        <Route path="/nfl/betting-models" element={<BettingModelsNFL />} />
        <Route path="/partner-sharps-home" element={<PartnerSharpsHome />} />
        <Route path="/account" element={<AccountHome />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </Router>
  );
};

export default App;
