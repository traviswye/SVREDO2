// src/features/mlb/hooks/usePitcherMetrics.js
import { useState, useEffect } from 'react';
import { formatDate, extractPercentage, extractStatus } from '../utils/pitcherMetricsUtils';

export const usePitcherMetrics = (date) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [gamePreviewsResponse, pitcherTrendsResponse] = await Promise.all([
                    fetch(`https://localhost:44346/api/GamePreviews/${date}`),
                    fetch(`https://localhost:44346/api/Blending/todaysSPHistoryVsRecency?date=20${date}`)
                ]);

                const [gamePreviews, pitcherTrends] = await Promise.all([
                    gamePreviewsResponse.json(),
                    pitcherTrendsResponse.json()
                ]);

                const bbrefIds = [...new Set(
                    gamePreviews.flatMap(game => [game.homePitcher, game.awayPitcher])
                )];

                const playerNamesResponse = await fetch(
                    `https://localhost:44346/api/mlbplayer/batch`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(bbrefIds)
                    }
                );
                const playerNames = await playerNamesResponse.json();

                const trendsLookup = pitcherTrends.reduce((acc, trend) => {
                    acc[trend.pitcher] = trend.message?.trim()
                        ? trend
                        : { performanceStatus: "Unknown", message: "No data available" };
                    return acc;
                }, {});

                const mergedData = gamePreviews.map(game => {
                    const homePitcherTrend = trendsLookup[game.homePitcher] || {
                        performanceStatus: "N/A",
                        message: "No data available"
                    };
                    const awayPitcherTrend = trendsLookup[game.awayPitcher] || {
                        performanceStatus: "N/A",
                        message: "No data available"
                    };

                    return {
                        date: formatDate(game.date),
                        time: game.time,
                        homeTeam: game.homeTeam,
                        awayTeam: game.awayTeam,
                        venue: game.venue,
                        homePitcher: playerNames[game.homePitcher] || game.homePitcher,
                        homePitcherMessage: homePitcherTrend.message,
                        homePitcherStatus: extractStatus(homePitcherTrend.message),
                        awayPitcher: playerNames[game.awayPitcher] || game.awayPitcher,
                        awayPitcherMessage: awayPitcherTrend.message,
                        awayPitcherStatus: extractStatus(awayPitcherTrend.message),
                        homePercentage: extractPercentage(homePitcherTrend.message),
                        awayPercentage: extractPercentage(awayPitcherTrend.message),
                        previewLink: game.previewLink
                    };
                });

                setData(mergedData);
            } catch (error) {
                setError("Failed to fetch pitcher metrics data.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [date]);

    return { data, loading, error };
};