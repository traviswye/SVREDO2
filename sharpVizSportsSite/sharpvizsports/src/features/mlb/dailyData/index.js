// src/features/mlb/dailyData/index.js
import React from 'react';
import Sidebar from '../../../components/common/Sidebar';
import DataBox from '../../../components/common/DataBox';
import PitcherMetrics from './components/PitcherMetrics';
import HitterTempTracking from './components/HitterTempTracking';
import TeamTemperatures from './components/TeamTemperatureTracking';
import './DailyDataMLB.css';

const DailyDataMLB = () => {
    return (
        <div className="daily-data-mlb">
            <Sidebar />
            <div className="content">
                <h1>Daily MLB Data</h1>
                <div className="grid-container">
                    <TeamTemperatures />
                    <PitcherMetrics />
                    <HitterTempTracking />
                </div>
            </div>
        </div>
    );
};

export default DailyDataMLB;