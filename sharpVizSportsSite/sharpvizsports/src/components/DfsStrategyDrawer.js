import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import '../css/DfsStrategyDrawer.css';

const DfsStrategyDrawer = ({ isOpen, onClose, draftGroupId, sport, onSaveStrategy }) => {
    const [contestType, setContestType] = useState('Cash');
    const [stackStrategy, setStackStrategy] = useState('Use suggested stack for this slate');
    const [teams, setTeams] = useState([]);
    const [pitchers, setPitchers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [sortConfig, setSortConfig] = useState({ key: 'expectedRuns', direction: 'desc' });
    const [pitcherSortConfig, setPitcherSortConfig] = useState({ key: 'compositeScore', direction: 'desc' });
    const [selectedTeams, setSelectedTeams] = useState([]);
    const [selectedPitchers, setSelectedPitchers] = useState([]);

    // Cache state
    const dataCache = useRef({
        lastDraftGroupId: null,
        lastSport: null,
        cachedTeams: [],
        cachedPitchers: [],
        lastFetchTime: null
    });

    // Original selections - for reset functionality
    const originalSelections = useRef({
        contestType: null,
        stackStrategy: null,
        selectedTeams: [],
        selectedPitchers: []
    });

    // Strategy options
    const strategyOptions = [
        'Use suggested stack for this slate',
        '3-3',
        '4-2',
        '4-3',
        '4-4',
        '5-2',
        '5-3',
        '5-1'
    ];

    // Save original selections when drawer opens
    useEffect(() => {
        if (isOpen) {
            originalSelections.current = {
                contestType,
                stackStrategy,
                selectedTeams: [...selectedTeams],
                selectedPitchers: [...selectedPitchers]
            };
        }
    }, [isOpen]);

    useEffect(() => {
        if (isOpen && draftGroupId) {
            // Check if we have cached data for this draftGroupId and sport
            const cache = dataCache.current;
            const now = new Date().getTime();
            const cacheValidDuration = 5 * 60 * 1000; // 5 minutes in milliseconds

            const isCacheValid =
                cache.lastDraftGroupId === draftGroupId &&
                cache.lastSport === sport &&
                cache.cachedTeams.length > 0 &&
                cache.cachedPitchers.length > 0 &&
                cache.lastFetchTime &&
                (now - cache.lastFetchTime) < cacheValidDuration;

            if (isCacheValid) {
                console.log("Using cached data for strategy drawer");
                setTeams(cache.cachedTeams);
                setPitchers(cache.cachedPitchers);
            } else {
                console.log("Fetching fresh data for strategy drawer");
                fetchTeamData();
            }
        }
    }, [isOpen, draftGroupId, sport]);

    const fetchTeamData = async () => {
        setLoading(true);
        try {
            // Step 1: Get today's date in YYYY-MM-DD format for API calls
            // const today = '2024-09-11';
            const today = new Date().toISOString().split('T')[0];

            // Step 2: Fetch data from all necessary APIs
            const [
                runExpectancyResponse,
                pitcherRankingsResponse,
                parkFactorsResponse,
                lineupStrengthResponse
            ] = await Promise.all([
                axios.get(`https://localhost:44346/api/Blending/adjustedRunExpectancy?date=${today}`),
                axios.get(`https://localhost:44346/api/Blending/enhancedDailyPitcherRankings?date=${today}`),
                axios.get(`https://localhost:44346/api/ParkFactors`),
                axios.get(`https://localhost:44346/api/Blending/dailyLineupStrength?date=${today}`)
            ]);

            // Step 3: Process and combine the data for teams
            const processedTeams = processApiData(
                runExpectancyResponse.data,
                pitcherRankingsResponse.data,
                parkFactorsResponse.data,
                lineupStrengthResponse.data
            );

            // Step 4: Process pitcher data
            const processedPitchers = processPitcherData(
                pitcherRankingsResponse.data,
                parkFactorsResponse.data
            );

            // Update state
            setTeams(processedTeams);
            setPitchers(processedPitchers);

            // Update cache
            dataCache.current = {
                lastDraftGroupId: draftGroupId,
                lastSport: sport,
                cachedTeams: processedTeams,
                cachedPitchers: processedPitchers,
                lastFetchTime: new Date().getTime()
            };

        } catch (error) {
            console.error('Error fetching team data:', error);
        } finally {
            setLoading(false);
        }
    };

    const processPitcherData = (pitcherRankings, parkFactors) => {
        if (!pitcherRankings || !pitcherRankings.enhancedRankings) {
            return [];
        }

        // Create a map for park factors lookup
        const parkFactorMap = {};
        parkFactors.forEach(park => {
            parkFactorMap[park.team] = park.parkFactorRating / 100; // Convert to decimal
        });

        // Process pitcher data
        return pitcherRankings.enhancedRankings.map(pitcher => {
            const parkFactor = parkFactorMap[pitcher.team] || 1.0;

            // Extract player ID from pitcherId (remove the trailing digits)
            const playerId = pitcher.pitcherId.replace(/\d+$/, '');

            return {
                team: pitcher.team,
                teamAbbrev: convertTeamNameToAbbrev(pitcher.team),
                pitcherId: pitcher.pitcherId,
                playerId: playerId, // Used for DraftKings player ID matching
                isHome: pitcher.isHome,
                hotCold: pitcher.trendAnalysis?.performanceStatus || 'CONSISTENT',
                trendPercent: extractTrendPercentage(pitcher.trendAnalysis?.message || ''),
                compositeScore: pitcher.compositeScore || 0,
                parkFactor: parkFactor
            };
        });
    };

    const processApiData = (runExpectancy, pitcherRankings, parkFactors, lineupStrength) => {
        // Create a map for pitcher data lookup
        const pitcherMap = {};
        if (pitcherRankings && pitcherRankings.enhancedRankings) {
            pitcherRankings.enhancedRankings.forEach(pitcher => {
                pitcherMap[pitcher.team] = {
                    pitcherId: pitcher.pitcherId,
                    trend: pitcher.trendAnalysis?.performanceStatus || 'CONSISTENT',
                    trendPercent: extractTrendPercentage(pitcher.trendAnalysis?.message || ''),
                    compositeScore: pitcher.compositeScore || 0

                };
            });
        }

        // Create a map for park factors lookup
        const parkFactorMap = {};
        parkFactors.forEach(park => {
            parkFactorMap[park.team] = park.parkFactorRating / 100; // Convert to decimal
        });

        // Create a map for lineup strength data
        const lineupStrengthMap = {};
        if (lineupStrength && lineupStrength.games) {
            lineupStrength.games.forEach(game => {
                // Process home team
                const homeTeamData = game.homeTeam?.lineupStats;
                if (homeTeamData) {
                    const seasonOPS = homeTeamData.seasonOPS || 0;
                    const last7OPS = homeTeamData.last7OPS || 0;
                    const percentDifference = seasonOPS > 0 ?
                        ((last7OPS - seasonOPS) / seasonOPS) * 100 : 0;

                    lineupStrengthMap[game.homeTeam.team] = {
                        seasonOPS,
                        last7OPS,
                        trend: percentDifference,
                        trendStatus: percentDifference > 3 ? 'hot' :
                            percentDifference < -3 ? 'cold' : 'neutral'
                    };
                }

                // Process away team
                const awayTeamData = game.awayTeam?.lineupStats;
                if (awayTeamData) {
                    const seasonOPS = awayTeamData.seasonOPS || 0;
                    const last7OPS = awayTeamData.last7OPS || 0;
                    const percentDifference = seasonOPS > 0 ?
                        ((last7OPS - seasonOPS) / seasonOPS) * 100 : 0;

                    lineupStrengthMap[game.awayTeam.team] = {
                        seasonOPS,
                        last7OPS,
                        trend: percentDifference,
                        trendStatus: percentDifference > 3 ? 'hot' :
                            percentDifference < -3 ? 'cold' : 'neutral'
                    };
                }
            });
        }

        // Create a map for opposing pitchers and bullpens
        const matchupMap = {};
        if (runExpectancy && runExpectancy.games) {
            runExpectancy.games.forEach(game => {
                // Map home team's opposing pitcher/bullpen
                matchupMap[game.homeTeam.team] = {
                    opposingTeam: game.awayTeam.team,
                    bullpenRank: rankBullpen(game.awayTeam.bullpenOOPS || 0)
                };

                // Map away team's opposing pitcher/bullpen
                matchupMap[game.awayTeam.team] = {
                    opposingTeam: game.homeTeam.team,
                    bullpenRank: rankBullpen(game.homeTeam.bullpenOOPS || 0)
                };
            });
        }

        // Combine all data into team objects
        const teams = [];
        if (runExpectancy && runExpectancy.games) {
            runExpectancy.games.forEach(game => {
                // Get home team park factor
                const homeParkFactor = parkFactorMap[game.homeTeam.team] || 1.0;

                // Process home team
                const homeTeam = {
                    team: game.homeTeam.team,
                    teamAbbrev: convertTeamNameToAbbrev(game.homeTeam.team),
                    expectedRuns: game.homeTeam.adjustedExpectedRuns || 0,
                    expectedTotal: (game.homeTeam.adjustedExpectedRuns || 0) + (game.awayTeam.adjustedExpectedRuns || 0),
                    lineupTrend: lineupStrengthMap[game.homeTeam.team]?.trend || 0,
                    lineupTrendStatus: lineupStrengthMap[game.homeTeam.team]?.trendStatus || 'neutral',
                    opposingSP: matchupMap[game.homeTeam.team]?.opposingTeam ?
                        pitcherMap[matchupMap[game.homeTeam.team].opposingTeam]?.pitcherId || 'Unknown' : 'Unknown',
                    opposingSPTrend: matchupMap[game.homeTeam.team]?.opposingTeam ?
                        pitcherMap[matchupMap[game.homeTeam.team].opposingTeam]?.trend || 'CONSISTENT' : 'CONSISTENT',
                    opposingSPTrendPercent: matchupMap[game.homeTeam.team]?.opposingTeam ?
                        pitcherMap[matchupMap[game.homeTeam.team].opposingTeam]?.trendPercent || 0 : 0,
                    opposingSPScore: matchupMap[game.homeTeam.team]?.opposingTeam ?
                        pitcherMap[matchupMap[game.homeTeam.team].opposingTeam]?.compositeScore || 0 : 0,
                    opposingBullpenRank: matchupMap[game.homeTeam.team]?.bullpenRank || 'Average',
                    parkFactor: homeParkFactor,
                    isHomeTeam: true
                };

                // Process away team
                const awayTeam = {
                    team: game.awayTeam.team,
                    teamAbbrev: convertTeamNameToAbbrev(game.awayTeam.team),
                    expectedRuns: game.awayTeam.adjustedExpectedRuns || 0,
                    expectedTotal: (game.homeTeam.adjustedExpectedRuns || 0) + (game.awayTeam.adjustedExpectedRuns || 0),
                    lineupTrend: lineupStrengthMap[game.awayTeam.team]?.trend || 0,
                    lineupTrendStatus: lineupStrengthMap[game.awayTeam.team]?.trendStatus || 'neutral',
                    opposingSP: matchupMap[game.awayTeam.team]?.opposingTeam ?
                        pitcherMap[matchupMap[game.awayTeam.team].opposingTeam]?.pitcherId || 'Unknown' : 'Unknown',
                    opposingSPTrend: matchupMap[game.awayTeam.team]?.opposingTeam ?
                        pitcherMap[matchupMap[game.awayTeam.team].opposingTeam]?.trend || 'CONSISTENT' : 'CONSISTENT',
                    opposingSPTrendPercent: matchupMap[game.awayTeam.team]?.opposingTeam ?
                        pitcherMap[matchupMap[game.awayTeam.team].opposingTeam]?.trendPercent || 0 : 0,
                    opposingSPScore: matchupMap[game.awayTeam.team]?.opposingTeam ?
                        pitcherMap[matchupMap[game.awayTeam.team].opposingTeam]?.compositeScore || 0 : 0,
                    opposingBullpenRank: matchupMap[game.awayTeam.team]?.bullpenRank || 'Average',
                    parkFactor: homeParkFactor,
                    isHomeTeam: false
                };

                teams.push(homeTeam);
                teams.push(awayTeam);
            });
        }

        return teams;
    };

    // Helper function to extract trend percentage from pitcher message
    const extractTrendPercentage = (message) => {
        const matches = message.match(/(\d+\.\d+)%/);
        if (matches && matches.length > 1) {
            return parseFloat(matches[1]);
        }
        return 0;
    };

    // Helper function to rank bullpen based on OOPS
    const rankBullpen = (oops) => {
        if (oops <= 0.75) return 'Elite';
        if (oops <= 0.85) return 'Good';
        if (oops <= 0.95) return 'Average';
        if (oops <= 1.05) return 'Below Average';
        return 'Poor';
    };

    // Helper function to convert team names to abbreviations
    const convertTeamNameToAbbrev = (teamName) => {
        const abbrevMap = {
            'Angels': 'LAA',
            'Astros': 'HOU',
            'Athletics': 'OAK',
            'Blue Jays': 'TOR',
            'Braves': 'ATL',
            'Brewers': 'MIL',
            'Cardinals': 'STL',
            'Cubs': 'CHC',
            'Diamondbacks': 'ARI',
            'Dodgers': 'LAD',
            'Giants': 'SF',
            'Guardians': 'CLE',
            'Mariners': 'SEA',
            'Marlins': 'MIA',
            'Mets': 'NYM',
            'Nationals': 'WSH',
            'Orioles': 'BAL',
            'Padres': 'SD',
            'Phillies': 'PHI',
            'Pirates': 'PIT',
            'Rangers': 'TEX',
            'Rays': 'TB',
            'Red Sox': 'BOS',
            'Reds': 'CIN',
            'Rockies': 'COL',
            'Royals': 'KC',
            'Tigers': 'DET',
            'Twins': 'MIN',
            'White Sox': 'CHW',
            'Yankees': 'NYY'
        };

        return abbrevMap[teamName] || teamName;
    };

    const handleSort = (key) => {
        let direction = 'desc';
        if (sortConfig.key === key && sortConfig.direction === 'desc') {
            direction = 'asc';
        }
        setSortConfig({ key, direction });
    };

    const handlePitcherSort = (key) => {
        let direction = 'desc';
        if (pitcherSortConfig.key === key && pitcherSortConfig.direction === 'desc') {
            direction = 'asc';
        }
        setPitcherSortConfig({ key, direction });
    };

    const getSortedTeams = () => {
        const sortableTeams = [...teams];
        if (sortConfig.key) {
            sortableTeams.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) {
                    return sortConfig.direction === 'asc' ? -1 : 1;
                }
                if (a[sortConfig.key] > b[sortConfig.key]) {
                    return sortConfig.direction === 'asc' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableTeams;
    };

    const getSortedPitchers = () => {
        const sortablePitchers = [...pitchers];
        if (pitcherSortConfig.key) {
            sortablePitchers.sort((a, b) => {
                if (a[pitcherSortConfig.key] < b[pitcherSortConfig.key]) {
                    return pitcherSortConfig.direction === 'asc' ? -1 : 1;
                }
                if (a[pitcherSortConfig.key] > b[pitcherSortConfig.key]) {
                    return pitcherSortConfig.direction === 'asc' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortablePitchers;
    };

    const toggleTeamSelection = (teamAbbrev) => {
        setSelectedTeams(prev => {
            if (prev.includes(teamAbbrev)) {
                return prev.filter(team => team !== teamAbbrev);
            } else {
                // If we're adding a team and already have 2 teams selected,
                // remove the first one (for a sliding window of 2 teams max)
                if (prev.length >= 2) {
                    return [...prev.slice(1), teamAbbrev];
                }
                return [...prev, teamAbbrev];
            }
        });
    };

    const togglePitcherSelection = (pitcherId) => {
        setSelectedPitchers(prev => {
            if (prev.includes(pitcherId)) {
                return prev.filter(id => id !== pitcherId);
            } else {
                // If we're adding a pitcher and already have 2 pitchers selected,
                // remove the first one (for a sliding window of 2 pitchers max)
                if (prev.length >= 2) {
                    return [...prev.slice(1), pitcherId];
                }
                return [...prev, pitcherId];
            }
        });
    };

    const handleSave = () => {
        // Create the strategy payload
        const strategyPayload = {
            contestType,
            stackStrategy: contestType === 'Tournament' ? stackStrategy : null,
            selectedTeams: contestType === 'Tournament' ? selectedTeams : [],
            selectedPitchers: selectedPitchers
        };

        // Pass the data back to the parent component
        if (onSaveStrategy) {
            onSaveStrategy(strategyPayload);
        }

        // Close the drawer
        if (onClose) {
            onClose();
        }
    };

    const handleReset = () => {
        // Reset selections to initial values
        setContestType('Cash');
        setStackStrategy('Use suggested stack for this slate');
        setSelectedTeams([]);
        setSelectedPitchers([]);
    };

    // Helper function to render trend indicators
    const renderTrend = (trend, type = 'lineup') => {
        if (type === 'lineup') {
            // Format for lineup trend
            const formattedTrend = trend.toFixed(2);
            if (trend > 3) {
                return <span className="trend-up">{formattedTrend}% Hotter</span>;
            } else if (trend < -3) {
                return <span className="trend-down">{Math.abs(formattedTrend)}% Colder</span>;
            } else {
                return <span className="trend-neutral">Consistent</span>;
            }
        } else {
            // Format for pitcher trend
            if (trend === 'HOT') {
                return <span className="trend-up">↑</span>;
            } else if (trend === 'COLD') {
                return <span className="trend-down">↓</span>;
            } else {
                return <span className="trend-neutral">→</span>;
            }
        }
    };

    // Helper function to render bullpen ranks with color coding
    const renderBullpenRank = (rank) => {
        let className = 'rank-average';

        if (rank === 'Elite') className = 'rank-elite';
        else if (rank === 'Good') className = 'rank-good';
        else if (rank === 'Below Average') className = 'rank-below-average';
        else if (rank === 'Poor') className = 'rank-poor';

        return <span className={className}>{rank}</span>;
    };

    // Helper function to render hot/cold status
    const renderHotCold = (status, trendPercent) => {
        if (status === 'HOT') {
            return <span className="trend-up">{trendPercent.toFixed(1)}% Hotter</span>;
        } else if (status === 'COLD') {
            return <span className="trend-down">{trendPercent.toFixed(1)}% Colder</span>;
        } else {
            return <span className="trend-neutral">Consistent</span>;
        }
    };

    if (!isOpen) return null;

    return (
        <div className="dfs-strategy-drawer">
            <div className="drawer-content">
                <div className="drawer-header">
                    <h2>DFS Strategy Settings</h2>
                    <button className="close-button" onClick={onClose}>×</button>
                </div>

                <div className="strategy-settings">
                    <div className="setting-group">
                        <label>Contest Type:</label>
                        <select
                            value={contestType}
                            onChange={(e) => setContestType(e.target.value)}
                        >
                            <option value="Cash">Cash</option>
                            <option value="Tournament">Tournament</option>
                        </select>
                    </div>

                    {contestType === 'Tournament' && (
                        <div className="setting-group">
                            <label>Stack Strategy:</label>
                            <select
                                value={stackStrategy}
                                onChange={(e) => setStackStrategy(e.target.value)}
                            >
                                {strategyOptions.map(option => (
                                    <option key={option} value={option}>{option}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                {contestType === 'Tournament' && (
                    <div className="team-selection">
                        <h3>Select Teams to Stack</h3>
                        {loading ? (
                            <div className="loading">Loading team data...</div>
                        ) : (
                            <div className="team-table-container">
                                <table className="team-table">
                                    <thead>
                                        <tr>
                                            <th onClick={() => handleSort('team')}>Team {sortConfig.key === 'team' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th onClick={() => handleSort('expectedRuns')}>Expected Runs {sortConfig.key === 'expectedRuns' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th onClick={() => handleSort('expectedTotal')}>Expected Total {sortConfig.key === 'expectedTotal' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th onClick={() => handleSort('lineupTrend')}>Lineup Trend {sortConfig.key === 'lineupTrend' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th onClick={() => handleSort('opposingSP')}>Opposing SP {sortConfig.key === 'opposingSP' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th onClick={() => handleSort('opposingSPScore')}>Opposing SP Score {sortConfig.key === 'opposingSPScore' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th onClick={() => handleSort('opposingSPTrend')}>Opposing SP Trend {sortConfig.key === 'opposingSPTrend' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th onClick={() => handleSort('opposingBullpenRank')}>Opposing Bullpen {sortConfig.key === 'opposingBullpenRank' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th onClick={() => handleSort('parkFactor')}>Park Factor {sortConfig.key === 'parkFactor' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                            <th>Select</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {getSortedTeams().map((team, index) => (
                                            <tr key={index} className={selectedTeams.includes(team.teamAbbrev) ? 'selected-team' : ''}>
                                                <td>{team.team}</td>
                                                <td>{team.expectedRuns.toFixed(1)}</td>
                                                <td>{team.expectedTotal.toFixed(1)}</td>
                                                <td>{renderTrend(team.lineupTrend, 'lineup')}</td>
                                                <td>{team.opposingSP}</td>
                                                <td className={team.opposingSPScore > 2 ? 'score-high' : team.opposingSPScore > 1 ? 'score-medium' : 'score-low'}>
                                                    {team.opposingSPScore.toFixed(2)}
                                                </td>
                                                <td>
                                                    {team.opposingSPTrend === 'HOT' ? (
                                                        <span className="trend-up">{team.opposingSPTrendPercent.toFixed(1)}% Hotter</span>
                                                    ) : team.opposingSPTrend === 'COLD' ? (
                                                        <span className="trend-down">{team.opposingSPTrendPercent.toFixed(1)}% Colder</span>
                                                    ) : (
                                                        <span className="trend-neutral">Consistent</span>
                                                    )}
                                                </td>
                                                <td>{renderBullpenRank(team.opposingBullpenRank)}</td>
                                                <td>{team.parkFactor.toFixed(2)}</td>
                                                <td>
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedTeams.includes(team.teamAbbrev)}
                                                        onChange={() => toggleTeamSelection(team.teamAbbrev)}
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}

                {/* Starting Pitchers Table */}
                <div className="pitcher-selection">
                    <h3>Starting Pitchers</h3>
                    {loading ? (
                        <div className="loading">Loading pitcher data...</div>
                    ) : (
                        <div className="pitcher-table-container">
                            <table className="pitcher-table">
                                <thead>
                                    <tr>
                                        <th onClick={() => handlePitcherSort('team')}>Team {pitcherSortConfig.key === 'team' && (pitcherSortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                        <th onClick={() => handlePitcherSort('pitcherId')}>Pitcher {pitcherSortConfig.key === 'pitcherId' && (pitcherSortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                        <th onClick={() => handlePitcherSort('isHome')}>Home/Away {pitcherSortConfig.key === 'isHome' && (pitcherSortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                        <th onClick={() => handlePitcherSort('hotCold')}>Hot/Cold {pitcherSortConfig.key === 'hotCold' && (pitcherSortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                        <th onClick={() => handlePitcherSort('compositeScore')}>Score {pitcherSortConfig.key === 'compositeScore' && (pitcherSortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                        <th onClick={() => handlePitcherSort('parkFactor')}>Park Factor {pitcherSortConfig.key === 'parkFactor' && (pitcherSortConfig.direction === 'asc' ? '↑' : '↓')}</th>
                                        <th>Select</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {getSortedPitchers().map((pitcher, index) => (
                                        <tr key={index} className={selectedPitchers.includes(pitcher.pitcherId) ? 'selected-pitcher' : ''}>
                                            <td>{pitcher.team}</td>
                                            <td>{pitcher.pitcherId}</td>
                                            <td>{pitcher.isHome ? 'Home' : 'Away'}</td>
                                            <td>{renderHotCold(pitcher.hotCold, pitcher.trendPercent)}</td>
                                            <td className={pitcher.compositeScore > 2 ? 'score-high' : pitcher.compositeScore > 1 ? 'score-medium' : 'score-low'}>
                                                {pitcher.compositeScore.toFixed(2)}
                                            </td>
                                            <td>{pitcher.parkFactor.toFixed(2)}</td>
                                            <td>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedPitchers.includes(pitcher.pitcherId)}
                                                    onChange={() => togglePitcherSelection(pitcher.pitcherId)}
                                                />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                <div className="drawer-actions">
                    <button className="reset-button" onClick={handleReset}>
                        Reset
                    </button>
                    <button className="cancel-button" onClick={onClose}>
                        Cancel
                    </button>
                    <button className="save-button" onClick={handleSave}>
                        Save Strategy
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DfsStrategyDrawer;