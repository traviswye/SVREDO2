import React, { useState, useEffect } from "react";
import "../css/HvpDrawer.css";

const HvpDrawer = ({ isOpen, onClose }) => {
    const [hvpData, setHvpData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: "ba", direction: "desc" });
    const [selectedPitcher, setSelectedPitcher] = useState("");
    const [uniquePitchers, setUniquePitchers] = useState([]);

    useEffect(() => {
        if (isOpen) {
            fetchData();
        }
    }, [isOpen]);

    const fetchData = async () => {
        setLoading(true);
        try {
            // Format today's date as YY-MM-DD for the API call
            const today = new Date();
            const formattedDate = `${String(today.getFullYear()).slice(-2)}-${String(
                today.getMonth() + 1
            ).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

            const response = await fetch(
                `https://localhost:44346/api/HitterVsPitcher/allRecordsByDate/${formattedDate}`
            );

            if (!response.ok) {
                throw new Error(`API responded with status: ${response.status}`);
            }

            const data = await response.json();
            setHvpData(data);

            // Extract unique pitchers for the filter dropdown
            const pitchers = [...new Set(data.map(item => item.pitcher))];
            setUniquePitchers(pitchers);
        } catch (err) {
            console.error("Error fetching HVP data:", err);
            setError("Failed to load hitter vs pitcher data");
        } finally {
            setLoading(false);
        }
    };

    const handleSort = (key) => {
        let direction = "desc";
        if (sortConfig.key === key && sortConfig.direction === "desc") {
            direction = "asc";
        }
        setSortConfig({ key, direction });
    };

    const handlePitcherChange = (e) => {
        setSelectedPitcher(e.target.value);
    };

    if (!isOpen) return null;

    // Format functions
    const formatBattingAvg = (value) => {
        if (value === undefined || value === null) return ".000";
        return value.toFixed(3).toString().replace(/^0\./, ".");
    };

    // Filter and sort data
    const getFilteredAndSortedData = () => {
        let filteredData = [...hvpData];

        // Apply pitcher filter if selected
        if (selectedPitcher) {
            filteredData = filteredData.filter(item => item.pitcher === selectedPitcher);
        }

        // Apply sorting
        filteredData.sort((a, b) => {
            const valueA = a[sortConfig.key];
            const valueB = b[sortConfig.key];

            if (typeof valueA === 'number' && typeof valueB === 'number') {
                return sortConfig.direction === 'asc' ? valueA - valueB : valueB - valueA;
            }

            // Handle string comparison
            const stringA = String(valueA || '');
            const stringB = String(valueB || '');
            return sortConfig.direction === 'asc'
                ? stringA.localeCompare(stringB)
                : stringB.localeCompare(stringA);
        });

        return filteredData;
    };

    // Get sort direction indicator
    const getSortDirectionIndicator = (key) => {
        if (sortConfig.key !== key) return '';
        return sortConfig.direction === 'asc' ? ' ↑' : ' ↓';
    };

    // Generate BBRef URL
    const getBbRefURL = (playerId) => {
        if (!playerId) return "#";
        const firstLetter = playerId.charAt(0);
        return `https://www.baseball-reference.com/players/${firstLetter}/${playerId}.shtml`;
    };

    const filteredAndSortedData = getFilteredAndSortedData();

    return (
        <div className="hvp-drawer-overlay">
            <div className="hvp-drawer">
                <div className="hvp-drawer-header">
                    <h2>Hitter vs Pitcher Matchups</h2>
                    <button className="hvp-close-button" onClick={onClose}>
                        ×
                    </button>
                </div>

                <div className="hvp-drawer-controls">
                    <div className="hvp-filter-container">
                        <label htmlFor="pitcher-filter">Filter by Pitcher:</label>
                        <select
                            id="pitcher-filter"
                            value={selectedPitcher}
                            onChange={handlePitcherChange}
                            className="hvp-select"
                        >
                            <option value="">All Pitchers</option>
                            {uniquePitchers.map(pitcher => (
                                <option key={pitcher} value={pitcher}>
                                    {pitcher}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="hvp-stats-info">
                        <span>Showing {filteredAndSortedData.length} matchups</span>
                    </div>
                </div>

                {loading ? (
                    <div className="hvp-loading">
                        <div className="hvp-spinner"></div>
                        <p>Loading matchup data...</p>
                    </div>
                ) : error ? (
                    <div className="hvp-error">{error}</div>
                ) : (
                    <div className="hvp-table-container">
                        <table className="hvp-table">
                            <thead>
                                <tr>
                                    <th onClick={() => handleSort("pitcher")}>
                                        Pitcher {getSortDirectionIndicator("pitcher")}
                                    </th>
                                    <th onClick={() => handleSort("hitter")}>
                                        Hitter {getSortDirectionIndicator("hitter")}
                                    </th>
                                    <th onClick={() => handleSort("pa")}>
                                        PA {getSortDirectionIndicator("pa")}
                                    </th>
                                    <th onClick={() => handleSort("hits")}>
                                        H {getSortDirectionIndicator("hits")}
                                    </th>
                                    <th onClick={() => handleSort("hr")}>
                                        HR {getSortDirectionIndicator("hr")}
                                    </th>
                                    <th onClick={() => handleSort("rbi")}>
                                        RBI {getSortDirectionIndicator("rbi")}
                                    </th>
                                    <th onClick={() => handleSort("bb")}>
                                        BB {getSortDirectionIndicator("bb")}
                                    </th>
                                    <th onClick={() => handleSort("so")}>
                                        SO {getSortDirectionIndicator("so")}
                                    </th>
                                    <th onClick={() => handleSort("ba")}>
                                        BA {getSortDirectionIndicator("ba")}
                                    </th>
                                    <th onClick={() => handleSort("obp")}>
                                        OBP {getSortDirectionIndicator("obp")}
                                    </th>
                                    <th onClick={() => handleSort("slg")}>
                                        SLG {getSortDirectionIndicator("slg")}
                                    </th>
                                    <th onClick={() => handleSort("ops")}>
                                        OPS {getSortDirectionIndicator("ops")}
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredAndSortedData.length > 0 ? (
                                    filteredAndSortedData.map((matchup) => (
                                        <tr key={matchup.id} className="hvp-row">
                                            <td>
                                                <a
                                                    href={getBbRefURL(matchup.pitcher)}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="hvp-player-link"
                                                >
                                                    {matchup.pitcher}
                                                </a>
                                            </td>
                                            <td>
                                                <a
                                                    href={getBbRefURL(matchup.hitter)}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="hvp-player-link"
                                                >
                                                    {matchup.hitter}
                                                </a>
                                            </td>
                                            <td>{matchup.pa}</td>
                                            <td>{matchup.hits}</td>
                                            <td>{matchup.hr}</td>
                                            <td>{matchup.rbi}</td>
                                            <td>{matchup.bb}</td>
                                            <td>{matchup.so}</td>
                                            <td>{formatBattingAvg(matchup.ba)}</td>
                                            <td>{formatBattingAvg(matchup.obp)}</td>
                                            <td>{formatBattingAvg(matchup.slg)}</td>
                                            <td>{formatBattingAvg(matchup.ops)}</td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="12" className="hvp-no-data-message">
                                            No matchup data available for the selected criteria
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default HvpDrawer;