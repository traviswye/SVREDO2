import React from "react";
import "../css/GameCard.css";

const GameCard = ({ game, homePitcher, awayPitcher, onClick }) => {
  const getBbRefLink = (bbrefId) => {
    const firstLetter = bbrefId.charAt(0);
    return `https://www.baseball-reference.com/players/${firstLetter}/${bbrefId}.shtml`;
  };

  const formatPitcher = (teamAbbreviation, pitcher) => {
    if (!pitcher) {
      return (
        <>
          <strong>{teamAbbreviation}</strong>: Unannounced
        </>
      );
    }

    return (
      <>
        <strong>{teamAbbreviation}</strong>{": "}
        <a
          href={getBbRefLink(pitcher.bbrefId)}
          target="_blank"
          rel="noopener noreferrer"
        >
          {pitcher.bbrefId}
        </a>{" "}
        {pitcher.throws} | W-L: {pitcher.wl} | ERA: {pitcher.era}
      </>
    );
  };

  return (
    <div className="game-card" onClick={() => onClick(game)}>
      <div className="game-header">
        <span>{game.time}</span>
        <span className="rain-prob">Rain: {game.rainProbability}%</span>
      </div>
      <h3>
        {game.awayTeam} @ {game.homeTeam}
      </h3>
      <p>Venue: {game.venue}</p>
      <p>Temp: {game.temperature}°F | {game.windDescription}</p>
      <div className="pitchers">
        <p>{formatPitcher(game.awayTeamAbbreviation, awayPitcher)}</p>
        <p>{formatPitcher(game.homeTeamAbbreviation, homePitcher)}</p>
      </div>
    </div>
  );
};

export default GameCard;
