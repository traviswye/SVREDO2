import React from 'react';
import Sidebar from '../../../../components/common/Sidebar/SideBar';
import TeamTemperatures from '../TeamTemperatureTracking/TeamTemperatures';
import PitcherMetrics from './components/PitcherMetrics';
import HitterTracking from './components/HitterTracking';
import TeamProfitability from './components/TeamProfitability';
import './DailyDataMLB.css';

const DailyDataMLB = () => {
    return (
        <div className="daily-data-mlb">
            <Sidebar />
            <div className="content">
                <h1>Daily MLB Data</h1>
                <div className="grid-container">
                    <TeamTemperatures />
                    <TeamProfitability />
                    <PitcherMetrics date={new Date().toISOString()} />
                    <HitterTracking date={new Date().toISOString()} />
                </div>
            </div>
        </div>
    );
}