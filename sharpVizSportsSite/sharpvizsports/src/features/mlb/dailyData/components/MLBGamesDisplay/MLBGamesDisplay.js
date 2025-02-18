// src/features/mlb/components/MLBGamesDisplay/MLBGamesDisplay.js
import React, { useState } from 'react';
import GamesDisplay from '../../../../../components/common/GamesDisplay/GamesDisplay';
import DatePicker from '../../../../../components/common/DatePicker/DatePicker';
import MLBGameCard from '../MLBGameCard/MLBGameCard';
import GamePreviewDrawer from '../GamePreviewDrawer/GamePreviewDrawer';
import { useMLBGames } from '../../hooks/useMLBGames';
import { useMLBStaticData } from '../../hooks/useMLBStaticData';
import { formatDate } from '../../../utils/dateUtils';
import './MLBGamesDisplay.css';

const MLBGamesDisplay = ({ initialDate }) => {
  const [selectedDate, setSelectedDate] = useState(
    initialDate ? formatDate(new Date(initialDate)) : formatDate(new Date())
  );
  const [selectedGame, setSelectedGame] = useState(null);

  const { games, pitchers, loading: gamesLoading } = useMLBGames(selectedDate);
  const {
    teamRecords,
    parkFactors,
    lineups,
    predictedLineups,
    loading: staticDataLoading
  } = useMLBStaticData(selectedDate);

  const handleDateChange = (date) => {
    setSelectedDate(date);
  };

  const incrementDate = (days) => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + days);
    setSelectedDate(formatDate(newDate));
  };

  const handleCardClick = (game) => {
    setSelectedGame(game);
  };

  if (gamesLoading || staticDataLoading) {
    return <div className="loading-spinner">Loading...</div>;
  }

  return (
    <GamesDisplay
      datePicker={
        <DatePicker
          selectedDate={selectedDate}
          onChange={handleDateChange}
          onPrevious={() => incrementDate(-1)}
          onNext={() => incrementDate(1)}
        />
      }
      className="mlb-games-display"
    >
      {games.map((game) => (
        <MLBGameCard
          key={game.id}
          game={game}
          homePitcher={pitchers[game.homePitcher]}
          awayPitcher={pitchers[game.awayPitcher]}
          onClick={() => handleCardClick(game)}
        />
      ))}

      {selectedGame && (
        <GamePreviewDrawer
          game={selectedGame}
          parkFactors={parkFactors}
          teamRecords={teamRecords}
          lineups={lineups}
          predictedLineups={predictedLineups}
          onClose={() => setSelectedGame(null)}
        />
      )}
    </GamesDisplay>
  );
};

export default MLBGamesDisplay;