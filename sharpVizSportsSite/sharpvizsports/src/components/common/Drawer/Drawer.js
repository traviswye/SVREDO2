// src/components/common/Drawer/Drawer.js
import React, { useEffect } from 'react';
import './Drawer.css';

const Drawer = ({
    isOpen,
    onClose,
    title,
    children,
    position = 'right',
    width = '400px'
}) => {
    useEffect(() => {
        const handleEsc = (event) => {
            if (event.keyCode === 27) onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    if (!isOpen) return null;

    return (
        <div className="drawer-overlay" onClick={onClose}>
            <div
                className={`drawer drawer-${position}`}
                style={{ width }}
                onClick={e => e.stopPropagation()}
            >
                <button className="drawer-close-button" onClick={onClose}>
                    ×
                </button>
                {title && <h2 className="drawer-title">{title}</h2>}
                <div className="drawer-content">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Drawer;