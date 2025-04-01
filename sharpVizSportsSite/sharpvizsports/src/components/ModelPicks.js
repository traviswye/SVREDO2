import React, { useState, useEffect } from "react";
import axios from "axios";
import "../css/ModelPicks.css";

const ModelPicks = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeFilter, setActiveFilter] = useState("ALL");

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);

            try {
                // This is a placeholder - we'll need to implement the actual API call
                // once the endpoint is ready. For now, we'll use sample data.

                // Simulate API call delay
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Sample data for now
                const sampleData = [
                    {
                        id: 1,
                        game: "Dodgers @ Giants",
                        timeStart: "4:05 PM",
                        pickType: "Moneyline",
                        team: "Dodgers",
                        odds: -150,
                        confidence: 0.76,
                        value: 0.12,
                        model: "BlendedR",
                        status: "Pending"
                    },
                    {
                        id: 2,
                        game: "Braves @ Mets",
                        timeStart: "6:10 PM",
                        pickType: "Run Line",
                        team: "Braves",
                        line: -1.5,
                        odds: +140,
                        confidence: 0.68,
                        value: 0.15,
                        model: "PitcherAdvantage",
                        status: "Pending"
                    },
                    {
                        id: 3,
                        game: "Yankees @ Red Sox",
                        timeStart: "7:10 PM",
                        pickType: "F5 Moneyline",
                        team: "Yankees",
                        odds: -120,
                        confidence: 0.72,
                        value: 0.09,
                        model: "BlendedR",
                        status: "Pending"
                    },
                    {
                        id: 4,
                        game: "Cubs @ Cardinals",
                        timeStart: "7:45 PM",
                        pickType: "Total",
                        total: "Over 8.5",
                        odds: -110,
                        confidence: 0.64,
                        value: 0.07,
                        model: "BlendedR",
                        status: "Pending"
                    },
                    {
                        id: 5,
                        game: "Astros @ Mariners",
                        timeStart: "9:40 PM",
                        pickType: "NRFI",
                        odds: -140,
                        confidence: 0.82,
                        value: 0.18,
                        model: "NRFIModel",
                        status: "Pending"
                    },
                    {
                        id: 6,
                        game: "Padres @ Rockies",
                        timeStart: "8:40 PM",
                        pickType: "F5 Total",
                        total: "Under 5.5",
                        odds: -105,
                        confidence: 0.69,
                        value: 0.11,
                        model: "BlendedR",
                        status: "Pending"
                    },
                    {
                        id: 7,
                        game: "Phillies @ Nationals",
                        timeStart: "6:45 PM",
                        pickType: "Prop",
                        player: "Bryce Harper",
                        prop: "Over 1.5 Total Bases",
                        odds: +115,
                        confidence: 0.73,
                        value: 0.14,
                        model: "PropsModel",
                        status: "Pending"
                    }
                ];

                setData(sampleData);
            } catch (error) {
                console.error("Error fetching model picks:", error);
                setError("Failed to load model picks. Please try again later.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Handle filter change
    const handleFilterChange = (filter) => {
        setActiveFilter(filter);
    };

    // Filter data based on active filter
    const getFilteredData = () => {
        if (activeFilter === "ALL") {
            return data;
        }
        return data.filter(pick => pick.pickType.includes(activeFilter));
    };

    // Format the odds display
    const formatOdds = (odds) => {
        if (odds > 0) {
            return `+${odds}`;
        }
        return odds;
    };

    // Render the confidence level with appropriate styling
    const renderConfidence = (confidence) => {
        let className = "confidence-medium";
        if (confidence >= 0.75) {
            className = "confidence-high";
        } else if (confidence < 0.65) {
            className = "confidence-low";
        }

        return <span className={className}>{(confidence * 100).toFixed(0)}%</span>;
    };

    // Render the value with appropriate styling
    const renderValue = (value) => {
        let className = "value-medium";
        if (value >= 0.15) {
            className = "value-high";
        } else if (value < 0.08) {
            className = "value-low";
        }

        return <span className={className}>{value.toFixed(2)}</span>;
    };

    // Get pick details based on pick type
    const getPickDetails = (pick) => {
        switch (pick.pickType) {
            case "Moneyline":
            case "F5 Moneyline":
                return pick.team;
            case "Run Line":
                return `${pick.team} ${pick.line > 0 ? '+' : ''}${pick.line}`;
            case "Total":
            case "F5 Total":
                return pick.total;
            case "NRFI":
                return "No Run First Inning";
            case "Prop":
                return `${pick.player}: ${pick.prop}`;
            default:
                return "";
        }
    };

    if (loading) {
        return <div className="loading-message">Loading model picks...</div>;
    }

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    if (data.length === 0) {
        return <div className="no-data-message">No model picks available for today.</div>;
    }

    return (
        <div className="model-picks-container">
            <h2 className="model-picks-title">Today's Model Picks</h2>

            <div className="picks-filter-tabs">
                <button
                    className={activeFilter === "ALL" ? "active" : ""}
                    onClick={() => handleFilterChange("ALL")}
                >
                    All Picks
                </button>
                <button
                    className={activeFilter === "Moneyline" ? "active" : ""}
                    onClick={() => handleFilterChange("Moneyline")}
                >
                    Moneyline
                </button>
                <button
                    className={activeFilter === "Run Line" ? "active" : ""}
                    onClick={() => handleFilterChange("Run Line")}
                >
                    Run Line
                </button>
                <button
                    className={activeFilter === "Total" ? "active" : ""}
                    onClick={() => handleFilterChange("Total")}
                >
                    Totals
                </button>
                <button
                    className={activeFilter === "F5" ? "active" : ""}
                    onClick={() => handleFilterChange("F5")}
                >
                    F5
                </button>
                <button
                    className={activeFilter === "NRFI" ? "active" : ""}
                    onClick={() => handleFilterChange("NRFI")}
                >
                    NRFI
                </button>
                <button
                    className={activeFilter === "Prop" ? "active" : ""}
                    onClick={() => handleFilterChange("Prop")}
                >
                    Props
                </button>
            </div>

            <div className="model-picks-table-wrapper">
                <table className="model-picks-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Game</th>
                            <th>Pick Type</th>
                            <th>Pick</th>
                            <th>Odds</th>
                            <th>Confidence</th>
                            <th>Value</th>
                            <th>Model</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {getFilteredData().map((pick) => (
                            <tr key={pick.id}>
                                <td>{pick.timeStart}</td>
                                <td>{pick.game}</td>
                                <td>{pick.pickType}</td>
                                <td className="pick-detail">{getPickDetails(pick)}</td>
                                <td className="numeric-cell">{formatOdds(pick.odds)}</td>
                                <td>{renderConfidence(pick.confidence)}</td>
                                <td>{renderValue(pick.value)}</td>
                                <td>{pick.model}</td>
                                <td>
                                    <span className={`status-${pick.status.toLowerCase()}`}>
                                        {pick.status}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="model-picks-legend">
                <div className="legend-item">
                    <span className="confidence-high">High Confidence (≥75%)</span>
                </div>
                <div className="legend-item">
                    <span className="confidence-medium">Medium Confidence (65-74%)</span>
                </div>
                <div className="legend-item">
                    <span className="confidence-low">Low Confidence (&lt;65%)</span>
                </div>
            </div>
        </div>
    );
};

export default ModelPicks;