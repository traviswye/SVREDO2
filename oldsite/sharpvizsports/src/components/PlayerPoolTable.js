import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PlayerPoolTable = ({
    draftGroupId,
    sport,
    onAddToWatchList,
    onAddToDraft,
    onOptimizationResults // New prop
}) => {
    const [players, setPlayers] = useState([]);
    const [activeTab, setActiveTab] = useState('ALL');
    const [positions, setPositions] = useState(['ALL']);
    const [watchList, setWatchList] = useState([]);

    // Predefined position tabs and optimization configs for different sports
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

            try {
                const response = await axios.get(`https://localhost:44346/api/DKPlayerPools/draftgroup/${draftGroupId}`);

                // Enhance players with multi-position categorization
                const enhancedPlayers = response.data.map(player => ({
                    ...player,
                    positionGroups: getPositionCategories(sport, player.position)
                }));

                setPlayers(enhancedPlayers);

                // Use predefined positions for the specific sport
                const finalPositions = ['ALL', ...sportPositionTabs[sport]];
                setPositions(finalPositions);
            } catch (error) {
                console.error('Error fetching player pool:', error);
            }
        };

        fetchPlayers();
    }, [draftGroupId, sport]);

    const addToWatchList = (player) => {
        // Prevent duplicates based on playerDkId
        const isDuplicate = watchList.some(p => p.playerDkId === player.playerDkId);

        if (!isDuplicate) {
            setWatchList(prevWatchList => [...prevWatchList, player]);
        }
    };

    const removeFromWatchList = (playerDkId) => {
        setWatchList(prevWatchList =>
            prevWatchList.filter(p => p.playerDkId !== playerDkId)
        );
    };

    const optimizeWatchList = async () => {
        try {
            // Get the configuration for the current sport
            const sportConfig = sportOptimizationConfigs[sport];

            if (!sportConfig) {
                console.error(`No optimization config for sport: ${sport}`);
                return;
            }

            // Prepare the optimization payload
            const optimizationPayload = {
                draftGroupId: draftGroupId,
                positions: sportConfig.positions,
                salaryCap: sportConfig.salaryCap,
                optimizeForDkppg: true,
                oppRankLimit: 0,
                userWatchlist: watchList.map(player => player.playerDkId),
                mustStartPlayers: []
            };

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
        }
    };
    const renderPlayerTable = (filterPosition = 'ALL') => {
        const filteredPlayers = filterPosition === 'ALL'
            ? players
            : players.filter(player => player.positionGroups.includes(filterPosition));

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
                            <td>${player.salary}</td>
                            <td>{player.game}</td>
                            <td>{player.dKppg}</td>
                            <td>
                                <div className="action-buttons">
                                    <button
                                        onClick={() => addToWatchList(player)}
                                        title="Add to Watch List"
                                    >
                                        Target
                                    </button>
                                    <button
                                        onClick={() => onAddToDraft(player)}
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


    const renderWatchListTable = () => (
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
                    {watchList.map(player => (
                        <tr key={player.playerDkId}>
                            <td>{player.fullName}</td>
                            <td>{player.position}</td>
                            <td>${player.salary}</td>
                            <td>{player.game}</td>
                            <td>{player.dKppg}</td>
                            <td>
                                <button onClick={() => removeFromWatchList(player.playerDkId)}>
                                    Remove
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            {watchList.length > 0 && (
                <div className="optimize-button-container">
                    <button
                        onClick={optimizeWatchList}
                        className="optimize-button"
                    >
                        Optimize Lineup
                    </button>
                </div>
            )}
        </div>
    );

    return (
        <div className="player-pool-container">
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
                    Watch List
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