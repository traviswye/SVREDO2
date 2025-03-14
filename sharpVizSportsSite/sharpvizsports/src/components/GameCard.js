import React from "react";
import "../css/GameCard.css";

const GameCard = ({ game, homePitcher, awayPitcher, onClick }) => {
  const getBbRefLink = (bbrefId) => {
    if (!bbrefId) return null;
    const firstLetter = bbrefId.charAt(0);
    return `https://www.baseball-reference.com/players/${firstLetter}/${bbrefId}.shtml`;
  };

  const formatPitcher = (teamAbbreviation, pitcher) => {
    if (!pitcher) {
      return (
        <div className="pitcher-info unannounced">
          <span className="team-abbr">{teamAbbreviation}</span>
          <span className="pitcher-status">Unannounced</span>
        </div>
      );
    }

    return (
      <div className="pitcher-info">
        <span className="team-abbr">{teamAbbreviation}</span>
        <a
          href={getBbRefLink(pitcher.bbrefId)}
          target="_blank"
          rel="noopener noreferrer"
          className="pitcher-name"
        >
          {pitcher.bbrefId}
        </a>
        <span className="pitcher-hand">{pitcher.throws}</span>
        <span className="pitcher-record">
          <span className="stat-label">W-L:</span> {pitcher.wl || "N/A"}
        </span>
        <span className="pitcher-era">
          <span className="stat-label">ERA:</span> {pitcher.era || "N/A"}
        </span>
      </div>
    );
  };

  // Calculate a color for rain probability indicator
  const getRainProbColor = (probability) => {
    if (probability >= 70) return "#d32f2f"; // High chance - red
    if (probability >= 40) return "#f57c00"; // Medium chance - orange
    if (probability >= 20) return "#ffb300"; // Low chance - amber
    return "#7cb342"; // Very low chance - light green
  };

  // Format the game date/time
  const formatGameTime = (timeString) => {
    if (!timeString) return "TBD";
    // Just return the time as-is since it already has AM/PM
    return timeString;
  };

  return (
    <div className="game-card" onClick={() => onClick(game)}>
      <div className="card-header">
        <div className="game-time">{formatGameTime(game.time)}</div>
        {game.rainProbability > 0 && (
          <div
            className="rain-indicator"
            title={`${game.rainProbability}% chance of rain`}
            style={{
              backgroundColor: getRainProbColor(game.rainProbability),
              opacity: game.rainProbability / 100 + 0.3 // Min opacity 0.3
            }}
          >
            <span className="rain-icon">💧</span>
            <span className="rain-prob">{game.rainProbability}%</span>
          </div>
        )}
      </div>

      <div className="matchup-header">
        <h3>{game.awayTeam} @ {game.homeTeam}</h3>
      </div>

      <div className="venue-info">
        <div className="venue-name">{game.venue}</div>
        <div className="weather-info">
          <span className="temperature">
            <span className="weather-icon">🌡️</span> {game.temperature}°F
          </span>
          <span className="wind-info">
            <span className="weather-icon">💨</span> {game.windDescription}
          </span>
        </div>
      </div>

      <div className="pitchers-container">
        <div className="away-pitcher">
          {formatPitcher(game.awayTeamAbbreviation, awayPitcher)}
        </div>
        <div className="pitcher-vs">VS</div>
        <div className="home-pitcher">
          {formatPitcher(game.homeTeamAbbreviation, homePitcher)}
        </div>
      </div>

      <div className="card-footer">
        <button className="view-details-btn">View Details</button>
      </div>
    </div>
  );
};

export default GameCard;