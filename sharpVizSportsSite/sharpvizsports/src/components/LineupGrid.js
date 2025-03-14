import React, { useState, useEffect } from "react";
import "../css/LineupGrid.css";
import axios from "axios";

const LineupGrid = ({ teamName, lineup }) => {
  const [playerStats, setPlayerStats] = useState({});
  const [statsType, setStatsType] = useState("Last7G");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!lineup || !lineup.batting1st) return;

    const fetchStats = async () => {
      setLoading(true);

      const playerIds = [];
      for (let i = 1; i <= 9; i++) {
        const playerId = lineup[`batting${i}st`];
        if (playerId && playerId !== "N/A") {
          playerIds.push(playerId);
        }
      }

      try {
        const response = await axios.post(
          `https://localhost:44346/api/TrailingGameLogSplits/batch`,
          {
            BbrefIds: playerIds,
            Split: statsType
          }
        );

        setPlayerStats(response.data);
      } catch (error) {
        console.error("Error fetching player stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [lineup, statsType]);

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

  if (!lineup || !lineup.batting1st) {
    return <p className="empty-lineup">No lineup available for {teamName}</p>;
  }

  const renderPlayer = (position) => {
    const playerId = lineup[`batting${position}st`];
    const stats = playerId && playerStats[playerId];

    return (
      <tr key={position} className={playerId ? "" : "empty-slot"}>
        <td className="order-cell">{position}</td>
        <td className="player-cell">
          {playerId ? (
            
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
      </tr >
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