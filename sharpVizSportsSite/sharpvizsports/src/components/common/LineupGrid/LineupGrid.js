// src/components/common/LineupGrid/LineupGrid.js
import React from 'react';
import './LineupGrid.css';

const LineupGrid = ({
    title,
    headers,
    players,
    renderCell,
    className = '',
    loading = false,
    error = null
}) => {
    if (loading) {
        return (
            <div className={`lineup-grid ${className}`}>
                <h4>{title}</h4>
                <div className="lineup-loading">Loading lineup...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`lineup-grid ${className}`}>
                <h4>{title}</h4>
                <div className="lineup-error">{error}</div>
            </div>
        );
    }

    if (!players || players.length === 0) {
        return (
            <div className={`lineup-grid ${className}`}>
                <h4>{title}</h4>
                <div className="lineup-empty">No lineup available</div>
            </div>
        );
    }

    return (
        <div className={`lineup-grid ${className}`}>
            <h4>{title}</h4>
            <table className="lineup-table">
                <thead>
                    <tr>
                        {headers.map((header, index) => (
                            <th key={index}>{header}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {players.map((player, index) => (
                        <tr key={index}>
                            {headers.map((header, cellIndex) => (
                                <td key={cellIndex}>
                                    {renderCell(header, player, index)}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};