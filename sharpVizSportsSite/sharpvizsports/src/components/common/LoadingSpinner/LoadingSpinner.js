// src/components/common/LoadingSpinner/LoadingSpinner.js
import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({
    size = 'medium',
    color = 'primary',
    text = 'Loading...',
    fullScreen = false
}) => {
    return (
        <div className={`spinner-container ${fullScreen ? 'fullscreen' : ''}`}>
            <div className={`spinner ${size} ${color}`} role="status">
                <div className="spinner-circle"></div>
            </div>
            {text && <div className="spinner-text">{text}</div>}
        </div>
    );
};

export default LoadingSpinner;

// Optional: Create an index.js for cleaner imports
// src/components/common/LoadingSpinner/index.js
//export { default } from './LoadingSpinner';