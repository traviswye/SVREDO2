import React, { useState, useEffect } from "react";
import axios from "axios";
import "../css/PickHistory.css";

const PickHistory = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeFilter, setActiveFilter] = useState("ALL");
    const [summaryStats, setSummaryStats] = useState({});

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
                        date: "2025-03-30",
                        game: "Dodgers @ Giants",
                        pickType: "Moneyline",
                        pick: "Dodgers",
                        odds: -160,
                        result: "Win",
                        model: "BlendedR"
                    },
                    {
                        id: 2,
                        date: "2025-03-30",
                        game: "Yankees @ Red Sox",
                        pickType: "F5 Moneyline",
                        pick: "Yankees",
                        odds: -140,
                        result: "Win",
                        model: "BlendedR"
                    },
                    {
                        id: 3,
                        date: "2025-03-30",
                        game: "Braves @ Mets",
                        pickType: "Run Line",
                        pick: "Braves -1.5",
                        odds: +130,
                        result: "Loss",
                        model: "PitcherAdvantage"
                    },
                    {
                        id: 4,
                        date: "2025-03-29",
                        game: "Cubs @ Cardinals",
                        pickType: "Total",
                        pick: "Over 8.5",
                        odds: -110,
                        result: "Win",
                        model: "BlendedR"
                    },
                    {
                        id: 5,
                        date: "2025-03-29",
                        game: "Phillies @ Nationals",
                        pickType: "F5 Total",
                        pick: "Under 4.5",
                        odds: -115,
                        result: "Loss",
                        model: "BlendedR"
                    },
                    {
                        id: 6,
                        date: "2025-03-29",
                        game: "Astros @ Mariners",
                        pickType: "NRFI",
                        pick: "NRFI",
                        odds: -140,
                        result: "Win",
                        model: "NRFIModel"
                    },
                    {
                        id: 7,
                        date: "2025-03-28",
                        game: "Padres @ Rockies",
                        pickType: "Prop",
                        pick: "Machado Over 1.5 Hits",
                        odds: +140,
                        result: "Win",
                        model: "PropsModel"
                    },
                    {
                        id: 8,
                        date: "2025-03-28",
                        game: "Tigers @ Blue Jays",
                        pickType: "Moneyline",
                        pick: "Blue Jays",
                        odds: -180,
                        result: "Win",
                        model: "BlendedR"
                    },
                    {
                        id: 9,
                        date: "2025-03-28",
                        game: "Brewers @ Reds",
                        pickType: "Run Line",
                        pick: "Brewers -1.5",
                        odds: +130,
                        result: "Loss",
                        model: "PitcherAdvantage"
                    },
                    {
                        id: 10,
                        date: "2025-03-27",
                        game: "Angels @ Athletics",
                        pickType: "NRFI",
                        pick: "NRFI",
                        odds: -120,
                        result: "Win",
                        model: "NRFIModel"
                    },
                    {
                        id: 11,
                        date: "2025-03-27",
                        game: "Rays @ Orioles",
                        pickType: "Prop",
                        pick: "Adley Rutschman Over 0.5 RBI",
                        odds: +110,
                        result: "Loss",
                        model: "PropsModel"
                    },
                    {
                        id: 12,
                        date: "2025-03-27",
                        game: "Guardians @ Twins",
                        pickType: "F5 Moneyline",
                        pick: "Guardians",
                        odds: +105,
                        result: "Win",
                        model: "BlendedR"
                    }
                ];

                setData(sampleData);

                // Calculate summary statistics
                calculateSummaryStats(sampleData);
            } catch (error) {
                console.error("Error fetching pick history:", error);
                setError("Failed to load pick history. Please try again later.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Calculate summary stats from the historical data
    const calculateSummaryStats = (historyData) => {
        // Initialize stats object
        const stats = {
            ALL: { wins: 0, losses: 0, winRate: 0, profit: 0 },
            Moneyline: { wins: 0, losses: 0, winRate: 0, profit: 0 },
            "Run Line": { wins: 0, losses: 0, winRate: 0, profit: 0 },
            Total: { wins: 0, losses: 0, winRate: 0, profit: 0 },
            F5: { wins: 0, losses: 0, winRate: 0, profit: 0 },
            NRFI: { wins: 0, losses: 0, winRate: 0, profit: 0 },
            Prop: { wins: 0, losses: 0, winRate: 0, profit: 0 }
        };

        // Process each pick
        historyData.forEach(pick => {
            // Calculate profit based on odds
            const stakeAmount = 100; // Standard $100 stake
            let profit = 0;

            if (pick.result === "Win") {
                if (pick.odds > 0) {
                    profit = (stakeAmount * pick.odds) / 100;
                } else {
                    profit = stakeAmount / (Math.abs(pick.odds) / 100);
                }
            } else {
                profit = -stakeAmount;
            }

            // Update ALL category
            if (pick.result === "Win") stats.ALL.wins++;
            else stats.ALL.losses++;
            stats.ALL.profit += profit;

            // Update specific category
            const category = pick.pickType.includes("F5") ? "F5" : pick.pickType;

            if (!stats[category]) {
                stats[category] = { wins: 0, losses: 0, winRate: 0, profit: 0 };
            }

            if (pick.result === "Win") stats[category].wins++;
            else stats[category].losses++;
            stats[category].profit += profit;
        });

        // Calculate win rates for each category
        Object.keys(stats).forEach(category => {
            const total = stats[category].wins + stats[category].losses;
            stats[category].winRate = total > 0 ? (stats[category].wins / total) * 100 : 0;
            stats[category].profit = Math.round(stats[category].profit);
        });

        setSummaryStats(stats);
    };

    // Handle filter change
    const handleFilterChange = (filter) => {
        setActiveFilter(filter);
    };

    // Filter data based on active filter
    const getFilteredData = () => {
        if (activeFilter === "ALL") {
            return data;
        }

        if (activeFilter === "F5") {
            return data.filter(pick => pick.pickType.includes("F5"));
        }

        return data.filter(pick => pick.pickType === activeFilter);
    };

    // Format the odds display
    const formatOdds = (odds) => {
        if (odds > 0) {
            return `+${odds}`;
        }
        return odds;
    };

    // Render the result with appropriate styling
    const renderResult = (result) => {
        return <span className={`result-${result.toLowerCase()}`}>{result}</span>;
    };

    // Format the date display
    const formatDate = (dateString) => {
        const options = { month: 'short', day: 'numeric', year: 'numeric' };
        return new Date(dateString).toLocaleDateString(undefined, options);
    };

    if (loading) {
        return <div className="loading-message">Loading pick history...</div>;
    }

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    if (data.length === 0) {
        return <div className="no-data-message">No pick history available.</div>;
    }

    return (
        <div className="pick-history-container">
            <h2 className="pick-history-title">Pick History & Performance</h2>

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

            {/* Stats Summary Display */}
            <div className="stats-summary">
                {summaryStats[activeFilter] && (
                    <>
                        <div className="stat-card">
                            <div className="stat-title">Record</div>
                            <div className="stat-value">{summaryStats[activeFilter].wins} - {summaryStats[activeFilter].losses}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-title">Win Rate</div>
                            <div className="stat-value">{summaryStats[activeFilter].winRate.toFixed(1)}%</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-title">Profit</div>
                            <div className={`stat-value ${summaryStats[activeFilter].profit >= 0 ? 'profit-positive' : 'profit-negative'}`}>
                                ${summaryStats[activeFilter].profit.toLocaleString()}
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-title">Total Bets</div>
                            <div className="stat-value">{summaryStats[activeFilter].wins + summaryStats[activeFilter].losses}</div>
                        </div>
                    </>
                )}
            </div>

            <div className="pick-history-table-wrapper">
                <table className="pick-history-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Game</th>
                            <th>Pick Type</th>
                            <th>Pick</th>
                            <th>Odds</th>
                            <th>Result</th>
                            <th>Model</th>
                        </tr>
                    </thead>
                    <tbody>
                        {getFilteredData().map((pick) => (
                            <tr key={pick.id}>
                                <td>{formatDate(pick.date)}</td>
                                <td>{pick.game}</td>
                                <td>{pick.pickType}</td>
                                <td>{pick.pick}</td>
                                <td className="numeric-cell">{formatOdds(pick.odds)}</td>
                                <td>{renderResult(pick.result)}</td>
                                <td>{pick.model}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default PickHistory;