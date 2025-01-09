import React from "react";
import "../css/PreviewDrawer.css";
import LineupGrid from "./LineupGrid";

const PreviewDrawer = ({ game, teamRecords, lineups, predictedLineups, parkFactors, onClose }) => {
  if (!game) return null;

  // Extract relevant data using helper functions
  const homeTeamRecord = getTeamRecord(game.homeTeam, teamRecords);
  const awayTeamRecord = getTeamRecord(game.awayTeam, teamRecords);
  const homeTeamLineup = getLineup(game.homeTeam, lineups, predictedLineups);
  const awayTeamLineup = getLineup(game.awayTeam, lineups, predictedLineups);
  const venueParkFactors = getParkFactors(game.venue, parkFactors);

  return (
    <div className="preview-drawer">
      {/* Drawer Header */}
      <div className="drawer-header">
        <h2>
          {game.awayTeam} @ {game.homeTeam}
        </h2>
        <button onClick={onClose}>Close</button>
      </div>

      {/* Drawer Content */}
      <div className="drawer-content">
        {/* Game Details */}
        <section>
          <p><strong>Venue:</strong> {game.venue}</p>
          <p><strong>Time:</strong> {game.time}</p>
          <p><strong>Temperature:</strong> {game.temperature}°F</p>
          <p><strong>Wind Speed:</strong> {game.windSpeed + " MPH"}</p>
          <p><strong>Wind Gusts:</strong> {game.windGusts + " MPH"}</p>
          <p><strong>Wind Direction:</strong> {game.windDescription}</p>
          <p><strong>Rain Probability:</strong> {game.rainProbability}%</p>
          <a href={game.previewLink} target="_blank" rel="noopener noreferrer">
            Baseball-Reference Preview
          </a>
        </section>

        {/* Records Section */}
        <section className="drawer-section">
          <h3>Records</h3>
          <p><strong>{game.awayTeam}:</strong> {JSON.stringify(awayTeamRecord)}</p>
          <p><strong>{game.homeTeam}:</strong> {JSON.stringify(homeTeamRecord)}</p>
        </section>
        {/* Last 5 Section */}
        <section className="drawer-section">
          <h3>Last 5 Games</h3>
          <p>Loading recent games data...</p> {/* Placeholder */}
        </section>

        {/* Pitching Matchup Section */}
        <section className="drawer-section">
          <h3>Pitching Matchup</h3>
          <p>Loading pitching matchup...</p> {/* Placeholder */}
        </section>
        {/* Lineups Section */}
        <section className="drawer-section">
        <h3>Lineups</h3>
          <div className="lineups-container">
            <LineupGrid teamName={game.awayTeam} lineup={awayTeamLineup} />
            <LineupGrid teamName={game.homeTeam} lineup={homeTeamLineup} />
          </div>
        </section>

        {/* Park Factors Section */}
        <section className="drawer-section">
          <h3>Park Factors</h3>
          <p><strong>{game.venue}:</strong> {JSON.stringify(venueParkFactors)}</p>
        </section>

        {/* Additional Sections */}
                {/* Hot and Cold Section */}
        <section className="drawer-section">
          <h3>Hot and Cold</h3>
          <p>Loading hot and cold player data...</p> {/* Placeholder */}
        </section>

        {/* Odds Section */}
        <section className="drawer-section">
          <h3>Odds</h3>
          <p>Loading game odds...</p> {/* Placeholder */}
        </section>

        {/* SharpViz Pick Section */}
        <section className="drawer-section">
          <h3>SharpViz Pick</h3>
          <p>Loading SharpViz prediction...</p> {/* Placeholder */}
        </section>
        {/* Add sections for Last 5, Hot and Cold, Odds, etc. as needed */}
      </div>
    </div>
  );
};

// Helper Functions
const getTeamRecord = (teamName, teamRecords) => {
  return teamRecords.find((record) => record.team === teamName) || {};
};

const getLineup = (teamName, lineups, predictedLineups) => {
  const lineup = lineups.find((lineup) => lineup.team === teamName);
  if (lineup) return lineup;

  return predictedLineups.find((lineup) => lineup.team === teamName) || {};
};

const getParkFactors = (venue, parkFactors) => {
  return parkFactors.find((parkFactor) => parkFactor.venue === venue) || {};
};

export default PreviewDrawer;
