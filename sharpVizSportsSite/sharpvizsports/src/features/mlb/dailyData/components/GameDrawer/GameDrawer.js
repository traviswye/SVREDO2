import React from "react";
import "../css/GameDrawer.css";

const GameDrawer = ({ game, onClose }) => {
  if (!game) return null;

  return (
    <div className="drawer-overlay">
      <div className="drawer">
        <button className="close-button" onClick={onClose}>
          Close
        </button>
        <h2>{game.awayTeam} @ {game.homeTeam}</h2>
        <p><strong>Time:</strong> {game.time}</p>
        <p><strong>Venue:</strong> {game.venue}</p>
        <p><strong>Temperature:</strong> {game.temperature}°F</p>
        <p><strong>Wind:</strong> {game.windDescription}</p>
        <p><strong>Rain Probability:</strong> {game.rainProbability}%</p>
        <p>
          <strong>Pitchers:</strong>
          <br />
          <a
            href={`https://www.baseball-reference.com/players/${game.awayPitcher.charAt(0)}/${game.awayPitcher}.shtml`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {game.awayPitcher}
          </a> (Away)
          <br />
          <a
            href={`https://www.baseball-reference.com/players/${game.homePitcher.charAt(0)}/${game.homePitcher}.shtml`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {game.homePitcher}
          </a> (Home)
        </p>
        <a
          href={game.previewLink}
          target="_blank"
          rel="noopener noreferrer"
        >
          Full Preview
        </a>
      </div>
    </div>
  );
};

export default GameDrawer;
