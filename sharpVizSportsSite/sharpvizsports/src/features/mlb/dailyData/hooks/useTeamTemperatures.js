// src/features/mlb/dailyData/hooks/useTeamTemperatures.js
import { useState, useEffect } from 'react';

export const useTeamTemperatures = (date) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(
                    `https://localhost:44346/api/TeamTemperatureTracking/latest-teams/2024/true`
                );
                const json = await response.json();
                setData(json);
            } catch (err) {
                setError("Failed to fetch team temperatures");
                console.error("Error fetching team temperatures:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [date]);

    return { data, loading, error };
};