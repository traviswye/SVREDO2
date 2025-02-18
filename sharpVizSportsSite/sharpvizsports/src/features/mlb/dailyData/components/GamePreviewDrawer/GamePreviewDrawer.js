// src/features/mlb/components/GamePreviewDrawer/GamePreviewDrawer.js
import React from 'react';
import Drawer from '../../../../../components/common/Drawer/Drawer';
import './GamePreviewDrawer.css';

const GamePreviewDrawer = ({
  game,
  parkFactors,
  teamRecords,
  lineups,
  predictedLineups,
  onClose
}) => {
  if (!game) return null;

  const getLineup = (teamId, isHome) => {
    const actualLineup = lineups[game.id]?.[isHome ? 'home' : 'away'];
    const predictedLineup = predictedLineups[game.id]?.[isHome ? 'home' : 'away'];
    return actualLineup || predictedLineup || [];
  };

  const getBbRefLink = (bbrefId) => {
    const firstLetter = bbrefId.charAt(0);
    return `https://www.baseball-reference.com/players/${firstLetter}/${bbrefId}.shtml`;
  };

  return (
    <Drawer
      isOpen={true}
      onClose={onClose}
      title={`${game.awayTeam} @ ${game.homeTeam}`}
      width="500px"
    >
      <div className="game-preview-content">
        <section className="game-info">
          <div className="info-row">
            <span className="label">Time:</span>
            <span>{game.time}</span>
          </div>
          <div className="info-row">
            <span className="label">Venue:</span>
            <span>{game.venue}</span>
          </div>
          <div className="info-row">
            <span className="label">Weather:</span>
            <span>{game.temperature}°F | {game.windDescription}</span>
          </div>
          <div className="info-row">
            <span className="label">Rain Probability:</span>
            <span>{game.rainProbability}%</span>
          </div>
        </section>

        <section className="pitchers-section">
          <h3>Probable Pitchers</h3>
          <div className="pitcher-info">
            <div className="away-pitcher">
              <h4>{game.awayTeam}</h4>
              <a href={getBbRefLink(game.awayPitcher)}
                target="_blank"
                rel="noopener noreferrer">
                {game.awayPitcher}
              </a>
            </div>
            <div className="home-pitcher">
              <h4>{game.homeTeam}</h4>
              <a href={getBbRefLink(game.homePitcher)}
                target="_blank"
                rel="noopener noreferrer">
                {game.homePitcher}
              </a>
            </div>
          </div>
        </section>

        <section className="lineups-section">
          <h3>Lineups</h3>
          <div className="lineups-container">
            <div className="away-lineup">
              <h4>{game.awayTeam}</h4>
              {getLineup(game.awayTeam, false).map((player, index) => (
                <div key={index} className="lineup-player">
                  {index + 1}. {player.name} - {player.position}
                </div>
              ))}
            </div>
            <div className="home-lineup">
              <h4>{game.homeTeam}</h4>
              {getLineup(game.homeTeam, true).map((player, index) => (
                <div key={index} className="lineup-player">
                  {index + 1}. {player.name} - {player.position}
                </div>
              ))}
            </div>
          </div>
        </section>

        {game.previewLink && (
          <section className="preview-link">
            <a href={game.previewLink}
              target="_blank"
              rel="noopener noreferrer"
              className="full-preview-button">
              View Full Preview
            </a>
          </section>
        )}
      </div>
    </Drawer>
  );
};

export default GamePreviewDrawer;