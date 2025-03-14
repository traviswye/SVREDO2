import React, { useState } from "react";
import "../css/PreviewDrawer.css";
import LineupGrid from "./LineupGrid";

const PreviewDrawer = ({ game, teamRecords, lineups, predictedLineups, parkFactors, onClose }) => {
  const [activeTab, setActiveTab] = useState("details");

  if (!game) return null;

  // Extract relevant data using helper functions
  const homeTeamRecord = getTeamRecord(game.homeTeam, teamRecords);
  const awayTeamRecord = getTeamRecord(game.awayTeam, teamRecords);
  const homeTeamLineup = getLineup(game.homeTeam, lineups, predictedLineups);
  const awayTeamLineup = getLineup(game.awayTeam, lineups, predictedLineups);
  const venueParkFactors = getParkFactors(game.venue, parkFactors);

  // Format win-loss records
  const formatRecord = (record) => {
    if (!record || !record.wins || !record.losses) return "N/A";
    return `${record.wins}-${record.losses} (${record.winPercentage.toFixed(3)})`;
  };

  // Format park factor data
  const formatParkFactor = (factor) => {
    if (!factor) return null;

    return {
      overall: factor.parkFactorRating || "N/A",
      homeRuns: factor.hr || "N/A",
      runs: factor.r || "N/A",
      hits: factor.h || "N/A"
    };
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  return (
    <div className="preview-drawer-overlay">
      <div className="preview-drawer">
        <div className="drawer-header">
          <h2 className="game-title">
            {game.awayTeam} @ {game.homeTeam}
          </h2>
          <button className="close-drawer-btn" onClick={onClose}>×</button>
        </div>

        <div className="drawer-tabs">
          <button
            className={`tab-button ${activeTab === 'details' ? 'active' : ''}`}
            onClick={() => handleTabChange('details')}
          >
            Game Details
          </button>
          <button
            className={`tab-button ${activeTab === 'lineups' ? 'active' : ''}`}
            onClick={() => handleTabChange('lineups')}
          >
            Lineups
          </button>
          <button
            className={`tab-button ${activeTab === 'matchups' ? 'active' : ''}`}
            onClick={() => handleTabChange('matchups')}
          >
            Matchups
          </button>
          <button
            className={`tab-button ${activeTab === 'stats' ? 'active' : ''}`}
            onClick={() => handleTabChange('stats')}
          >
            Team Stats
          </button>
        </div>

        <div className="drawer-content">
          {activeTab === 'details' && (
            <div className="tab-panel details-panel">
              <section className="game-basics-section">
                <h3 className="section-title">Game Details</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Time:</span>
                    <span className="info-value">{game.time}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Venue:</span>
                    <span className="info-value">{game.venue}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Temperature:</span>
                    <span className="info-value">{game.temperature}°F</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Wind:</span>
                    <span className="info-value">{game.windSpeed} MPH {game.windDescription}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Rain Probability:</span>
                    <span className="info-value">{game.rainProbability}%</span>
                  </div>
                </div>
                <div className="preview-link">
                  <a
                    href={game.previewLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bbref-link"
                  >
                    View on Baseball-Reference
                  </a>
                </div>
              </section>

              <section className="records-section">
                <h3 className="section-title">Team Records</h3>
                <div className="team-records">
                  <div className="team-record-card">
                    <h4 className="team-name">{game.awayTeam}</h4>
                    <div className="record-detail">
                      <span className="record-label">Record:</span>
                      <span className="record-value">{homeTeamRecord ? `${homeTeamRecord.wins}-${homeTeamRecord.losses}` : 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Win %:</span>
                      <span className="record-value">{homeTeamRecord?.winPercentage?.toFixed(3) || 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Away:</span>
                      <span className="record-value">{homeTeamRecord?.awayRec || 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Last 10:</span>
                      <span className="record-value">{homeTeamRecord?.l10 || 'N/A'}</span>
                    </div>
                  </div>

                  <div className="team-record-card">
                    <h4 className="team-name">{game.homeTeam}</h4>
                    <div className="record-detail">
                      <span className="record-label">Record:</span>
                      <span className="record-value">{awayTeamRecord ? `${awayTeamRecord.wins}-${awayTeamRecord.losses}` : 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Win %:</span>
                      <span className="record-value">{awayTeamRecord?.winPercentage?.toFixed(3) || 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Home:</span>
                      <span className="record-value">{awayTeamRecord?.homeRec || 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Last 10:</span>
                      <span className="record-value">{awayTeamRecord?.l10 || 'N/A'}</span>
                    </div>
                  </div>
                </div>
              </section>

              <section className="park-factors-section">
                <h3 className="section-title">Park Factors</h3>
                {venueParkFactors ? (
                  <div className="park-factors-grid">
                    <div className="park-factor-item">
                      <span className="factor-label">Overall:</span>
                      <span className="factor-value">{venueParkFactors.parkFactorRating || 'N/A'}</span>
                    </div>
                    <div className="park-factor-item">
                      <span className="factor-label">Home Runs:</span>
                      <span className="factor-value">{venueParkFactors.h || 'N/A'}</span>
                    </div>
                    <div className="park-factor-item">
                      <span className="factor-label">Runs:</span>
                      <span className="factor-value">{venueParkFactors.r || 'N/A'}</span>
                    </div>
                    <div className="park-factor-item">
                      <span className="factor-label">Hits:</span>
                      <span className="factor-value">{venueParkFactors.h || 'N/A'}</span>
                    </div>
                  </div>
                ) : (
                  <p className="no-data-message">No park factor data available for this venue.</p>
                )}
              </section>
            </div>
          )}

          {activeTab === 'lineups' && (
            <div className="tab-panel lineups-panel">
              <h3 className="section-title">Lineups</h3>
              <div className="lineups-container">
                <div className="lineup-section">
                  <LineupGrid teamName={game.awayTeam} lineup={awayTeamLineup} />
                </div>

                <div className="lineup-section">
                  <LineupGrid teamName={game.homeTeam} lineup={homeTeamLineup} />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'matchups' && (
            <div className="tab-panel matchups-panel">
              <section className="pitching-matchup-section">
                <h3 className="section-title">Pitching Matchup</h3>
                <p className="coming-soon">Detailed pitching matchup data coming soon.</p>
              </section>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="tab-panel stats-panel">
              <section className="team-stats-section">
                <h3 className="section-title">Team Statistics</h3>
                <p className="coming-soon">Detailed team statistics coming soon.</p>
              </section>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper Functions
const getTeamRecord = (teamName, teamRecords) => {
  return teamRecords.find((record) => record.team === teamName) || null;
};

const getLineup = (teamName, lineups, predictedLineups) => {
  // First try actual lineups
  if (lineups && Array.isArray(lineups)) {
    const lineup = lineups.find((lineup) => lineup.team === teamName);
    if (lineup) return lineup;
  }

  // Then try predicted lineups
  if (predictedLineups && Array.isArray(predictedLineups)) {
    const lineup = predictedLineups.find((lineup) => lineup.team === teamName);
    if (lineup) return lineup;
  }

  return null;
};

const getParkFactors = (venue, parkFactors) => {
  if (!parkFactors || !Array.isArray(parkFactors)) return null;
  return parkFactors.find((parkFactor) => parkFactor.venue === venue) || null;
};

export default PreviewDrawer;