import React, { useState, useEffect } from "react";
import "../css/LineupGrid.css";
import axios from "axios";

const LineupGrid = ({ teamName, lineup }) => {
  const [playerStats, setPlayerStats] = useState({});
  const [statsType, setStatsType] = useState("Last7G");
  const [loading, setLoading] = useState(false);

  // Helper function to extract player IDs consistently regardless of property naming convention
  const extractPlayerIds = () => {
    if (!lineup) return [];

    const playerIds = [];
    const positions = [1, 2, 3, 4, 5, 6, 7, 8, 9];

    // Check various naming patterns
    positions.forEach(pos => {
      // Check all possible key formats
      const possibleKeys = [
        `batting${pos}st`,
        `batting${pos}nd`,
        `batting${pos}rd`,
        `batting${pos}th`,
        `Batting${pos}st`,
        `Batting${pos}nd`,
        `Batting${pos}rd`,
        `Batting${pos}th`,
        // Add exact match format
        `Batting${pos === 1 ? '1st' : pos === 2 ? '2nd' : pos === 3 ? '3rd' : pos + 'th'}`
      ];

      // Try each key until we find a match
      for (const key of possibleKeys) {
        if (lineup[key] && lineup[key] !== "N/A") {
          playerIds.push(lineup[key]);
          break; // Found a match, move to next position
        }
      }
    });

    console.log(`Extracted ${playerIds.length} player IDs from ${teamName} lineup:`, playerIds);
    return playerIds;
  };

  // Check if the lineup has any valid players
  const hasAnyPlayers = () => {
    return extractPlayerIds().length > 0;
  };

  // Determine if this is a predicted lineup
  const isPredicted = () => {
    // Check various properties that might indicate if this is a predicted lineup
    if (lineup.source === "predicted") return true;
    if (lineup.isPredicted) return true;
    if (lineup.Date && !lineup.Result) return true; // Likely a prediction if it has a date but no result
    return false;
  };

  useEffect(() => {
    if (!lineup) return;

    const fetchStats = async () => {
      setLoading(true);
      const playerIds = extractPlayerIds();

      if (playerIds.length === 0) {
        console.log(`No player IDs found in ${teamName} lineup:`, lineup);
        setLoading(false);
        return;
      }

      try {
        console.log(`Fetching ${statsType} stats for ${teamName} players:`, playerIds);
        const response = await axios.post(
          `https://localhost:44346/api/TrailingGameLogSplits/batch`,
          {
            BbrefIds: playerIds,
            Split: statsType
          }
        );

        if (response.data) {
          console.log(`Received stats for ${teamName} players:`, response.data);
          setPlayerStats(response.data);
        } else {
          console.warn(`No stats returned for ${teamName} players`);
          setPlayerStats({});
        }
      } catch (error) {
        console.error(`Error fetching ${teamName} player stats:`, error);
        setPlayerStats({});
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [statsType, lineup, teamName]);

  // Get player ID for a specific batting order position
  const getPlayerIdForPosition = (position) => {
    if (!lineup) return null;

    // Try different formats based on position number
    const possibleKeys = [];

    if (position === 1) {
      possibleKeys.push("batting1st", "Batting1st");
    } else if (position === 2) {
      possibleKeys.push("batting2nd", "Batting2nd");
    } else if (position === 3) {
      possibleKeys.push("batting3rd", "Batting3rd");
    } else {
      possibleKeys.push(`batting${position}th`, `Batting${position}th`);
    }

    // Try all variations to find a match
    for (const key of possibleKeys) {
      if (lineup[key] && lineup[key] !== "N/A") {
        return lineup[key];
      }
    }

    return null;
  };

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

  if (!lineup || !hasAnyPlayers()) {
    return <p className="empty-lineup">No lineup available for {teamName}</p>;
  }

  // Render function for player rows
  const renderPlayer = (position) => {
    const playerId = getPlayerIdForPosition(position);
    const stats = playerId && playerStats[playerId];

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
        <td className="stat-cell">{stats ? formatStat(stats.ba) : "-"}</td>
        <td className="stat-cell">{stats ? formatStat(stats.hr, 0) : "-"}</td>
        <td className="stat-cell">{stats ? formatStat(stats.ops) : "-"}</td>
        <td className="stat-cell">{stats ? formatStat(stats.pa, 0) : "-"}</td>
      </tr>
    );
  };

  return (
    <div className="lineup-grid">
      <div className="lineup-header">
        <h3 className="team-name">{teamName}</h3>
        <div className="lineup-status">
          <span className={isPredicted() ? "predicted-badge" : "confirmed-badge"}>
            {isPredicted() ? "Projected" : "Confirmed"}
          </span>
        </div>
      </div>

      <div className="stats-tabs">
        <button
          className={`tab-button ${statsType === "Last7G" ? "active" : ""}`}
          onClick={() => setStatsType("Last7G")}
        >
          Last 7 Games
        </button>
        <button
          className={`tab-button ${statsType === "Season" ? "active" : ""}`}
          onClick={() => setStatsType("Season")}
        >
          Season Stats
        </button>
        {loading && <span className="loading-indicator">Loading...</span>}
      </div>

      <div className="lineup-table-container">
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
      </div>
    </div>
  );
};

export default LineupGrid;