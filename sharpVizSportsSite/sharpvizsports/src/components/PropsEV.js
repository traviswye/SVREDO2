import React, { useState, useEffect } from "react";
import axios from "axios";
import "../css/PropsEV.css";

const PropsEV = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: "player", direction: "asc" });

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);

            try {
                // This is a placeholder - we'll need to implement the actual API call
                // once the endpoint is ready. For now, we'll use sample data.

                // Simulate API call delay
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Sample data - to be replaced with actual API response
                const sampleData = [
                    {
                        id: 1,
                        player: "guerrvl01",
                        playerName: "Vladimir Guerrero Jr.",
                        team: "Blue Jays",
                        game: "Blue Jays @ Yankees",
                        propType: "Home Runs",
                        line: 0.5,
                        recommendation: "Over",
                        confidence: 0.72,
                        predictedValue: 0.83,
                        ev: 0.33
                    },
                    {
                        id: 2,
                        player: "troutmi01",
                        playerName: "Mike Trout",
                        team: "Angels",
                        game: "Angels @ Astros",
                        propType: "Hits",
                        line: 0.5,
                        recommendation: "Over",
                        confidence: 0.68,
                        predictedValue: 1.12,
                        ev: 0.62
                    },
                    {
                        id: 3,
                        player: "judgeaa01",
                        playerName: "Aaron Judge",
                        team: "Yankees",
                        game: "Blue Jays @ Yankees",
                        propType: "Total Bases",
                        line: 1.5,
                        recommendation: "Over",
                        confidence: 0.65,
                        predictedValue: 2.3,
                        ev: 0.8
                    },
                    {
                        id: 4,
                        player: "degronja01",
                        playerName: "Jacob deGrom",
                        team: "Rangers",
                        game: "Rangers @ Mariners",
                        propType: "Strikeouts",
                        line: 6.5,
                        recommendation: "Over",
                        confidence: 0.75,
                        predictedValue: 8.2,
                        ev: 1.7
                    },
                    {
                        id: 5,
                        player: "arenano01",
                        playerName: "Nolan Arenado",
                        team: "Cardinals",
                        game: "Cardinals @ Cubs",
                        propType: "RBIs",
                        line: 0.5,
                        recommendation: "Under",
                        confidence: 0.63,
                        predictedValue: 0.3,
                        ev: 0.2
                    }
                ];

                setData(sampleData);
            } catch (error) {
                console.error("Error fetching props data:", error);
                setError("Failed to load props data. Please try again later.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Handle sorting
    const requestSort = (key) => {
        let direction = "asc";
        if (sortConfig.key === key && sortConfig.direction === "asc") {
            direction = "desc";
        }
        setSortConfig({ key, direction });
    };

    // Get sorted data
    const getSortedData = () => {
        if (!data || data.length === 0) return [];

        const sortableData = [...data];
        if (sortConfig.key) {
            sortableData.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) {
                    return sortConfig.direction === "asc" ? -1 : 1;
                }
                if (a[sortConfig.key] > b[sortConfig.key]) {
                    return sortConfig.direction === "asc" ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableData;
    };

    // Generate BBRef link for player
    const getBbRefLink = (playerId) => {
        if (!playerId) return "#";
        const firstLetter = playerId.charAt(0);
        return `https://www.baseball-reference.com/players/${firstLetter}/${playerId}.shtml`;
    };

    // Render confidence with color coding
    const renderConfidence = (confidence) => {
        let className = "confidence-medium";
        if (confidence >= 0.7) {
            className = "confidence-high";
        } else if (confidence < 0.6) {
            className = "confidence-low";
        }

        return <span className={className}>{(confidence * 100).toFixed(0)}%</span>;
    };

    // Render recommendation with styling
    const renderRecommendation = (recommendation, ev) => {
        const className = recommendation === "Over" ? "recommendation-over" : "recommendation-under";
        return (
            <div className="recommendation-container">
                <span className={className}>{recommendation}</span>
                <span className="ev-value">(EV: {ev.toFixed(2)})</span>
            </div>
        );
    };

    if (loading) {
        return <div className="loading-message">Loading props data...</div>;
    }

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    if (data.length === 0) {
        return <div className="no-data-message">No props data available.</div>;
    }

    return (
        <div className="props-ev-container">
            <h2 className="props-ev-title">Props Betting Edge</h2>
            <div className="props-ev-table-wrapper">
                <table className="props-ev-table">
                    <thead>
                        <tr>
                            <th onClick={() => requestSort("player")}>Player</th>
                            <th onClick={() => requestSort("team")}>Team</th>
                            <th onClick={() => requestSort("game")}>Game</th>
                            <th onClick={() => requestSort("propType")}>Prop Type</th>
                            <th onClick={() => requestSort("line")}>Line</th>
                            <th onClick={() => requestSort("predictedValue")}>Predicted</th>
                            <th onClick={() => requestSort("recommendation")}>Recommendation</th>
                            <th onClick={() => requestSort("confidence")}>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {getSortedData().map((prop) => (
                            <tr key={prop.id}>
                                <td>
                                    <a href={getBbRefLink(prop.player)} target="_blank" rel="noopener noreferrer">
                                        {prop.playerName}
                                    </a>
                                </td>
                                <td>{prop.team}</td>
                                <td>{prop.game}</td>
                                <td>{prop.propType}</td>
                                <td className="numeric-cell">{prop.line.toFixed(1)}</td>
                                <td className="numeric-cell">{prop.predictedValue.toFixed(2)}</td>
                                <td>{renderRecommendation(prop.recommendation, prop.ev)}</td>
                                <td>{renderConfidence(prop.confidence)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default PropsEV;