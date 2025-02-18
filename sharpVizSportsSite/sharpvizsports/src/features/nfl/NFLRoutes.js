// src/features/nfl/NFLRoutes.js
import React from 'react';
import { Routes, Route } from 'react-router-dom';

const NFLRoutes = () => {
    return (
        <Routes>
            <Route path="/" element={<div>NFL Coming Soon</div>} />
        </Routes>
    );
};

export default NFLRoutes;