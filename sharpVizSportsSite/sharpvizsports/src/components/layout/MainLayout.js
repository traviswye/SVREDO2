import React from 'react';
import Sidebar from '../common/Sidebar/SideBar';
import './MainLayout.css';

const MainLayout = ({ children }) => {
    return (
        <div className="main-layout">
            <Sidebar />
            <main className="main-content">
                {children}
            </main>
        </div>
    );
};

export default MainLayout;