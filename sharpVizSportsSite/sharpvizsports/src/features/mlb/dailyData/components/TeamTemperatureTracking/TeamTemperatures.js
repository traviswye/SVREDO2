// src/features/mlb/dailyData/components/TeamTemperatureTracking/TeamTemperatures.js
import React from 'react';
import { useTeamTemperatures } from '../../hooks/useTeamTemperatures';
import DataBox from '../../../../../components/common/DataBox/DataBox';

const TeamTemperatures = ({ title, subtitle, date }) => {
    const headers = [
        "Team",
        "Current Temperature",
        "Wins",
        "Loses",
        "Winning %",
        "RS",
        "RA",
        "Pythagran %",
        "Streak",
        "Last Result",
        "Previous Temp",
        "Date",
        "Game Number",
    ];

    const keyHeaders = [
        "team",
        "currentTemp",
        "wins",
        "loses",
        "winPerc",
        "rs",
        "ra",
        "pythagPerc",
        "streak",
        "lastResult",
        "previousTemp",
        "date",
        "gameNumber",
    ];

    const { data, loading, error } = useTeamTemperatures(date);

    const formatValue = (key, value) => {
        if (key === 'winPerc' || key === 'pythagPerc') {
            return value?.toFixed(3);
        }
        if (key === 'date') {
            return value?.split('T')[0];
        }
        return value;
    };

    return (
        <DataBox
            title={title}
            subtitle={subtitle}
            headers={headers}
            keyHeaders={keyHeaders}
            data={data || []} // Ensure we always pass an array
            loading={loading}
            error={error}
            formatValue={formatValue}
            defaultSort={{ key: "currentTemp", direction: "desc" }}
        />
    );
};

export default TeamTemperatures;