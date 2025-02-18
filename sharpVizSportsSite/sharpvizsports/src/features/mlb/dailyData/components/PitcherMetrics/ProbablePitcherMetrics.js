// src/features/mlb/components/PitcherMetrics/ProbablePitcherMetrics.js
import React from 'react';
import DataBox from '../../../../components/common/DataBox/DataBox';
import { usePitcherMetrics } from '../../hooks/usePitcherMetrics';
import PitcherStatusIcon from './PitcherStatusIcon';
import './ProbablePitcherMetrics.css';

const ProbablePitcherMetrics = ({ title, subtitle, date }) => {
    const { data, loading, error } = usePitcherMetrics(date);

    const headers = [
        "Date",
        "Time",
        "Home Team",
        "Away Team",
        "Venue",
        "Home Pitcher",
        "Status",
        "Trend",
        "Away Pitcher",
        "Status",
        "Trend"
    ];

    const keyHeaders = [
        "date",
        "time",
        "homeTeam",
        "awayTeam",
        "venue",
        "homePitcher",
        "homePitcherStatus",
        "homePercentage",
        "awayPitcher",
        "awayPitcherStatus",
        "awayPercentage"
    ];

    const formatValue = (key, value, row) => {
        switch (key) {
            case "date":
                return (
                    <a
                        href={row.previewLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="preview-link"
                    >
                        {value}
                    </a>
                );
            case "homePercentage":
                return <PitcherStatusIcon message={row.homePitcherMessage} />;
            case "awayPercentage":
                return <PitcherStatusIcon message={row.awayPitcherMessage} />;
            case "homePitcherStatus":
            case "awayPitcherStatus":
                return (
                    <span className={`status-text status-${value.toLowerCase()}`}>
                        {value}
                    </span>
                );
            default:
                return value;
        }
    };

    return (
        <DataBox
            title={title}
            subtitle={subtitle}
            headers={headers}
            keyHeaders={keyHeaders}
            data={data}
            loading={loading}
            error={error}
            formatValue={formatValue}
            defaultSort={{ key: "time", direction: "asc" }}
            className="pitcher-metrics"
        />
    );
};

export default ProbablePitcherMetrics;