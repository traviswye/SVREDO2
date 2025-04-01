import React, { useState, useEffect } from "react";
import axios from "axios";
import "../css/NRFIEV.css";

const NRFIEV = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: "nrfiProbability", direction: "desc" });

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);

            try {
                // This is a placeholder - we'll need to implement the actual API call
                // once the endpoint is ready. For now, we'll use sample data.

                // Simulate API call delay
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Format today's date for API call
                const today = new Date().toISOString().split("T")[0];
                const shortToday = `${today.slice(2, 4)}-${today.slice(5, 7)}-${today.slice(8, 10)}`;

                // In production, we would call the NRFI evaluation API:
                // const response = await axios.get(`https://localhost:44346/api/Evaluation/evaluateNRFI1st/${shortToday}`);
                // setData(response.data);

                // Sample data for now
                const sampleData = [
                    {
                        gameId: 1,
                        homeTeam: "Dodgers",
                        awayTeam: "Padres",
                        homePitcher: "kershcl01",
                        homePitcherName: "Clayton Kershaw",
                        awayPitcher: "snellbl01",
                        awayPitcherName: "Blake Snell",
                        nrfiProbability: 0.78,
                        yrfiProbability: 0.22,
                        recommendedBet: "NRFI",
                        homeFirstInningAvg: 0.4,
                        awayFirstInningAvg: 0.5,
                        homePitcherFirstInningERA: 1.2,
                        awayPitcherFirstInningERA: 1.8,
                        odds: -140,
                        ev: 0.15
                    },
                    {
                        gameId: 2,
                        homeTeam: "Yankees",
                        awayTeam: "Red Sox",
                        homePitcher: "colega01",
                        homePitcherName: "Gerrit Cole",
                        awayPitcher: "salech01",
                        awayPitcherName: "Chris Sale",
                        nrfiProbability: 0.71,
                        yrfiProbability: 0.29,
                        recommendedBet: "NRFI",
                        homeFirstInningAvg: 0.6,
                        awayFirstInningAvg: 0.7,
                        homePitcherFirstInningERA: 2.1,
                        awayPitcherFirstInningERA: 2.3,
                        odds: -130,
                        ev: 0.12
                    },
                    {
                        gameId: 3,
                        homeTeam: "Braves",
                        awayTeam: "Mets",
                        homePitcher: "soriasp01",
                        homePitcherName: "Spencer Strider",
                        awayPitcher: "seaveto01",
                        awayPitcherName: "Tom Seaver",
                        nrfiProbability: 0.63,
                        yrfiProbability: 0.37,
                        recommendedBet: "NRFI",
                        homeFirstInningAvg: 0.7,
                        awayFirstInningAvg: 0.5,
                        homePitcherFirstInningERA: 2.8,
                        awayPitcherFirstInningERA: 1.9,
                        odds: -120,
                        ev: 0.08
                    },
                    {
                        gameId: 4,
                        homeTeam: "Astros",
                        awayTeam: "Rangers",
                        homePitcher: "verlaju01",
                        homePitcherName: "Justin Verlander",
                        awayPitcher: "schen00",
                        awayPitcherName: "Max Scherzer",
                        nrfiProbability: 0.69,
                        yrfiProbability: 0.31,
                        recommendedBet: "NRFI",
                        homeFirstInningAvg: 0.5,
                        awayFirstInningAvg: 0.6,
                        homePitcherFirstInningERA: 1.7,
                        awayPitcherFirstInningERA: 2.5,
                        odds: -125,
                        ev: 0.11
                    },
                    {
                        gameId: 5,
                        homeTeam: "Giants",
                        awayTeam: "Diamondbacks",
                        homePitcher: "webblo01",
                        homePitcherName: "Logan Webb",
                        awayPitcher: "gallaza01",
                        awayPitcherName: "Zac Gallen",
                        nrfiProbability: 0.81,
                        yrfiProbability: 0.19,
                        recommendedBet: "NRFI",
                        homeFirstInningAvg: 0.3,
                        awayFirstInningAvg: 0.4,
                        homePitcherFirstInningERA: 1.1,
                        awayPitcherFirstInningERA: 1.5,
                        odds: -150,
                        ev: 0.17
                    }
                ];

                setData(sampleData);
            } catch (error) {
                console.error("Error fetching NRFI data:", error);
                setError("Failed to load NRFI data. Please try again later.");
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

    // Generate BBRef link for pitcher
    const getBbRefLink = (pitcherId) => {
        if (!pitcherId) return "#";
        const firstLetter = pitcherId.charAt(0);
        return `https://www.baseball-reference.com/players/${firstLetter}/${pitcherId}.shtml`;
    };

    // Format probability as percentage
    const formatProbability = (value) => {
        return `${(value * 100).toFixed(1)}%`;
    };

    // Render formatted odds
    const renderOdds = (odds) => {
        if (odds > 0) {
            return `+${odds}`;
        }
        return odds;
    };

    // Render recommendation with styling
    const renderRecommendation = (recommendation, ev) => {
        const className = recommendation === "NRFI" ? "recommendation-nrfi" : "recommendation-yrfi";
        const evClass = ev > 0.1 ? "ev-high" : ev > 0.05 ? "ev-medium" : "ev-low";

        return (
            <div className="recommendation-container">
                <span className={className}>{recommendation}</span>
                <span className={`ev-value ${evClass}`}>(EV: {ev.toFixed(2)})</span>
            </div>
        );
    };

    // Render probability with color coding
    const renderProbability = (probability) => {
        let className = "probability-medium";
        if (probability >= 0.75) {
            className = "probability-high";
        } else if (probability < 0.6) {
            className = "probability-low";
        }

        return <span className={className}>{formatProbability(probability)}</span>;
    };

    if (loading) {
        return <div className="loading-message">Loading NRFI analysis...</div>;
    }

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    if (data.length === 0) {
        return <div className="no-data-message">No NRFI data available for today's games.</div>;
    }

    return (
        <div className="nrfi-ev-container">
            <h2 className="nrfi-ev-title">NRFI/YRFI Analysis</h2>
            <div className="nrfi-ev-table-wrapper">
                <table className="nrfi-ev-table">
                    <thead>
                        <tr>
                            <th onClick={() => requestSort("homeTeam")}>Game</th>
                            <th onClick={() => requestSort("homePitcher")}>Home Pitcher</th>
                            <th onClick={() => requestSort("awayPitcher")}>Away Pitcher</th>
                            <th onClick={() => requestSort("nrfiProbability")}>NRFI Prob</th>
                            <th onClick={() => requestSort("yrfiProbability")}>YRFI Prob</th>
                            <th onClick={() => requestSort("homePitcherFirstInningERA")}>Home P 1st ERA</th>
                            <th onClick={() => requestSort("awayPitcherFirstInningERA")}>Away P 1st ERA</th>
                            <th onClick={() => requestSort("homeFirstInningAvg")}>Home 1st Avg</th>
                            <th onClick={() => requestSort("awayFirstInningAvg")}>Away 1st Avg</th>
                            <th onClick={() => requestSort("odds")}>Odds</th>
                            <th onClick={() => requestSort("recommendedBet")}>Recommendation</th>
                        </tr>
                    </thead>
                    <tbody>
                        {getSortedData().map((game) => (
                            <tr key={game.gameId}>
                                <td>{game.awayTeam} @ {game.homeTeam}</td>
                                <td>
                                    <a href={getBbRefLink(game.homePitcher)} target="_blank" rel="noopener noreferrer">
                                        {game.homePitcherName}
                                    </a>
                                </td>
                                <td>
                                    <a href={getBbRefLink(game.awayPitcher)} target="_blank" rel="noopener noreferrer">
                                        {game.awayPitcherName}
                                    </a>
                                </td>
                                <td>{renderProbability(game.nrfiProbability)}</td>
                                <td>{renderProbability(game.yrfiProbability)}</td>
                                <td className="numeric-cell">{game.homePitcherFirstInningERA.toFixed(2)}</td>
                                <td className="numeric-cell">{game.awayPitcherFirstInningERA.toFixed(2)}</td>
                                <td className="numeric-cell">{game.homeFirstInningAvg.toFixed(2)}</td>
                                <td className="numeric-cell">{game.awayFirstInningAvg.toFixed(2)}</td>
                                <td className="numeric-cell">{renderOdds(game.odds)}</td>
                                <td>{renderRecommendation(game.recommendedBet, game.ev)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default NRFIEV;