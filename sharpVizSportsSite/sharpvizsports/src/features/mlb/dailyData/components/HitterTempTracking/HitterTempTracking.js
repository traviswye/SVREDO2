// src/features/mlb/components/HitterTempTracking/HitterTempTracking.js
import React from 'react';
import DataBox from '../../../../../components/common/DataBox/DataBox';
import { useHitterTemperatures } from '../../hooks/useHitterTemperatures';
import './HitterTempTracking.css';

const HitterTempTracking = ({ title, subtitle, date }) => {
  const { data, loading, error } = useHitterTemperatures(date);

  const headers = [
    "Date", "Player ID", "Team", "Current Temp",
    "Trailing Temp 1", "Trailing Temp 2", "Trailing Temp 3",
    "Trailing Temp 4", "Trailing Temp 5", "Trailing Temp 6",
    "Park Factor", "G", "PA", "HR", "BA", "OPS",
    "Home Games", "Away Games"
  ];

  const keyHeaders = [
    "date", "bbrefId", "team", "currentTemp",
    "trailingTemp1", "trailingTemp2", "trailingTemp3",
    "trailingTemp4", "trailingTemp5", "trailingTemp6",
    "splitParkFactor", "g", "pa", "hr", "ba", "ops",
    "homeGames", "awayGames"
  ];

  const formatValue = (key, value) => {
    if (key === "bbrefId") {
      return (
        <a
          href={`https://www.baseball-reference.com/players/${value[0]}/${value}.shtml`}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="player-link"
        >
          {value}
        </a>
      );
    }
    if (key === "ba" || key === "ops") {
      return value.toString().padStart(4, '0');
    }
    return value;
  };

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  return (
    <DataBox
      title={title}
      subtitle={subtitle}
      headers={headers}
      keyHeaders={keyHeaders}
      data={data}
      loading={loading}
      formatValue={formatValue}
      defaultSort={{ key: "currentTemp", direction: "desc" }}
      searchEnabled={true}
      searchPlaceholder="Search by Player ID"
      className="hitter-temp-tracking"
    />
  );
};

export default HitterTempTracking;