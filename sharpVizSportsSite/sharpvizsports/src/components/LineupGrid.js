import React from "react";
import "../css/LineupGrid.css";

const LineupGrid = ({ teamName, lineup }) => {
  if (!lineup || !lineup.batting1st) {
    return <p className="empty-lineup">No lineup available for {teamName}</p>;
  }

  const battingOrder = [
    { position: 1, player: lineup.batting1st },
    { position: 2, player: lineup.batting2nd },
    { position: 3, player: lineup.batting3rd },
    { position: 4, player: lineup.batting4th },
    { position: 5, player: lineup.batting5th },
    { position: 6, player: lineup.batting6th },
    { position: 7, player: lineup.batting7th },
    { position: 8, player: lineup.batting8th },
    { position: 9, player: lineup.batting9th },
  ];

  // Function to get Baseball Reference player URL
  const getBbRefURL = (playerID) => {
    if (!playerID || playerID === "N/A") return null;

    // Baseball-Reference URLs are formatted as:
    // https://www.baseball-reference.com/players/[first letter of ID]/[player ID].shtml
    const firstLetter = playerID.charAt(0);
    return `https://www.baseball-reference.com/players/${firstLetter}/${playerID}.shtml`;
  };

  // Function to format player name for display
  const formatPlayerName = (playerID) => {
    if (!playerID || playerID === "N/A") return "TBD";

    // If the player ID contains full name info, use it
    if (playerID.includes(" ")) return playerID;

    // Otherwise just return the ID
    return playerID;
  };

  return (
    <div className="lineup-grid">
      <table className="lineup-table">
        <thead>
          <tr>
            <th className="order-column">#</th>
            <th className="player-column">Player</th>
            <th className="stats-column">Stats</th>
          </tr>
        </thead>
        <tbody>
          {battingOrder.map((slot) => (
            <tr key={slot.position} className={slot.player ? "" : "empty-slot"}>
              <td className="order-cell">{slot.position}</td>
              <td className="player-cell">
                {slot.player ? (
                  <a
                    href={getBbRefURL(slot.player)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="player-link"
                  >
                    {formatPlayerName(slot.player)}
                  </a>
                ) : (
                  <span className="tbd-player">TBD</span>
                )}
              </td>
              <td className="stats-cell">
                <div className="stat-row">
                  <span className="stat-label">AVG:</span>
                  <span className="stat-value">-</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">HR:</span>
                  <span className="stat-value">-</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">OPS:</span>
                  <span className="stat-value">-</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="lineup-source">
        {lineup.source === "predicted" ? (
          <div className="predicted-tag">Predicted Lineup</div>
        ) : (
          <div className="confirmed-tag">Confirmed Lineup</div>
        )}
      </div>
    </div>
  );
};

export default LineupGrid;