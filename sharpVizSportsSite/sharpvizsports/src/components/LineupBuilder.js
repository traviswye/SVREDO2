import React, { useState, useEffect } from 'react';

const LineupBuilder = ({ sport, draftedPlayers }) => {
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

    useEffect(() => {
        // Reset lineup when sport changes
        setLineup(getPositionsForSport(sport).map(pos => ({
            position: pos,
            player: null
        })));
    }, [sport]);


    useEffect(() => {
        if (draftedPlayers.length > 0) {
            const emptyLineup = getPositionsForSport(sport).map(pos => ({
                position: pos,
                player: null
            }));

            const updatedLineup = [...emptyLineup];
            draftedPlayers.forEach(player => {
                // Use assignedPosition from optimization response
                const optimalPosition = player.assignedPosition || player.position.split('/')[0];
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
                                positionMappings[sport].G.includes(pos))) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }

                            // Check if player can fill F position
                            if (lineupPos === 'F' && playerPositions.some(pos =>
                                positionMappings[sport].F.includes(pos))) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }

                            // Check if player can fill UTIL position
                            if (lineupPos === 'UTIL' && playerPositions.some(pos =>
                                positionMappings[sport].UTIL.includes(pos))) {
                                updatedLineup[i].player = player;
                                placed = true;
                                break;
                            }
                        }
                    }
                }
            });

            setLineup(updatedLineup);
        }
    }, [draftedPlayers, sport]);

    const calculateTotals = () => {
        return lineup.reduce((totals, row) => {
            if (row.player) {
                totals.salary += row.player.salary;
                totals.dkppg += row.player.dKppg;
            }
            return totals;
        }, { salary: 0, dkppg: 0 });
    };

    const clearPosition = (positionIndex) => {
        const updatedLineup = [...lineup];
        updatedLineup[positionIndex] = {
            ...updatedLineup[positionIndex],
            player: null
        };
        setLineup(updatedLineup);
    };

    const renderLineupTable = () => {
        const totals = calculateTotals();

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
                        <tr key={`${row.position}-${index}`}>
                            <td>{row.position}</td>
                            <td>{row.player ? row.player.fullName : 'Empty'}</td>
                            <td>{row.player ? `$${row.player.salary}` : '-'}</td>
                            <td>{row.player ? row.player.game : '-'}</td>
                            <td>{row.player ? row.player.dKppg : '-'}</td>
                            <td>
                                <button
                                    onClick={() => clearPosition(index)}
                                    disabled={!row.player}
                                    className="clear-button"
                                >
                                    Clear
                                </button>
                            </td>
                        </tr>
                    ))}
                    <tr className="totals-row">
                        <td colSpan="2">Totals</td>
                        <td>${totals.salary}</td>
                        <td>-</td>
                        <td>{totals.dkppg.toFixed(2)}</td>
                        <td>
                            <button
                                onClick={() => setLineup(
                                    getPositionsForSport(sport).map(pos => ({
                                        position: pos,
                                        player: null
                                    }))
                                )}
                                className="reset-button"
                            >
                                Reset All
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        );
    };

    return (
        <div className="lineup-builder-container">
            <h2>{sport} Lineup Builder</h2>
            {renderLineupTable()}
        </div>
    );
};

export default LineupBuilder;