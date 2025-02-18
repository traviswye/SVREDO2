import React from "react";
import "../css/LineupGrid.css";

const LineupGrid = ({ teamName, lineup }) => {
  if (!lineup || !lineup.batting1st) return <p>No lineup available for {teamName}</p>;

  const battingOrder = [
    lineup.batting1st,
    lineup.batting2nd,
    lineup.batting3rd,
    lineup.batting4th,
    lineup.batting5th,
    lineup.batting6th,
    lineup.batting7th,
    lineup.batting8th,
    lineup.batting9th,
  ];

  return (
    <div className="lineup-grid">
      <h4>{teamName} Lineup</h4>
      <table className="lineup-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Player</th>
            <th>HR</th>
            <th>AVG</th>
            <th>Last7G AVG</th>
            <th>Last7G HR</th>
          </tr>
        </thead>
        <tbody>
          {battingOrder.map((player, index) => (
            <tr key={index}>
              <td>{index + 1}</td>
              <td>{player}</td>
              <td>-</td> {/* Placeholder for HR */}
              <td>-</td> {/* Placeholder for AVG */}
              <td>-</td> {/* Placeholder for Last7G AVG */}
              <td>-</td> {/* Placeholder for Last7G HR */}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LineupGrid;
