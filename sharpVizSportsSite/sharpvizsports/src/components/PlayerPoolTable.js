import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../css/PlayerPoolTable.css';

const PlayerPoolTable = ({
    draftGroupId,
    sport,
    onAddToWatchList,
    onAddToDraft,
    onOptimizationResults,
    prepareOptimizationPayload
}) => {
    const [players, setPlayers] = useState([]);
    const [activeTab, setActiveTab] = useState('ALL');
    const [positions, setPositions] = useState(['ALL']);
    const [watchList, setWatchList] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [notification, setNotification] = useState(null);

    // Predefined position tabs for different sports
    const sportPositionTabs = {
        NBA: ['ALL', 'PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL'],
        MLB: ['ALL', 'SP', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF']
    };

    const sportOptimizationConfigs = {
        NBA: {
            positions: ["C", "PF", "SF", "SG", "PG", "G", "F", "UTIL"],
            salaryCap: 50000
        },
        MLB: {
            positions: ["P", "P", "C", "1B", "2B", "3B", "SS", "OF", "OF", "OF"],
            salaryCap: 50000
        }
    };

    // Utility function to map positions
    const getPositionCategories = (sport, playerPositions) => {
        const positionMappings = {
            NBA: {
                positionGroups: {
                    PG: ['PG', 'G'],
                    SG: ['SG', 'G'],
                    SF: ['SF', 'F'],
                    PF: ['PF', 'F'],
                    C: ['C'],
                    G: ['PG', 'SG'],
                    F: ['SF', 'PF'],
                    UTIL: true
                }
            },
            MLB: {
                positionGroups: {
                    SP: ['SP', 'P'],
                    P: ['P'],
                    C: ['C'],
                    '1B': ['1B'],
                    '2B': ['2B'],
                    '3B': ['3B'],
                    SS: ['SS'],
                    OF: ['OF'],
                    ALL: true
                }
            }
        };

        const mapping = positionMappings[sport]?.positionGroups;
        if (!mapping) return [];

        // Split player positions if they have multiple (e.g., 'PG/SF')
        const playerPositionArray = playerPositions.split('/');

        // Find all position groups this player belongs to
        const playerPositionGroups = Object.keys(mapping).filter(group => {
            // UTIL/ALL is always included
            if (mapping[group] === true) return true;

            // Check if any of the player's positions match the group's allowed positions
            return playerPositionArray.some(pos =>
                mapping[group] === true || mapping[group].includes(pos)
            );
        });

        return playerPositionGroups;
    };

    useEffect(() => {
        const fetchPlayers = async () => {
            if (!draftGroupId) return;
            setLoading(true);

            try {
                const response = await axios.get(`https://localhost:44346/api/DKPlayerPools/draftgroup/${draftGroupId}`);

                // Enhance players with multi-position categorization
                const enhancedPlayers = response.data.map(player => ({
                    ...player,
                    positionGroups: getPositionCategories(sport, player.position)
                }));

                setPlayers(enhancedPlayers);

                // Filter the watchList to only include players from the current slate
                if (watchList.length > 0) {
                    const currentPlayerIds = new Set(enhancedPlayers.map(player => player.playerDkId));
                    const originalWatchListLength = watchList.length;
                    const filteredWatchList = watchList.filter(player => currentPlayerIds.has(player.playerDkId));

                    // Update watchList if players were filtered out
                    if (filteredWatchList.length !== originalWatchListLength) {
                        const removedCount = originalWatchListLength - filteredWatchList.length;
                        setWatchList(filteredWatchList);
                        setNotification(`${removedCount} player(s) were removed from your watch list because they are not available in the current slate.`);

                        // Clear notification after 5 seconds
                        setTimeout(() => {
                            setNotification(null);
                        }, 5000);
                    }
                }

                // Use predefined positions for the specific sport
                const finalPositions = sportPositionTabs[sport] || ['ALL'];
                setPositions(finalPositions);
            } catch (error) {
                console.error('Error fetching player pool:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchPlayers();
    }, [draftGroupId, sport]);

    const addToWatchList = (player) => {
        // Prevent duplicates based on playerDkId
        const isDuplicate = watchList.some(p => p.playerDkId === player.playerDkId);

        if (!isDuplicate) {
            setWatchList(prevWatchList => [...prevWatchList, player]);
            // Notify parent component if provided
            if (onAddToWatchList) {
                onAddToWatchList(player);
            }
        }
    };

    const removeFromWatchList = (playerDkId) => {
        setWatchList(prevWatchList =>
            prevWatchList.filter(p => p.playerDkId !== playerDkId)
        );
    };

    const toggleWatchList = (player) => {
        const isDuplicate = watchList.some(p => p.playerDkId === player.playerDkId);

        if (isDuplicate) {
            // Remove from watchlist
            removeFromWatchList(player.playerDkId);
        } else {
            // Add to watchlist
            addToWatchList(player);
        }
    };

    const optimizeWatchList = async () => {
        // Create a set of player IDs from current player pool for quick lookup
        const availablePlayerIds = new Set(players.map(player => player.playerDkId));

        // Filter watch list to only include available players for optimization
        const availablePlayers = watchList.filter(player => availablePlayerIds.has(player.playerDkId));

        if (availablePlayers.length === 0) {
            alert('No players in your watch list are available in the current slate.');
            return;
        }

        setLoading(true);
        try {
            // Get the player IDs for the optimization
            const playerIds = availablePlayers.map(player => player.playerDkId);

            // Use the provided function to prepare the payload if available
            let optimizationPayload;

            if (prepareOptimizationPayload) {
                optimizationPayload = prepareOptimizationPayload(playerIds, draftGroupId);
            } else {
                // Fallback to default payload if function not provided
                const sportConfig = sportOptimizationConfigs[sport];

                if (!sportConfig) {
                    console.error(`No optimization config for sport: ${sport}`);
                    return;
                }

                optimizationPayload = {
                    draftGroupId: draftGroupId,
                    positions: sportConfig.positions,
                    salaryCap: sportConfig.salaryCap,
                    optimizeForDkppg: true,
                    oppRankLimit: 0,
                    userWatchlist: playerIds,
                    mustStartPlayers: []
                };
            }

            // Make the optimization call
            const response = await axios.post(
                'https://localhost:44346/api/DfsOptimization/optimize',
                optimizationPayload,
                {
                    headers: {
                        'accept': 'text/plain',
                        'Content-Type': 'application/json'
                    }
                }
            );

            // Handle the optimization response
            console.log('Optimization Results:', response.data);

            // Pass the optimization results to the parent component
            if (onOptimizationResults) {
                onOptimizationResults(response.data);
            }
        } catch (error) {
            console.error('Optimization error:', error);
            alert('Error optimizing lineup. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e) => {
        setSearchQuery(e.target.value);
    };

    const filterPlayers = (players, position = 'ALL', query = '') => {
        return players.filter(player => {
            const positionMatch = position === 'ALL' || player.positionGroups.includes(position);
            const searchMatch = query === '' ||
                player.fullName.toLowerCase().includes(query.toLowerCase()) ||
                player.position.toLowerCase().includes(query.toLowerCase()) ||
                player.game.toLowerCase().includes(query.toLowerCase());

            return positionMatch && searchMatch;
        });
    };

    const renderPlayerTable = (filterPosition = 'ALL') => {
        const filteredPlayers = filterPlayers(players, filterPosition, searchQuery);

        if (loading) {
            return <div className="loading-indicator">Loading players...</div>;
        }

        if (filteredPlayers.length === 0) {
            return <div className="no-players-message">No players found matching your criteria.</div>;
        }

        return (
            <table className="player-pool-table">
                <thead>
                    <tr>
                        <th>Full Name</th>
                        <th>Position</th>
                        <th>Salary</th>
                        <th>Game</th>
                        <th>DK PPG</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredPlayers.map(player => (
                        <tr key={player.id}>
                            <td>{player.fullName}</td>
                            <td>{player.position}</td>
                            <td>${player.salary.toLocaleString()}</td>
                            <td>{player.game}</td>
                            <td>{player.dKppg}</td>
                            <td>
                                <div className="action-buttons">
                                    <button
                                        onClick={() => toggleWatchList(player)}
                                        className={`target-button ${watchList.some(p => p.playerDkId === player.playerDkId) ? 'targeted' : ''}`}
                                        title={watchList.some(p => p.playerDkId === player.playerDkId) ? 'Remove from Watch List' : 'Add to Watch List'}
                                    >
                                        {watchList.some(p => p.playerDkId === player.playerDkId) ? 'Targeted' : 'Target'}
                                    </button>
                                    <button
                                        onClick={() => onAddToDraft(player)}
                                        className="draft-button"
                                        title="Draft to Lineup"
                                    >
                                        Draft
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    const renderWatchListTable = () => {
        // Create a set of player IDs from current player pool for quick lookup
        const availablePlayerIds = new Set(players.map(player => player.playerDkId));

        // Separate available and unavailable players
        const availablePlayers = watchList.filter(player => availablePlayerIds.has(player.playerDkId));
        const unavailablePlayers = watchList.filter(player => !availablePlayerIds.has(player.playerDkId));

        if (watchList.length === 0) {
            return <div className="no-players-message">Your watch list is empty. Target players to add them here.</div>;
        }

        return (
            <div>
                <table className="watch-list-table">
                    <thead>
                        <tr>
                            <th>Full Name</th>
                            <th>Position</th>
                            <th>Salary</th>
                            <th>Game</th>
                            <th>DK PPG</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {availablePlayers.map(player => (
                            <tr key={player.playerDkId}>
                                <td>{player.fullName}</td>
                                <td>{player.position}</td>
                                <td>${player.salary.toLocaleString()}</td>
                                <td>{player.game}</td>
                                <td>{player.dKppg}</td>
                                <td>
                                    <button
                                        onClick={() => removeFromWatchList(player.playerDkId)}
                                        className="remove-button"
                                    >
                                        Remove
                                    </button>
                                </td>
                            </tr>
                        ))}

                        {/* Display unavailable players with different styling */}
                        {unavailablePlayers.length > 0 && (
                            <>
                                <tr className="unavailable-header">
                                    <td colSpan="6">Players Not Available in Current Slate</td>
                                </tr>
                                {unavailablePlayers.map(player => (
                                    <tr key={player.playerDkId} className="unavailable-player">
                                        <td>{player.fullName}</td>
                                        <td>{player.position}</td>
                                        <td>${player.salary.toLocaleString()}</td>
                                        <td>{player.game}</td>
                                        <td>{player.dKppg}</td>
                                        <td>
                                            <button
                                                onClick={() => removeFromWatchList(player.playerDkId)}
                                                className="remove-button"
                                            >
                                                Remove
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </>
                        )}
                    </tbody>
                </table>
                {availablePlayers.length > 0 && (
                    <div className="optimize-button-container">
                        <button
                            onClick={optimizeWatchList}
                            className="optimize-button"
                            disabled={loading}
                        >
                            {loading ? 'Optimizing...' : 'Optimize Lineup'}
                        </button>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="player-pool-wrapper">
            <h2>{sport} Player Pool</h2>
            {notification && (
                <div className="notification">
                    <span>{notification}</span>
                    <button onClick={() => setNotification(null)}>×</button>
                </div>
            )}
            <div className="player-pool-controls">
                <div className="search-box">
                    <input
                        type="text"
                        placeholder="Search players, positions, or teams..."
                        value={searchQuery}
                        onChange={handleSearch}
                    />
                    {searchQuery && (
                        <button
                            className="clear-search"
                            onClick={() => setSearchQuery('')}
                        >
                            ×
                        </button>
                    )}
                </div>
            </div>

            <div className="tabs">
                {positions.map(pos => (
                    <button
                        key={pos}
                        onClick={() => setActiveTab(pos)}
                        className={activeTab === pos ? 'active' : ''}
                    >
                        {pos}
                    </button>
                ))}
                <button
                    onClick={() => setActiveTab('watchList')}
                    className={activeTab === 'watchList' ? 'active' : ''}
                >
                    Watch List {watchList.length > 0 && `(${watchList.length})`}
                </button>
            </div>

            <div className="tab-content">
                {activeTab === 'watchList'
                    ? renderWatchListTable()
                    : renderPlayerTable(activeTab)
                }
            </div>
        </div>
    );
};

export default PlayerPoolTable;