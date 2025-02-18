// src/features/mlb/components/MLBLineupGrid/MLBLineupGrid.js
import React from 'react';
import LineupGrid from '../../../../components/common/LineupGrid/LineupGrid';
import { useMLBPlayerStats } from '../../hooks/useMLBPlayerStats';
import './MLBLineupGrid.css';

const MLBLineupGrid = ({
  teamName,
  lineup,
  isPredicted = false,
  playerStats = {},
  loading = false
}) => {
  const headers = [
    '#',
    'Player',
    'Pos',
    'HR',
    'AVG',
    'OPS',
    'L7 AVG',
    'L7 HR',
    'BvP'
  ];

  const getBbRefLink = (bbrefId) => {
    const firstLetter = bbrefId.charAt(0);
    return `https://www.baseball-reference.com/players/${firstLetter}/${bbrefId}.shtml`;
  };

  const formatStat = (value, type) => {
    if (value === undefined || value === null) return '-';
    switch (type) {
      case 'avg':
      case 'ops':
        return value.toFixed(3);
      case 'hr':
        return value;
      default:
        return value;
    }
  };

  const battingOrder = lineup ? [
    lineup.batting1st,
    lineup.batting2nd,
    lineup.batting3rd,
    lineup.batting4th,
    lineup.batting5th,
    lineup.batting6th,
    lineup.batting7th,
    lineup.batting8th,
    lineup.batting9th,
  ] : [];

  const renderCell = (header, player, index) => {
    const stats = playerStats[player?.bbrefId] || {};

    switch (header) {
      case '#':
        return index + 1;
      case 'Player':
        return player?.bbrefId ? (
          <a
            href={getBbRefLink(player.bbrefId)}
            target="_blank"
            rel="noopener noreferrer"
            className="player-link"
          >
            {player.name || player.bbrefId}
          </a>
        ) : player.name || '-';
      case 'Pos':
        return player?.position || '-';
      case 'HR':
        return formatStat(stats.homeRuns, 'hr');
      case 'AVG':
        return formatStat(stats.battingAverage, 'avg');
      case 'OPS':
        return formatStat(stats.ops, 'ops');
      case 'L7 AVG':
        return formatStat(stats.last7GamesAvg, 'avg');
      case 'L7 HR':
        return formatStat(stats.last7GamesHr, 'hr');
      case 'BvP':
        return formatStat(stats.batterVsPitcher, 'avg');
      default:
        return '-';
    }
  };

  return (
    <LineupGrid
      title={`${teamName} ${isPredicted ? 'Predicted ' : ''}Lineup`}
      headers={headers}
      players={battingOrder}
      renderCell={renderCell}
      className="mlb-lineup-grid"
      loading={loading}
      error={!lineup && !loading ? `No lineup available for ${teamName}` : null}
    />
  );
};

export default MLBLineupGrid;