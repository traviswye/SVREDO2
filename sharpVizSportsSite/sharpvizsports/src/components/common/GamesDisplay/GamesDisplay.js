// src/components/common/GamesDisplay/GamesDisplay.js
import React from 'react';
import './GamesDisplay.css';

const GamesDisplay = ({
    children,
    datePicker,
    className = '',
    gridColumns = 5,
}) => {
    return (
        <div className={`games-display ${className}`}>
            {datePicker && (
                <div className="date-picker-container">
                    {datePicker}
                </div>
            )}
            <div
                className="games-grid"
                style={{
                    '--grid-columns': gridColumns
                }}
            >
                {children}
            </div>
        </div>
    );
};

export default GamesDisplay;