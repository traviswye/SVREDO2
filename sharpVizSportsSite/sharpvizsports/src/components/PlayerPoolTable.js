import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../css/PlayerPoolTable.css';

const PlayerPoolTable = ({
    draftGroupId,
    sport,
    onAddToWatchList,
    onAddToDraft,
    onOptimizationResults,
    prepareOptimizationPayload,
    onPlayersLoaded,
    draftedPlayers
}) => {
    const [players, setPlayers] = useState([]);
    const [activeTab, setActiveTab] = useState('ALL');
    const [positions, setPositions] = useState(['ALL']);
    const [watchList, setWatchList] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [notification, setNotification] = useState(null);
    const [draftedPlayerIds, setDraftedPlayerIds] = useState(new Set());
    const [ignorePlayerStatus, setIgnorePlayerStatus] = useState(false);

    // Initialize with salary as default sort column (descending)
    const [sortConfig, setSortConfig] = useState({
        key: 'salary',
        direction: 'desc'
    });

    // Predefined position tabs for different sports
    const sportPositionTabs = {
        NBA: ['ALL', 'PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL'],
        MLB: ['ALL', 'SP', 'RP', 'C', '1B', '2B', '3B', 'SS', 'OF']
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

    // Define which columns should default to descending order when first clicked
    const descendingByDefault = ['salary', 'dKppg'];

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
                    SP: ['SP'],
                    RP: ['RP'],
                    P: ['SP', 'RP'],
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

        // Split player positions if they have multiple (e.g., 'SP/RP')
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
        // This prop would need to be passed from the parent component
        if (draftedPlayers) {
            const draftedIds = new Set(draftedPlayers.map(player => player.playerDkId));
            setDraftedPlayerIds(draftedIds);
        }
    }, [draftedPlayers]);

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
                if (onPlayersLoaded) {
                    onPlayersLoaded(enhancedPlayers);
                }

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

    const handleAddToDraft = (player) => {
        // Only draft if not already drafted
        if (!draftedPlayerIds.has(player.playerDkId)) {
            // Update the local tracking set
            setDraftedPlayerIds(prev => new Set([...prev, player.playerDkId]));

            // Notify parent component
            if (onAddToDraft) {
                onAddToDraft(player);
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
                // Get base payload from parent component
                optimizationPayload = prepareOptimizationPayload(playerIds, draftGroupId);

                // IMPORTANT: Override the ignorePlayerStatus with our local state value
                optimizationPayload.ignorePlayerStatus = ignorePlayerStatus;
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
                    mustStartPlayers: [],
                    ignorePlayerStatus: ignorePlayerStatus // Make sure to include the state value here
                };
            }

            console.log('Optimization payload:', optimizationPayload);

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

            // Extract any error messages
            let optimizationErrors = [];

            // Check for error message
            if (response.data.message && response.data.message.includes("issues")) {
                optimizationErrors.push(response.data.message);
            }

            // Check for error details
            if (response.data.errorDetails && response.data.errorDetails.length > 0) {
                optimizationErrors.push(...response.data.errorDetails);
            }

            // If we have players and errors, attach errors to the first player
            if (response.data.players && response.data.players.length > 0 && optimizationErrors.length > 0) {
                response.data.players[0].optimizationErrors = optimizationErrors;
            }

            // Pass the modified optimization results
            if (onOptimizationResults) {
                onOptimizationResults(response.data);
            }

            // // Display notification if needed on playerpooltable component
            // if (optimizationErrors.length > 0) {
            //     setNotification(optimizationErrors.join("; "));
            // }
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

    // Sort function for table - MODIFIED to default to DESC for numeric columns
    const requestSort = (key) => {
        let direction;

        if (sortConfig.key === key) {
            // If already sorting by this column, toggle direction
            direction = sortConfig.direction === 'asc' ? 'desc' : 'asc';
        } else {
            // For new column, check if it should default to descending
            direction = descendingByDefault.includes(key) ? 'desc' : 'asc';
        }

        setSortConfig({ key, direction });
    };

    // Function to sort the data with secondary sorting by DKPPG
    const sortedData = (data) => {
        if (!data || data.length === 0) return [];

        return [...data].sort((a, b) => {
            // Primary sort by selected column
            if (sortConfig.key) {
                // Handle different data types appropriately
                if (sortConfig.key === 'salary' || sortConfig.key === 'dKppg') {
                    // Numeric comparison
                    if (a[sortConfig.key] < b[sortConfig.key]) {
                        return sortConfig.direction === 'asc' ? -1 : 1;
                    }
                    if (a[sortConfig.key] > b[sortConfig.key]) {
                        return sortConfig.direction === 'asc' ? 1 : -1;
                    }

                    // If primary sort values are equal, use DKPPG as secondary sort (always descending)
                    if (sortConfig.key !== 'dKppg') {
                        // FIXED: Sort by DKPPG in descending order for secondary sort
                        return (b.dKppg || 0) - (a.dKppg || 0);
                    }

                    return 0;
                } else {
                    // String comparison
                    const aValue = a[sortConfig.key]?.toString().toLowerCase() || '';
                    const bValue = b[sortConfig.key]?.toString().toLowerCase() || '';

                    if (aValue < bValue) {
                        return sortConfig.direction === 'asc' ? -1 : 1;
                    }
                    if (aValue > bValue) {
                        return sortConfig.direction === 'asc' ? 1 : -1;
                    }

                    // FIXED: Sort by DKPPG in descending order for secondary sort
                    return (b.dKppg || 0) - (a.dKppg || 0);
                }
            }
            return 0;
        });
    };

    // Get the sort direction indicator
    const getSortDirectionIndicator = (key) => {
        if (sortConfig.key !== key) return '';
        return sortConfig.direction === 'asc' ? ' ↑' : ' ↓';
    };

    // Helper function to render player status
    const renderStatus = (status) => {
        if (!status || status === 'None') return null;

        // Only show status when it's OUT or GTD
        if (status === 'OUT') {
            return <span className="status-out">{status}</span>;
        } else if (status === 'GTD') {
            return <span className="status-gtd">{status}</span>;
        } else if (status === 'IL') {
            return <span className="status-il">{status}</span>;
        } else if (status === 'DTD') {
            return <span className="status-dtd">{status}</span>;
        }

        return null;
    };

    const filterPlayers = (players, position = 'ALL', query = '') => {
        return players.filter(player => {
            const positionMatch = position === 'ALL' || player.positionGroups.includes(position);
            const searchMatch = query === '' ||
                player.fullName.toLowerCase().includes(query.toLowerCase()) ||
                player.position.toLowerCase().includes(query.toLowerCase()) ||
                (player.status && player.status.toLowerCase().includes(query.toLowerCase())) ||
                player.game.toLowerCase().includes(query.toLowerCase());

            return positionMatch && searchMatch;
        });
    };

    const renderPlayerTable = (filterPosition = 'ALL') => {
        const filteredPlayers = filterPlayers(players, filterPosition, searchQuery);
        const sortedPlayers = sortedData(filteredPlayers);

        if (loading) {
            return <div className="loading-indicator">Loading players...</div>;
        }

        if (sortedPlayers.length === 0) {
            return <div className="no-players-message">No players found matching your criteria.</div>;
        }

        return (
            <table className="player-pool-table">
                <thead>
                    <tr>
                        <th onClick={() => requestSort('fullName')}>
                            Full Name{getSortDirectionIndicator('fullName')}
                        </th>
                        <th onClick={() => requestSort('position')}>
                            Position{getSortDirectionIndicator('position')}
                        </th>
                        <th onClick={() => requestSort('status')}>
                            Status{getSortDirectionIndicator('status')}
                        </th>
                        <th onClick={() => requestSort('salary')}>
                            Salary{getSortDirectionIndicator('salary')}
                        </th>
                        <th onClick={() => requestSort('game')}>
                            Game{getSortDirectionIndicator('game')}
                        </th>
                        <th onClick={() => requestSort('dKppg')}>
                            DK PPG{getSortDirectionIndicator('dKppg')}
                        </th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {sortedPlayers.map(player => (
                        <tr key={player.id} className={player.status === 'OUT' ? 'player-out' : ''}>
                            <td>{player.fullName}</td>
                            <td>{player.position}</td>
                            <td>{renderStatus(player.status)}</td>
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
                                        onClick={() => handleAddToDraft(player)}
                                        className="draft-button"
                                        title="Draft to Lineup"
                                        disabled={draftedPlayerIds.has(player.playerDkId) || player.status === 'OUT'}
                                    >
                                        {draftedPlayerIds.has(player.playerDkId) ? 'Drafted' : 'Draft'}
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

        // Sort the watchlist using the same sorting logic
        const sortedAvailablePlayers = sortedData(availablePlayers);
        const sortedUnavailablePlayers = sortedData(unavailablePlayers);

        if (watchList.length === 0) {
            return <div className="no-players-message">Your watch list is empty. Target players to add them here.</div>;
        }

        return (
            <div>
                <table className="watch-list-table">
                    <thead>
                        <tr>
                            <th onClick={() => requestSort('fullName')}>
                                Full Name{getSortDirectionIndicator('fullName')}
                            </th>
                            <th onClick={() => requestSort('position')}>
                                Position{getSortDirectionIndicator('position')}
                            </th>
                            <th onClick={() => requestSort('status')}>
                                Status{getSortDirectionIndicator('status')}
                            </th>
                            <th onClick={() => requestSort('salary')}>
                                Salary{getSortDirectionIndicator('salary')}
                            </th>
                            <th onClick={() => requestSort('game')}>
                                Game{getSortDirectionIndicator('game')}
                            </th>
                            <th onClick={() => requestSort('dKppg')}>
                                DK PPG{getSortDirectionIndicator('dKppg')}
                            </th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedAvailablePlayers.map(player => (
                            <tr key={player.playerDkId} className={player.status === 'OUT' ? 'player-out' : ''}>
                                <td>{player.fullName}</td>
                                <td>{player.position}</td>
                                <td>{renderStatus(player.status)}</td>
                                <td>${player.salary.toLocaleString()}</td>
                                <td>{player.game}</td>
                                <td>{player.dKppg}</td>
                                <td>
                                    <div className="action-buttons">
                                        <button
                                            onClick={() => removeFromWatchList(player.playerDkId)}
                                            className="remove-button"
                                        >
                                            Remove
                                        </button>
                                        {/* Add Draft button to watchlist */}
                                        <button
                                            onClick={() => handleAddToDraft(player)}
                                            className="draft-button"
                                            disabled={draftedPlayerIds.has(player.playerDkId) || player.status === 'OUT'}
                                        >
                                            {draftedPlayerIds.has(player.playerDkId) ? 'Drafted' : 'Draft'}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}

                        {/* Display unavailable players with different styling */}
                        {sortedUnavailablePlayers.length > 0 && (
                            <>
                                <tr className="unavailable-header">
                                    <td colSpan="7">Players Not Available in Current Slate</td>
                                </tr>
                                {sortedUnavailablePlayers.map(player => (
                                    <tr key={player.playerDkId} className="unavailable-player">
                                        <td>{player.fullName}</td>
                                        <td>{player.position}</td>
                                        <td>{renderStatus(player.status)}</td>
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
                {sortedAvailablePlayers.length > 0 && (
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
            {/* this is for if we want errors displayed in playerpooltable component */}
            {/* {notification && (
                <div className="notification">
                    <span>{notification}</span>
                    <button onClick={() => setNotification(null)}>×</button>
                </div>
            )} */}
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

                {/* Only show the checkbox when in the watchList tab */}
                {activeTab === 'watchList' && (
                    <div className="options-container">
                        <label className="status-option">
                            <input
                                type="checkbox"
                                checked={ignorePlayerStatus}
                                onChange={() => setIgnorePlayerStatus(!ignorePlayerStatus)}
                            />
                            Include players with "OUT" status in optimization
                        </label>
                    </div>
                )}
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