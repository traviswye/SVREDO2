import React, { useState, useEffect } from "react";
import "../css/BullpenTeamStats.css";
import axios from "axios";

const BullpenStats = ({ team, year }) => {
    const [bullpenData, setBullpenData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchBullpenData = async () => {
            if (!team) return;

            setLoading(true);
            try {
                // Use the new Pitchers/bullpens endpoint
                const response = await axios.get(`https://localhost:44346/api/Pitchers/bullpens`, {
                    params: {
                        team: team,
                        year: '2024'
                        // year: year || new Date().getFullYear()
                    }
                });

                setBullpenData(response.data);
            } catch (err) {
                console.error(`Error fetching bullpen data for ${team}:`, err);
                setError(`Unable to load bullpen data for ${team}`);
            } finally {
                setLoading(false);
            }
        };

        fetchBullpenData();
    }, [team, year]);

    if (loading) {
        return <div className="bullpen-loading">Loading bullpen data...</div>;
    }

    if (error) {
        return <div className="bullpen-error">{error}</div>;
    }

    if (!bullpenData) {
        return <div className="bullpen-no-data">No bullpen data available for {team}.</div>;
    }

    return (
        <div className="bullpen-container">
            <h4 className="bullpen-team-name">{team} Bullpen</h4>

            <div className="bullpen-metrics">
                <div className="bullpen-metric">
                    <span className="metric-label">ERA:</span>
                    <span className="metric-value">{bullpenData.era?.toFixed(2) || "N/A"}</span>
                </div>
                <div className="bullpen-metric">
                    <span className="metric-label">WHIP:</span>
                    <span className="metric-value">{bullpenData.whip?.toFixed(2) || "N/A"}</span>
                </div>
                <div className="bullpen-metric">
                    <span className="metric-label">IP:</span>
                    <span className="metric-value">{bullpenData.totalIP?.toFixed(1) || "N/A"}</span>
                </div>
                <div className="bullpen-metric">
                    <span className="metric-label">K/9:</span>
                    <span className="metric-value">{bullpenData.k9?.toFixed(2) || "N/A"}</span>
                </div>
                <div className="bullpen-metric">
                    <span className="metric-label">BB/9:</span>
                    <span className="metric-value">{bullpenData.bB9?.toFixed(2) || "N/A"}</span>
                </div>
                <div className="bullpen-metric">
                    <span className="metric-label">HR/9:</span>
                    <span className="metric-value">{bullpenData.hR9?.toFixed(2) || "N/A"}</span>
                </div>
                <div className="bullpen-metric">
                    <span className="metric-label">FIP:</span>
                    <span className="metric-value">{bullpenData.fip?.toFixed(2) || "N/A"}</span>
                </div>
                {/* Removed OPS since it's not in the model */}
            </div>

            {bullpenData.lastUsed && (
                <div className="bullpen-usage">
                    <h5>Recent Usage</h5>
                    <div className="usage-details">
                        {bullpenData.lastUsed.map((pitcher, index) => (
                            <div key={index} className="pitcher-usage">
                                <span className="pitcher-name">{pitcher.name}</span>
                                <span className="pitcher-days">{pitcher.daysRest} days rest</span>
                                <span className="pitcher-ip">{pitcher.ip} IP</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default BullpenStats;