// src/features/mlb/components/MLBGameCard/MLBGameCard.js
import React from "react";
import GameCard from "../../../../../components/common/GameCard/GameCard";
import "./MLBGameCard.css";

const MLBGameCard = ({ game, homePitcher, awayPitcher, onClick }) => {
    const getBbRefLink = (bbrefId) => {
        const firstLetter = bbrefId.charAt(0);
        return `https://www.baseball-reference.com/players/${firstLetter}/${bbrefId}.shtml`;
    };

    const formatPitcher = (teamAbbreviation, pitcher) => {
        if (!pitcher) {
            return (
                <div className="pitcher-info">
                    <strong>{teamAbbreviation}</strong>: Unannounced
                </div>
            );
        }

        return (
            <div className="pitcher-info">
                <strong>{teamAbbreviation}</strong>:{" "}
                <a
                    href={getBbRefLink(pitcher.bbrefId)}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                >
                    {pitcher.bbrefId}
                </a>{" "}
                <span className="pitcher-stats">
                    {pitcher.throws} | W-L: {pitcher.wl} | ERA: {pitcher.era}
                </span>
            </div>
        );
    };

    const header = (
        <>
            <span className="game-time">{game.time}</span>
            <span className="rain-prob">Rain: {game.rainProbability}%</span>
        </>
    );

    const title = `${game.awayTeam} @ ${game.homeTeam}`;

    const subtitle = `Venue: ${game.venue}`;

    const mainContent = (
        <div className="weather-info">
            Temp: {game.temperature}°F | {game.windDescription}
        </div>
    );

    const additionalContent = (
        <div className="pitchers">
            {formatPitcher(game.awayTeamAbbreviation, awayPitcher)}
            {formatPitcher(game.homeTeamAbbreviation, homePitcher)}
        </div>
    );

    return (
        <GameCard
            header={header}
            title={title}
            subtitle={subtitle}
            mainContent={mainContent}
            additionalContent={additionalContent}
            onClick={() => onClick(game)}
            className="mlb-game-card"
        />
    );
};

export default MLBGameCard;