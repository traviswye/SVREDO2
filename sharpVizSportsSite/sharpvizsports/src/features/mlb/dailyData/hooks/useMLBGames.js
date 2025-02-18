// src/features/mlb/hooks/useMLBGames.js
import { useState, useEffect } from 'react';
import { formatDate } from '../../../../utils/dateUtils';
import { getTeamAbbreviation } from '../../../mlb/utils/teamUtils';

export const useMLBGames = (selectedDate) => {
    const [games, setGames] = useState([]);
    const [pitchers, setPitchers] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchGames = async () => {
            setLoading(true);
            try {
                const shortDate = selectedDate.substring(2);

                const [gamesResponse, pitchersResponse] = await Promise.all([
                    fetch(`https://localhost:44346/api/GamePreviews/${shortDate}`),
                    fetch(`https://localhost:44346/api/Pitchers/pitchersByDate/${shortDate}`)
                ]);

                const [gamesData, pitchersData] = await Promise.all([
                    gamesResponse.json(),
                    pitchersResponse.json()
                ]);

                const uniqueGames = Array.from(
                    new Set(gamesData.map((game) => game.id))
                ).map((id) => gamesData.find((game) => game.id === id));

                const pitchersMap = pitchersData.reduce((map, pitcher) => {
                    if (!map[pitcher.bbrefId] || map[pitcher.bbrefId].year < pitcher.year) {
                        map[pitcher.bbrefId] = pitcher;
                    }
                    return map;
                }, {});

                setGames(uniqueGames.map(game => ({
                    ...game,
                    awayTeamAbbreviation: getTeamAbbreviation(game.awayTeam),
                    homeTeamAbbreviation: getTeamAbbreviation(game.homeTeam),
                })));
                setPitchers(pitchersMap);
            } catch (error) {
                setError(error);
            } finally {
                setLoading(false);
            }
        };

        fetchGames();
    }, [selectedDate]);

    return { games, pitchers, loading, error };
};