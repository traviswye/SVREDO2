import React, { useState, useEffect } from 'react';
import '../css/LineupBuilder.css';

const LineupBuilder = ({ sport, draftedPlayers, onResetLineup }) => {
    const getPositionsForSport = (sport) => {
        const sportPositions = {
            NBA: ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL'],
            MLB: ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        };
        return sportPositions[sport] || [];
    };

    const positionMappings = {
        NBA: {
            G: ['PG', 'SG'],
            F: ['SF', 'PF'],
            UTIL: ['PG', 'SG', 'SF', 'PF', 'C']
        },
        MLB: {
            P: ['SP', 'RP']
        }
    };

    // Initialize lineup state with empty slots for the selected sport
    const [lineup, setLineup] = useState(() => {
        const positions = getPositionsForSport(sport);
        return positions.map(pos => ({
            position: pos,
            player: null
        }));
    });

    // State for financial stats
    const [totalSalary, setTotalSalary] = useState(0);
    const [averagePPG, setAveragePPG] = useState(0);

    // State for error messages - simplified to a single array
    const [optimizationErrors, setOptimizationErrors] = useState([]);

    // Reset lineup when sport changes
    useEffect(() => {
        setLineup(getPositionsForSport(sport).map(pos => ({
            position: pos,
            player: null
        })));
    }, [sport]);

    // Process drafted players into the lineup
    useEffect(() => {
        const emptyLineup = getPositionsForSport(sport).map(pos => ({
            position: pos,
            player: null
        }));

        // Clear optimization errors
        setOptimizationErrors([]);

        if (draftedPlayers.length > 0) {
            // Check for optimization errors in the first player
            const firstPlayer = draftedPlayers[0];
            if (firstPlayer && firstPlayer.optimizationErrors) {
                setOptimizationErrors(firstPlayer.optimizationErrors);
            }

            // Process players into lineup
            const updatedLineup = [...emptyLineup];
            draftedPlayers.forEach(player => {
                // Your existing player placement logic...
                const playerPositions = player.position.split('/');
                const optimalPosition = player.assignedPosition || player.optimalPosition || playerPositions[0];
                let placed = false;

                // First try to place in optimal/assigned position
                for (let i = 0; i < updatedLineup.length; i++) {
                    if (!updatedLineup[i].player && updatedLineup[i].position === optimalPosition) {
                        updatedLineup[i].player = player;
                        placed = true;
                        break;
                    }
                }

                // If not placed, try all positions the player can play
                if (!placed) {
                    for (const pos of playerPositions) {
                        for (let i = 0; i < updatedLineup.length; i++) {
                            if (!updatedLineup[i].player && updatedLineup[i].position === pos) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }
                        }
                        if (placed) break;
                    }
                }

                // Special handling for MLB positions
                if (!placed && sport === 'MLB') {
                    // Handle pitcher placement
                    if ((playerPositions.includes('SP') || playerPositions.includes('RP')) &&
                        updatedLineup.some(slot => !slot.player && slot.position === 'P')) {
                        const emptyPSlot = updatedLineup.findIndex(slot => !slot.player && slot.position === 'P');
                        if (emptyPSlot !== -1) {
                            updatedLineup[emptyPSlot].player = player;
                            placed = true;
                        }
                    }

                    // Handle outfielder placement
                    if (!placed && playerPositions.includes('OF')) {
                        const emptyOFSlot = updatedLineup.findIndex(slot => !slot.player && slot.position === 'OF');
                        if (emptyOFSlot !== -1) {
                            updatedLineup[emptyOFSlot].player = player;
                            placed = true;
                        }
                    }
                }

                // Check composite positions
                if (!placed) {
                    for (let i = 0; i < updatedLineup.length; i++) {
                        if (!updatedLineup[i].player) {
                            const lineupPos = updatedLineup[i].position;

                            // Check each special position type
                            if (lineupPos === 'G' &&
                                playerPositions.some(pos => positionMappings[sport]?.G?.includes(pos))) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }

                            if (lineupPos === 'F' &&
                                playerPositions.some(pos => positionMappings[sport]?.F?.includes(pos))) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }

                            if (lineupPos === 'UTIL' &&
                                playerPositions.some(pos => positionMappings[sport]?.UTIL?.includes(pos))) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }
                        }
                    }
                }
            });

            setLineup(updatedLineup);
        } else {
            // If there are no drafted players, set an empty lineup
            setLineup(emptyLineup);
        }
    }, [draftedPlayers, sport, positionMappings]);

    // Calculate financial totals when lineup changes
    useEffect(() => {
        const totals = calculateTotals();
        setTotalSalary(totals.salary);
        setAveragePPG(totals.dkppg);
    }, [lineup]);

    // Calculate salary and points totals
    const calculateTotals = () => {
        const filledPositions = lineup.filter(row => row.player);
        const totalSalary = filledPositions.reduce((sum, row) => sum + (row.player?.salary || 0), 0);
        const totalPPG = filledPositions.reduce((sum, row) => sum + (row.player?.dKppg || 0), 0);

        return {
            salary: totalSalary,
            dkppg: filledPositions.length > 0 ? totalPPG : 0
        };
    };

    // Handle removing a player from a position
    const clearPosition = (positionIndex) => {
        const playerToRemove = lineup[positionIndex].player;

        if (playerToRemove) {
            // Inform parent component about the change
            if (onResetLineup) {
                const updatedDraftedPlayers = draftedPlayers.filter(
                    p => p.playerDkId !== playerToRemove.playerDkId
                );
                onResetLineup(updatedDraftedPlayers);
            }

            // Update local lineup
            const updatedLineup = [...lineup];
            updatedLineup[positionIndex] = {
                ...updatedLineup[positionIndex],
                player: null
            };
            setLineup(updatedLineup);
        }
    };

    // Render error messages
    const renderOptimizationErrors = () => {
        if (optimizationErrors.length > 0) {
            return (
                <div className="optimization-errors">
                    <h3>Optimization Issues:</h3>
                    <ul>
                        {optimizationErrors.map((error, index) => (
                            <li key={index} className="error-message">{error}</li>
                        ))}
                    </ul>
                </div>
            );
        }
        return null;
    };

    // Render salary and stats summary
    const renderSalaryStatus = () => {
        const maxSalary = 50000;
        const remainingSalary = maxSalary - totalSalary;
        const filledPositions = lineup.filter(row => row.player).length;
        const totalPositions = lineup.length;

        return (
            <div className="salary-status">
                <div className="salary-bar">
                    <div
                        className="salary-progress"
                        style={{ width: `${(totalSalary / maxSalary) * 100}%` }}
                    ></div>
                </div>
                <div className="salary-details">
                    <div className="salary-item">
                        <span>Salary Used:</span>
                        <span>${totalSalary.toLocaleString()}</span>
                    </div>
                    <div className="salary-item">
                        <span>Remaining:</span>
                        <span>${remainingSalary.toLocaleString()}</span>
                    </div>
                    <div className="salary-item">
                        <span>Avg PPG:</span>
                        <span>{averagePPG.toFixed(2)}</span>
                    </div>
                    <div className="salary-item">
                        <span>Positions:</span>
                        <span>{filledPositions}/{totalPositions}</span>
                    </div>
                </div>
            </div>
        );
    };

    // Render the lineup table
    const renderLineupTable = () => {
        return (
            <table className="lineup-builder-table">
                <thead>
                    <tr>
                        <th>Position</th>
                        <th>Name</th>
                        <th>Salary</th>
                        <th>Game</th>
                        <th>DK PPG</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {lineup.map((row, index) => (
                        <tr key={`${row.position}-${index}`} className={row.player ? 'filled-position' : 'empty-position'}>
                            <td className="position-cell">{row.position}</td>
                            <td>{row.player ? row.player.fullName : '—'}</td>
                            <td>{row.player ? `$${row.player.salary.toLocaleString()}` : '—'}</td>
                            <td>{row.player ? row.player.game : '—'}</td>
                            <td>{row.player ? row.player.dKppg : '—'}</td>
                            <td>
                                <button
                                    onClick={() => clearPosition(index)}
                                    disabled={!row.player}
                                    className="clear-position-button"
                                >
                                    ✕
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    return (
        <div className="lineup-builder">
            <h2>{sport} Lineup</h2>
            {renderSalaryStatus()}
            {renderOptimizationErrors()}
            <div className="lineup-table-container">
                {renderLineupTable()}
            </div>
            <div className="lineup-actions">
                <button
                    onClick={() => {
                        if (onResetLineup) {
                            onResetLineup([]);
                        }
                        setLineup(getPositionsForSport(sport).map(pos => ({
                            position: pos,
                            player: null
                        })));
                    }}
                    className="reset-lineup-button"
                >
                    Reset Lineup
                </button>
                <button className="export-lineup-button">
                    Export Lineup
                </button>
            </div>
        </div>
    );
};

export default LineupBuilder;