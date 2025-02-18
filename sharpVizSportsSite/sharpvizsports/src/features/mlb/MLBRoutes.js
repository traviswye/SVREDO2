// src/features/mlb/MLBRoutes.js
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import DailyDataMLB from './dailyData/DailyDataMLB';
import DFSOptimizerMLB from './dfsOptimizer/DFSOptimizerMLB';
import BettingModelsMLB from './bettingModels/BettingModelsMLB';
import TodaysGames from './todaysGames/TodaysGames';

const MLBRoutes = () => {
    return (
        <Routes>
            <Route path="/" element={<TodaysGames />} />
            <Route path="daily-data/*" element={<DailyDataMLB />} />
            <Route path="dfs-optimizer" element={<DFSOptimizerMLB />} />
            <Route path="betting-models" element={<BettingModelsMLB />} />
            <Route path="todays-games" element={<TodaysGames />} />
        </Routes>
    );
};

export default MLBRoutes;