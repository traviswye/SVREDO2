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
            // Primary positions that can fill G slot
            G: ['PG', 'SG'],
            // Primary positions that can fill F slot
            F: ['SF', 'PF'],
            // All positions that can fill UTIL
            UTIL: ['PG', 'SG', 'SF', 'PF', 'C']
        },
        MLB: {
            // MLB specific mappings if needed
        }
    };

    const [lineup, setLineup] = useState(() => {
        const positions = getPositionsForSport(sport);
        return positions.map(pos => ({
            position: pos,
            player: null
        }));
    });

    const [totalSalary, setTotalSalary] = useState(0);
    const [averagePPG, setAveragePPG] = useState(0);

    useEffect(() => {
        // Reset lineup when sport changes
        setLineup(getPositionsForSport(sport).map(pos => ({
            position: pos,
            player: null
        })));
    }, [sport]);

    useEffect(() => {
        // Reset lineup when sport changes
        setLineup(getPositionsForSport(sport).map(pos => ({
            position: pos,
            player: null
        })));
    }, [sport]);

    useEffect(() => {
        const emptyLineup = getPositionsForSport(sport).map(pos => ({
            position: pos,
            player: null
        }));

        if (draftedPlayers.length > 0) {
            const updatedLineup = [...emptyLineup];
            draftedPlayers.forEach(player => {
                // Use assignedPosition from optimization response
                const optimalPosition = player.assignedPosition || player.optimalPosition || player.position.split('/')[0];
                let placed = false;

                // First try to place in optimal position
                for (let i = 0; i < updatedLineup.length; i++) {
                    if (!updatedLineup[i].player && updatedLineup[i].position === optimalPosition) {
                        updatedLineup[i].player = player;
                        placed = true;
                        break;
                    }
                }

                // If not placed, check composite positions (G, F, UTIL)
                if (!placed) {
                    for (let i = 0; i < updatedLineup.length; i++) {
                        if (!updatedLineup[i].player) {
                            const lineupPos = updatedLineup[i].position;
                            const playerPositions = player.position.split('/');

                            // Check if player can fill G position
                            if (lineupPos === 'G' && playerPositions.some(pos =>
                                positionMappings[sport]?.G?.includes(pos))) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }

                            // Check if player can fill F position
                            if (lineupPos === 'F' && playerPositions.some(pos =>
                                positionMappings[sport]?.F?.includes(pos))) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }

                            // Check if player can fill UTIL position
                            if (lineupPos === 'UTIL' && playerPositions.some(pos =>
                                positionMappings[sport]?.UTIL?.includes(pos))) {
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
    }, [draftedPlayers, sport]);

    useEffect(() => {
        // Calculate totals when lineup changes
        const totals = calculateTotals();
        setTotalSalary(totals.salary);
        setAveragePPG(totals.dkppg);
    }, [lineup]);

    const calculateTotals = () => {
        const filledPositions = lineup.filter(row => row.player);
        const totalSalary = filledPositions.reduce((sum, row) => sum + (row.player?.salary || 0), 0);
        const totalPPG = filledPositions.reduce((sum, row) => sum + (row.player?.dKppg || 0), 0);

        return {
            salary: totalSalary,
            dkppg: filledPositions.length > 0 ? totalPPG : 0
        };
    };

    const clearPosition = (positionIndex) => {
        // Get the player being removed
        const playerToRemove = lineup[positionIndex].player;

        if (playerToRemove) {
            // Create a new array of drafted players without the one being removed
            if (onResetLineup) {
                // Inform parent component about the change
                const updatedDraftedPlayers = draftedPlayers.filter(
                    p => p.playerDkId !== playerToRemove.playerDkId
                );
                // This will trigger a re-render with the updated props
                onResetLineup(updatedDraftedPlayers);
            }

            // Update the lineup
            const updatedLineup = [...lineup];
            updatedLineup[positionIndex] = {
                ...updatedLineup[positionIndex],
                player: null
            };
            setLineup(updatedLineup);
        }
    };

    const renderSalaryStatus = () => {
        const maxSalary = 50000; // Default salary cap
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
            <div className="lineup-table-container">
                {renderLineupTable()}
            </div>
            <div className="lineup-actions">
                <button
                    onClick={() => {
                        // Call the parent's reset function
                        if (onResetLineup) {
                            onResetLineup();
                        }

                        // Reset the local lineup display
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