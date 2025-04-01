import React, { useState, useEffect } from "react";
import axios from "axios";
import "../css/TodaysEV.css";

const TodaysEV = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: "time", direction: "asc" });

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);

            try {
                // Format today's date as YYYY-MM-DD for full API calls
                const today = new Date().toISOString().split("T")[0];
                // Format today's date as YY-MM-DD for GamePreviews API
                const shortToday = `${today.slice(2, 4)}-${today.slice(5, 7)}-${today.slice(8, 10)}`;

                // Make all API calls in parallel
                const [
                    gamePreviewsResponse,
                    pitcherRankingsResponse,
                    runExpectancyF5Response,
                    runExpectancyResponse,
                ] = await Promise.all([
                    axios.get(`https://localhost:44346/api/GamePreviews/${shortToday}`),
                    axios.get(`https://localhost:44346/api/Blending/enhancedDailyPitcherRankings?date=${today}`),
                    axios.get(`https://localhost:44346/api/Blending/adjustedRunExpectancyF5?date=${today}`),
                    axios.get(`https://localhost:44346/api/Blending/adjustedRunExpectancy?date=${today}`),

                    //for testing purposes....
                    // axios.get(`https://localhost:44346/api/GamePreviews/25-03-30`),
                    // axios.get(`https://localhost:44346/api/Blending/enhancedDailyPitcherRankings?date=2025-03-30`),
                    // axios.get(`https://localhost:44346/api/Blending/adjustedRunExpectancyF5?date=2025-03-30`),
                    // axios.get(`https://localhost:44346/api/Blending/adjustedRunExpectancy?date=2025-03-30`),

                ]);

                // Create reference maps for easier data merging
                const pitcherMap = createPitcherMap(pitcherRankingsResponse.data);
                const f5RunsMap = createRunsMap(runExpectancyF5Response.data);
                const fullRunsMap = createRunsMap(runExpectancyResponse.data);

                // Merge data from different endpoints
                const mergedData = gamePreviewsResponse.data.map((game) => {
                    // Get pitcher data
                    const homePitcher = pitcherMap[game.homePitcher] || {};
                    const awayPitcher = pitcherMap[game.awayPitcher] || {};

                    // Get runs expectations
                    const f5Runs = f5RunsMap[game.id] || { home: {}, away: {} };
                    const fullRuns = fullRunsMap[game.id] || { home: {}, away: {} };

                    return {
                        id: game.id,
                        time: game.time,
                        homeTeam: game.homeTeam,
                        awayTeam: game.awayTeam,
                        homePitcher: game.homePitcher,
                        homePitcherCompositeScore: homePitcher.compositeScore || "N/A",
                        homePitcherPerformanceStatus: homePitcher.performanceStatus || "N/A",
                        awayPitcher: game.awayPitcher,
                        awayPitcherCompositeScore: awayPitcher.compositeScore || "N/A",
                        awayPitcherPerformanceStatus: awayPitcher.performanceStatus || "N/A",
                        homeTeamAdjustedRunsF5: f5Runs.home.adjustedExpectedRuns || "N/A",
                        awayTeamAdjustedRunsF5: f5Runs.away.adjustedExpectedRuns || "N/A",
                        f5Total: calculateTotal(f5Runs.home.adjustedExpectedRuns, f5Runs.away.adjustedExpectedRuns),
                        homeTeamAdjustedRuns: fullRuns.home.adjustedExpectedRuns || "N/A",
                        awayTeamAdjustedRuns: fullRuns.away.adjustedExpectedRuns || "N/A",
                        fullTotal: calculateTotal(fullRuns.home.adjustedExpectedRuns, fullRuns.away.adjustedExpectedRuns),
                        venue: game.venue,
                        temperature: game.temperature,
                        rainProbability: game.rainProbability,
                    };
                });

                setData(mergedData);
            } catch (error) {
                console.error("Error fetching data:", error);
                setError("Failed to load data. Please try again later.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Helper function to create pitcher data map
    const createPitcherMap = (pitcherData) => {
        if (!pitcherData || !pitcherData.enhancedRankings) return {};

        return pitcherData.enhancedRankings.reduce((map, pitcher) => {
            map[pitcher.pitcherId] = {
                compositeScore: pitcher.compositeScore,
                performanceStatus: pitcher.trendAnalysis?.performanceStatus || "CONSISTENT",
            };
            return map;
        }, {});
    };

    // Helper function to create runs expectancy map
    const createRunsMap = (runsData) => {
        if (!runsData || !runsData.games) return {};

        return runsData.games.reduce((map, game) => {
            map[game.gameId] = {
                home: {
                    team: game.homeTeam.team,
                    adjustedExpectedRuns: game.homeTeam.adjustedExpectedRuns,
                },
                away: {
                    team: game.awayTeam.team,
                    adjustedExpectedRuns: game.awayTeam.adjustedExpectedRuns,
                },
            };
            return map;
        }, {});
    };

    // Helper function to calculate totals, handling possible N/A values
    const calculateTotal = (value1, value2) => {
        if (typeof value1 !== "number" || typeof value2 !== "number") {
            return "N/A";
        }
        return (value1 + value2).toFixed(2);
    };

    // Format numbers consistently
    const formatNumber = (value) => {
        if (typeof value !== "number") return value;
        return value.toFixed(2);
    };

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
                // Handle numeric and string values appropriately
                if (a[sortConfig.key] === "N/A") return 1;
                if (b[sortConfig.key] === "N/A") return -1;

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

    // Render performance status with appropriate styling
    const renderPerformanceStatus = (status) => {
        if (status === "HOT") {
            return <span className="status-hot">HOT</span>;
        } else if (status === "COLD") {
            return <span className="status-cold">COLD</span>;
        } else {
            return <span className="status-consistent">CONSISTENT</span>;
        }
    };

    // Generate BBRef link for pitcher
    const getBbRefLink = (pitcherId) => {
        if (!pitcherId || pitcherId === "N/A") return "#";
        const firstLetter = pitcherId.charAt(0);
        return `https://www.baseball-reference.com/players/${firstLetter}/${pitcherId}.shtml`;
    };

    if (loading) {
        return <div className="loading-message">Calculating today's games...</div>;
    }

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    if (data.length === 0) {
        return <div className="no-data-message">No games scheduled for today.</div>;
    }

    return (
        <div className="todays-ev-container">
            <h2 className="todays-ev-title">Today's Expected Values</h2>
            <div className="todays-ev-table-wrapper">
                <table className="todays-ev-table">
                    <thead>
                        <tr>
                            <th onClick={() => requestSort("time")}>Time</th>
                            <th onClick={() => requestSort("homeTeam")}>Home Team</th>
                            <th onClick={() => requestSort("awayTeam")}>Away Team</th>
                            <th onClick={() => requestSort("homePitcher")}>Home Pitcher</th>
                            <th onClick={() => requestSort("homePitcherCompositeScore")}>SP Score</th>
                            <th>Home Pitcher Status</th>
                            <th onClick={() => requestSort("awayPitcher")}>Away Pitcher</th>
                            <th onClick={() => requestSort("awayPitcherCompositeScore")}>SP Score</th>
                            <th>Away Pitcher Status</th>
                            <th onClick={() => requestSort("homeTeamAdjustedRunsF5")}>Home F5 Runs</th>
                            <th onClick={() => requestSort("awayTeamAdjustedRunsF5")}>Away F5 Runs</th>
                            <th onClick={() => requestSort("f5Total")}>F5 Total</th>
                            <th onClick={() => requestSort("homeTeamAdjustedRuns")}>Home Full Runs</th>
                            <th onClick={() => requestSort("awayTeamAdjustedRuns")}>Away Full Runs</th>
                            <th onClick={() => requestSort("fullTotal")}>Full Total</th>
                            <th onClick={() => requestSort("venue")}>Venue</th>
                            <th onClick={() => requestSort("temperature")}>Temp</th>
                            <th onClick={() => requestSort("rainProbability")}>Rain %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {getSortedData().map((game) => (
                            <tr key={game.id}>
                                <td>{game.time}</td>
                                <td>{game.homeTeam}</td>
                                <td>{game.awayTeam}</td>
                                <td>
                                    <a href={getBbRefLink(game.homePitcher)} target="_blank" rel="noopener noreferrer">
                                        {game.homePitcher}
                                    </a>
                                </td>
                                <td className="numeric-cell">
                                    {typeof game.homePitcherCompositeScore === "number"
                                        ? game.homePitcherCompositeScore.toFixed(2)
                                        : game.homePitcherCompositeScore}
                                </td>
                                <td>{renderPerformanceStatus(game.homePitcherPerformanceStatus)}</td>
                                <td>
                                    <a href={getBbRefLink(game.awayPitcher)} target="_blank" rel="noopener noreferrer">
                                        {game.awayPitcher}
                                    </a>
                                </td>
                                <td className="numeric-cell">
                                    {typeof game.awayPitcherCompositeScore === "number"
                                        ? game.awayPitcherCompositeScore.toFixed(2)
                                        : game.awayPitcherCompositeScore}
                                </td>
                                <td>{renderPerformanceStatus(game.awayPitcherPerformanceStatus)}</td>
                                <td className="numeric-cell">{formatNumber(game.homeTeamAdjustedRunsF5)}</td>
                                <td className="numeric-cell">{formatNumber(game.awayTeamAdjustedRunsF5)}</td>
                                <td className="numeric-cell total-cell">{game.f5Total}</td>
                                <td className="numeric-cell">{formatNumber(game.homeTeamAdjustedRuns)}</td>
                                <td className="numeric-cell">{formatNumber(game.awayTeamAdjustedRuns)}</td>
                                <td className="numeric-cell total-cell">{game.fullTotal}</td>
                                <td>{game.venue}</td>
                                <td className="numeric-cell">{typeof game.temperature === "number" ? game.temperature.toFixed(1) : game.temperature}</td>
                                <td className="numeric-cell">{game.rainProbability}%</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TodaysEV;