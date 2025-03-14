import React, { useState, useEffect } from "react";
import "../css/PreviewDrawer.css";
import LineupGrid from "./LineupGrid";

const PreviewDrawer = ({ game, teamRecords, lineups, predictedLineups, parkFactors, onClose }) => {
  const [activeTab, setActiveTab] = useState("details");
  const [pitchers, setPitchers] = useState({});
  const [hitterVsPitcher, setHitterVsPitcher] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchPitcherData = async () => {
      if (!game) return;
      setLoading(true);
      try {
        // Format the date for the API call (YY-MM-DD)
        const dateParts = game.date ? game.date.split('T')[0].split('-') : [];
        const apiDate = dateParts.length === 3
          ? `${dateParts[0].slice(-2)}-${dateParts[1]}-${dateParts[2]}`
          : "24-09-13"; // Fallback date if game.date is not properly formatted

        // Fetch pitcher data
        const pitchersResponse = await fetch(`https://localhost:44346/api/Pitchers/pitchersByDate/${apiDate}`);
        if (pitchersResponse.ok) {
          const pitchersData = await pitchersResponse.json();
          const pitchersMap = pitchersData.reduce((map, pitcher) => {
            map[pitcher.bbrefId] = pitcher;
            return map;
          }, {});
          setPitchers(pitchersMap);
        }

        // Fetch hitter vs pitcher data
        const hvpResponse = await fetch(`https://localhost:44346/api/HitterVsPitcher/LineupView/${apiDate}`);
        if (hvpResponse.ok) {
          const hvpData = await hvpResponse.json();
          setHitterVsPitcher(hvpData);
        }
      } catch (error) {
        console.error("Error fetching pitcher data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPitcherData();
  }, [game]);

  if (!game) return null;

  // Extract relevant data using helper functions
  const homeTeamRecord = getTeamRecord(game.homeTeam, teamRecords);
  const awayTeamRecord = getTeamRecord(game.awayTeam, teamRecords);
  const homeTeamLineup = getLineup(game.homeTeam, lineups, predictedLineups);
  const awayTeamLineup = getLineup(game.awayTeam, lineups, predictedLineups);
  const venueParkFactors = getParkFactors(game.venue, parkFactors);

  // Get pitcher objects
  const homePitcher = pitchers[game.homePitcher] || null;
  const awayPitcher = pitchers[game.awayPitcher] || null;

  // Get hitter vs pitcher data
  const getHitterVsPitcherStats = (gameId, pitcherId) => {
    if (!hitterVsPitcher || !hitterVsPitcher.length) return [];

    const gameHvp = hitterVsPitcher.find(item =>
      item.game && item.game.id === gameId && item.game.pitcher === pitcherId);

    return gameHvp?.game?.hitters || [];
  };

  const homeHittersVsAwayPitcher = getHitterVsPitcherStats(game.id, game.awayPitcher);
  const awayHittersVsHomePitcher = getHitterVsPitcherStats(game.id, game.homePitcher);

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
                    <span className="info-label">Roof Type:</span>
                    <span className="info-value">{venueParkFactors?.roofType || "Open"}</span>
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
                      <span className="record-value">{awayTeamRecord ? `${awayTeamRecord.wins}-${awayTeamRecord.losses}` : 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Win %:</span>
                      <span className="record-value">{awayTeamRecord?.winPercentage?.toFixed(3) || 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Away:</span>
                      <span className="record-value">{awayTeamRecord?.awayRec || 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Last 10:</span>
                      <span className="record-value">{awayTeamRecord?.l10 || 'N/A'}</span>
                    </div>
                  </div>

                  <div className="team-record-card">
                    <h4 className="team-name">{game.homeTeam}</h4>
                    <div className="record-detail">
                      <span className="record-label">Record:</span>
                      <span className="record-value">{homeTeamRecord ? `${homeTeamRecord.wins}-${homeTeamRecord.losses}` : 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Win %:</span>
                      <span className="record-value">{homeTeamRecord?.winPercentage?.toFixed(3) || 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Home:</span>
                      <span className="record-value">{homeTeamRecord?.homeRec || 'N/A'}</span>
                    </div>
                    <div className="record-detail">
                      <span className="record-label">Last 10:</span>
                      <span className="record-value">{homeTeamRecord?.l10 || 'N/A'}</span>
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
                      <span className="factor-value">{venueParkFactors.hr || 'N/A'}</span>
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
                {loading ? (
                  <div className="loading-spinner-container">
                    <div className="loading-spinner"></div>
                    <p>Loading pitcher data...</p>
                  </div>
                ) : (
                  <>
                    <div className="pitchers-comparison">
                      <div className="pitcher-card">
                        <h4 className="pitcher-name">
                          <a href={`https://www.baseball-reference.com/players/${game.awayPitcher.charAt(0)}/${game.awayPitcher}.shtml`}
                            target="_blank"
                            rel="noopener noreferrer">
                            {game.awayPitcher}
                          </a>
                          <span className="team-abbr">{game.awayTeamAbbreviation}</span>
                          {awayPitcher && <span className="throws-info">{awayPitcher.throws}</span>}
                        </h4>

                        {awayPitcher ? (
                          <div className="pitcher-stats">
                            <div className="pitcher-stat">
                              <span className="stat-label">Record:</span>
                              <span className="stat-value">{awayPitcher.wl || "0-0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">ERA:</span>
                              <span className="stat-value">{awayPitcher.era?.toFixed(2) || "0.00"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">WHIP:</span>
                              <span className="stat-value">{awayPitcher.whip?.toFixed(3) || "0.000"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">IP:</span>
                              <span className="stat-value">{awayPitcher.ip || "0.0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">SO:</span>
                              <span className="stat-value">{awayPitcher.so || "0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">BB:</span>
                              <span className="stat-value">{awayPitcher.bb || "0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">SO/9:</span>
                              <span className="stat-value">{awayPitcher.sO9?.toFixed(1) || "0.0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">BB/9:</span>
                              <span className="stat-value">{awayPitcher.bB9?.toFixed(1) || "0.0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">ERA+:</span>
                              <span className="stat-value">{awayPitcher.eraPlus || "100"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">FIP:</span>
                              <span className="stat-value">{awayPitcher.fip?.toFixed(2) || "0.00"}</span>
                            </div>
                          </div>
                        ) : (
                          <p className="no-data-message">Pitcher data not available</p>
                        )}
                      </div>

                      <div className="pitcher-card">
                        <h4 className="pitcher-name">
                          <a href={`https://www.baseball-reference.com/players/${game.homePitcher.charAt(0)}/${game.homePitcher}.shtml`}
                            target="_blank"
                            rel="noopener noreferrer">
                            {game.homePitcher}
                          </a>
                          <span className="team-abbr">{game.homeTeamAbbreviation}</span>
                          {homePitcher && <span className="throws-info">{homePitcher.throws}</span>}
                        </h4>

                        {homePitcher ? (
                          <div className="pitcher-stats">
                            <div className="pitcher-stat">
                              <span className="stat-label">Record:</span>
                              <span className="stat-value">{homePitcher.wl || "0-0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">ERA:</span>
                              <span className="stat-value">{homePitcher.era?.toFixed(2) || "0.00"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">WHIP:</span>
                              <span className="stat-value">{homePitcher.whip?.toFixed(3) || "0.000"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">IP:</span>
                              <span className="stat-value">{homePitcher.ip || "0.0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">SO:</span>
                              <span className="stat-value">{homePitcher.so || "0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">BB:</span>
                              <span className="stat-value">{homePitcher.bb || "0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">SO/9:</span>
                              <span className="stat-value">{homePitcher.sO9?.toFixed(1) || "0.0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">BB/9:</span>
                              <span className="stat-value">{homePitcher.bB9?.toFixed(1) || "0.0"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">ERA+:</span>
                              <span className="stat-value">{homePitcher.eraPlus || "100"}</span>
                            </div>
                            <div className="pitcher-stat">
                              <span className="stat-label">FIP:</span>
                              <span className="stat-value">{homePitcher.fip?.toFixed(2) || "0.00"}</span>
                            </div>
                          </div>
                        ) : (
                          <p className="no-data-message">Pitcher data not available</p>
                        )}
                      </div>
                    </div>

                    <div className="matchup-history">
                      <h3 className="section-title">{game.homeTeam} Hitters vs. {game.awayTeam} Pitcher</h3>
                      <div className="hvp-table-container">
                        {homeHittersVsAwayPitcher.length > 0 ? (
                          <table className="hvp-table">
                            <thead>
                              <tr>
                                <th>Hitter</th>
                                <th>PA</th>
                                <th>H</th>
                                <th>HR</th>
                                <th>RBI</th>
                                <th>BB</th>
                                <th>SO</th>
                                <th>BA</th>
                                <th>OBP</th>
                                <th>SLG</th>
                                <th>OPS</th>
                              </tr>
                            </thead>
                            <tbody>
                              {homeHittersVsAwayPitcher.map((hvp, index) => (
                                <tr key={`home-${index}`}>
                                  <td className="hitter-cell">
                                    <a href={hvp.matchupURL || "#"} target="_blank" rel="noopener noreferrer">
                                      {hvp.hitter}
                                    </a>
                                  </td>
                                  <td>{hvp.pa}</td>
                                  <td>{hvp.hits}</td>
                                  <td>{hvp.hr}</td>
                                  <td>{hvp.rbi}</td>
                                  <td>{hvp.bb}</td>
                                  <td>{hvp.so}</td>
                                  <td>{hvp.ba?.toFixed(3) || ".000"}</td>
                                  <td>{hvp.obp?.toFixed(3) || ".000"}</td>
                                  <td>{hvp.slg?.toFixed(3) || ".000"}</td>
                                  <td>{hvp.ops?.toFixed(3) || ".000"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : (
                          <p className="no-data-message">No matchup history available</p>
                        )}
                      </div>

                      <h3 className="section-title">{game.awayTeam} Hitters vs. {game.homeTeam} Pitcher</h3>
                      <div className="hvp-table-container">
                        {awayHittersVsHomePitcher.length > 0 ? (
                          <table className="hvp-table">
                            <thead>
                              <tr>
                                <th>Hitter</th>
                                <th>PA</th>
                                <th>H</th>
                                <th>HR</th>
                                <th>RBI</th>
                                <th>BB</th>
                                <th>SO</th>
                                <th>BA</th>
                                <th>OBP</th>
                                <th>SLG</th>
                                <th>OPS</th>
                              </tr>
                            </thead>
                            <tbody>
                              {awayHittersVsHomePitcher.map((hvp, index) => (
                                <tr key={`away-${index}`}>
                                  <td className="hitter-cell">
                                    <a href={hvp.matchupURL || "#"} target="_blank" rel="noopener noreferrer">
                                      {hvp.hitter}
                                    </a>
                                  </td>
                                  <td>{hvp.pa}</td>
                                  <td>{hvp.hits}</td>
                                  <td>{hvp.hr}</td>
                                  <td>{hvp.rbi}</td>
                                  <td>{hvp.bb}</td>
                                  <td>{hvp.so}</td>
                                  <td>{hvp.ba?.toFixed(3) || ".000"}</td>
                                  <td>{hvp.obp?.toFixed(3) || ".000"}</td>
                                  <td>{hvp.slg?.toFixed(3) || ".000"}</td>
                                  <td>{hvp.ops?.toFixed(3) || ".000"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : (
                          <p className="no-data-message">No matchup history available</p>
                        )}
                      </div>
                    </div>
                  </>
                )}
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