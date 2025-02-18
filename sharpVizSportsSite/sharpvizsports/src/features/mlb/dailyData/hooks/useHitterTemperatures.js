// src/features/mlb/hooks/useHitterTemperatures.js
import { useState, useEffect } from 'react';

export const useHitterTemperatures = (date) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [tempTrackingResponse, trailingGameLogResponse] = await Promise.all([
                    fetch(`https://localhost:44346/api/HitterTempTracking/last7Days?targetDate=${date}`),
                    fetch(`https://localhost:44346/api/TrailingGameLogSplits/last7G`),
                ]);

                const tempTrackingData = await tempTrackingResponse.json();
                const trailingGameLogData = await trailingGameLogResponse.json();

                const trailingGameLogLookup = trailingGameLogData.reduce((acc, log) => {
                    acc[log.bbrefId] = log;
                    return acc;
                }, {});

                const mergedData = tempTrackingData
                    .filter((temp) => trailingGameLogLookup[temp.bbrefId])
                    .map((temp) => {
                        const log = trailingGameLogLookup[temp.bbrefId];
                        return {
                            date: temp.date.split("T")[0],
                            bbrefId: temp.bbrefId,
                            team: temp.team,
                            currentTemp: parseFloat(temp.currentTemp).toFixed(2),
                            trailingTemp1: parseFloat(temp.trailingTemp1).toFixed(2),
                            trailingTemp2: parseFloat(temp.trailingTemp2).toFixed(2),
                            trailingTemp3: parseFloat(temp.trailingTemp3).toFixed(2),
                            trailingTemp4: parseFloat(temp.trailingTemp4).toFixed(2),
                            trailingTemp5: parseFloat(temp.trailingTemp5).toFixed(2),
                            trailingTemp6: parseFloat(temp.trailingTemp6).toFixed(2),
                            splitParkFactor: parseFloat(log.splitParkFactor).toFixed(2),
                            g: log.g,
                            pa: log.pa,
                            hr: log.hr,
                            ba: parseFloat(log.ba).toFixed(3),
                            ops: parseFloat(log.ops).toFixed(3),
                            homeGames: log.homeGames,
                            awayGames: log.awayGames,
                        };
                    });

                setData(mergedData);
            } catch (error) {
                setError("Failed to fetch hitter temperature data.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [date]);

    return { data, loading, error };
};