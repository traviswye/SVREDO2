// src/features/mlb/hooks/useMLBStaticData.js
import { useState, useEffect } from 'react';

export const useMLBStaticData = (date) => {
    const [teamRecords, setTeamRecords] = useState({});
    const [parkFactors, setParkFactors] = useState({});
    const [lineups, setLineups] = useState({});
    const [predictedLineups, setPredictedLineups] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStaticData = async () => {
            try {
                setLoading(true);

                // Fetch all static data in parallel
                const [
                    teamRecordsResponse,
                    parkFactorsResponse,
                    lineupsResponse,
                    predictedLineupsResponse
                ] = await Promise.all([
                    fetch("https://localhost:44346/api/TeamRecSplits"),
                    fetch("https://localhost:44346/api/ParkFactors"),
                    fetch(`https://localhost:44346/api/Lineups/Actual/${date}`),
                    fetch(`https://localhost:44346/api/Lineups/Predictions/date/${date}`)
                ]);

                const [
                    teamRecordsData,
                    parkFactorsData,
                    lineupsData,
                    predictedLineupsData
                ] = await Promise.all([
                    teamRecordsResponse.json(),
                    parkFactorsResponse.json(),
                    lineupsResponse.json(),
                    predictedLineupsResponse.json()
                ]);

                setTeamRecords(teamRecordsData);
                setParkFactors(parkFactorsData);
                setLineups(lineupsData);
                setPredictedLineups(predictedLineupsData);
                setError(null);
            } catch (err) {
                setError("Failed to fetch MLB static data");
                console.error("Error fetching MLB static data:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchStaticData();
    }, [date]);

    return {
        teamRecords,
        parkFactors,
        lineups,
        predictedLineups,
        loading,
        error
    };
};