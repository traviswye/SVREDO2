import React, { useState, useEffect } from "react";
import "../css/LineupGrid.css";
import axios from "axios";

const LineupGrid = ({ teamName, lineup }) => {
  const [playerStats, setPlayerStats] = useState({});
  const [statsType, setStatsType] = useState("Last7G");
  const [loading, setLoading] = useState(false);

  // Helper to get player ID from lineup based on position
  const getPlayerIdForPosition = (position) => {
    if (!lineup) return null;

    // Try different possible property naming conventions
    const possibleKeys = [
      `batting${position}st`,      // batting1st, batting2st, etc.
      `Batting${position}st`,      // Batting1st, Batting2st, etc.
    ];

    // Special case conversions for proper ordinal suffixes
    if (position === 2) {
      possibleKeys.push(`batting${position}nd`, `Batting${position}nd`);
    } else if (position === 3) {
      possibleKeys.push(`batting${position}rd`, `Batting${position}rd`);
    } else if (position >= 4) {
      possibleKeys.push(`batting${position}th`, `Batting${position}th`);
    }

    // Try all possible keys
    for (const key of possibleKeys) {
      if (lineup[key] && lineup[key] !== "N/A") {
        return lineup[key];
      }
    }

    return null;
  };

  // Check if the lineup has any valid players
  const hasAnyPlayers = () => {
    if (!lineup) return false;

    for (let i = 1; i <= 9; i++) {
      if (getPlayerIdForPosition(i)) {
        return true;
      }
    }

    return false;
  };

  useEffect(() => {
    if (!lineup) return;

    // Create a stable reference for playerIds
    const getPlayerIds = () => {
      const ids = [];

      // Check the structure of the lineup object and extract player IDs correctly
      // Method 1: Check for batting1st, batting2st, etc. format
      if (lineup.batting1st) {
        for (let i = 1; i <= 9; i++) {
          const playerId = lineup[`batting${i}st`];
          if (playerId && playerId !== "N/A") {
            ids.push(playerId);
          }
        }
      }
      // Method 2: Check for Batting1st, Batting2nd, etc. format (camelCase with "nd", "rd", "th")
      else if (lineup.Batting1st) {
        const positions = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"];
        positions.forEach(pos => {
          const key = `Batting${pos}`;
          if (lineup[key] && lineup[key] !== "N/A") {
            ids.push(lineup[key]);
          }
        });
      }
      // Method 3: Just log and look for any property that might contain player IDs
      else {
        console.log("Lineup structure:", Object.keys(lineup));
        // Try to find any property that might contain a player ID
        Object.keys(lineup).forEach(key => {
          if (key.toLowerCase().includes('batting') && lineup[key] && lineup[key] !== "N/A") {
            console.log(`Found player ID in key ${key}:`, lineup[key]);
            ids.push(lineup[key]);
          }
        });
      }

      console.log("Collected player IDs:", ids);
      return ids;
    };

    const fetchStats = async () => {
      setLoading(true);
      const playerIds = getPlayerIds();

      // Only fetch if we have player IDs
      if (playerIds.length === 0) {
        console.log("No player IDs found in lineup object:", lineup);
        setLoading(false);
        return;
      }

      try {
        console.log("Fetching stats for players:", playerIds);
        const response = await axios.post(
          `https://localhost:44346/api/TrailingGameLogSplits/batch`,
          {
            BbrefIds: playerIds,
            Split: statsType
          }
        );

        console.log("API Response:", response.data);
        setPlayerStats(response.data || {});
      } catch (error) {
        console.error("Error fetching player stats:", error);
        // Set empty object to prevent undefined errors
        setPlayerStats({});
      } finally {
        setLoading(false);
      }
    };

    fetchStats();

    // Cleanup function to prevent state updates if component unmounts
    return () => {
      // This empty cleanup function helps React know this effect can be cleaned up
    };
    // Use a deep comparison for lineup object
  }, [statsType, JSON.stringify(lineup)]);

  const getBbRefURL = (playerId) => {
    if (!playerId || playerId === "N/A") return "#";
    const firstLetter = playerId.charAt(0);
    return `https://www.baseball-reference.com/players/${firstLetter}/${playerId}.shtml`;
  };

  const formatStat = (value, precision = 3) => {
    if (value === undefined || value === null) return "-";
    if (typeof value === 'number') {
      if (Number.isInteger(value)) return value.toString();
      return value.toFixed(precision);
    }
    return value;
  };

  const toggleStatsType = () => {
    setStatsType(prev => prev === "Last7G" ? "Season" : "Last7G");
  };

  if (!lineup || !hasAnyPlayers()) {
    return <p className="empty-lineup">No lineup available for {teamName}</p>;
  }

  // Render function for player rows
  const renderPlayer = (position) => {
    const playerId = getPlayerIdForPosition(position);
    // Safely access stats with optional chaining
    const stats = playerId && playerStats ? playerStats[playerId] : null;

    return (
      <tr key={position} className={playerId ? "" : "empty-slot"}>
        <td className="order-cell">{position}</td>
        <td className="player-cell">
          {playerId ? (
            <a
              href={getBbRefURL(playerId)}
              target="_blank"
              rel="noopener noreferrer"
              className="player-link"
            >
              {playerId}
            </a>
          ) : (
            <span className="tbd-player">TBD</span>
          )}
        </td>
        <td className="stat-cell">{stats ? formatStat(stats.BA) : "-"}</td>
        <td className="stat-cell">{stats ? formatStat(stats.HR, 0) : "-"}</td>
        <td className="stat-cell">{stats ? formatStat(stats.OPS) : "-"}</td>
        <td className="stat-cell">{stats ? formatStat(stats.PA, 0) : "-"}</td>
      </tr>
    );
  };

  return (
    <div className="lineup-grid">
      <div className="stats-toggle">
        <button
          className={`toggle-button ${statsType === "Last7G" ? "active" : ""}`}
          onClick={toggleStatsType}
        >
          {loading ? "Loading..." : statsType === "Last7G" ? "Last 7 Games" : "Season Stats"}
        </button>
      </div>

      <table className="lineup-table">
        <thead>
          <tr>
            <th className="order-column">#</th>
            <th className="player-column">Player</th>
            <th className="stats-column">AVG</th>
            <th className="stats-column">HR</th>
            <th className="stats-column">OPS</th>
            <th className="stats-column">PA</th>
          </tr>
        </thead>
        <tbody>
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(position => renderPlayer(position))}
        </tbody>
      </table>

      <div className="lineup-source">
        <div className={statsType === "Last7G" ? "last7-tag" : "season-tag"}>
          {statsType === "Last7G" ? "Last 7 Games" : "Season"} Stats
        </div>
        {lineup.source ? (
          <div className={lineup.source === "predicted" ? "predicted-tag" : "confirmed-tag"}>
            {lineup.source === "predicted" ? "Predicted" : "Confirmed"} Lineup
          </div>
        ) : (
          <div className="predicted-tag">Lineup</div>
        )}
      </div>
    </div>
  );
};

export default LineupGrid;