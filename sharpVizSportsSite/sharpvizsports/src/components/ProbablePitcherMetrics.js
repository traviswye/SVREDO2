import React, { useEffect, useState } from "react";
import "../css/DataBox.css";

// Helper functions
const formatDate = (date) => date.split("T")[0];

const extractPercentage = (message) => {
  if (!message || message.includes("No data available")) {
    return 0; // Default to 0 if no percentage found or data is unavailable
  }
  const match = message.match(/([-+]?\d+(\.\d+)?)%/);
  return match ? parseFloat(match[1]) : 0;
};

const extractStatus = (message) => {
  if (!message || message.includes("No data available")) {
    return "Unknown";
  }
  if (message.includes("COLD")) return "COLD";
  if (message.includes("HOT")) return "HOT";
  if (message.includes("CONSISTENT")) return "CONSISTENT";
  return "Unknown";
};

const getTooltipIcon = (message) => {
  if (!message || message.includes("No data available")) {
    return (
      <span title="No data available" role="img" aria-label="Unknown">
        🚫
      </span>
    );
  }

  if (message.includes("COLD")) {
    return <span title={message} role="img" aria-label="Cold">❄️</span>;
  }

  if (message.includes("HOT")) {
    return <span title={message} role="img" aria-label="Hot">🔥</span>;
  }

  if (message.includes("CONSISTENT")) {
    if (message.includes("better")) {
      return <span title={message} role="img" aria-label="Consistent Positive">🔴</span>;
    }
    if (message.includes("worse")) {
      return <span title={message} role="img" aria-label="Consistent Negative">🔵</span>;
    }
    return <span title={message} role="img" aria-label="Neutral">⚪</span>;
  }

  return (
    <span title="No data available" role="img" aria-label="Unknown">
      🚫
    </span>
  );
};

const ProbablePitcherMetrics = ({ title, subtitle, date }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: "time", direction: "asc" });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [gamePreviewsResponse, pitcherTrendsResponse] = await Promise.all([
          fetch(`https://localhost:44346/api/GamePreviews/${date}`),
          fetch(`https://localhost:44346/api/Blending/todaysSPHistoryVsRecency?date=20${date}`),
        ]);
  
        const gamePreviews = await gamePreviewsResponse.json();
        const pitcherTrends = await pitcherTrendsResponse.json();
  
        // Collect all bbrefId's
        const bbrefIds = [
          ...new Set(
            gamePreviews.flatMap((game) => [game.homePitcher, game.awayPitcher])
          ),
        ];
  
        // Make a batch request for full names
        const playerNamesResponse = await fetch(
          `https://localhost:44346/api/mlbplayer/batch`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(bbrefIds),
          }
        );
        const playerNames = await playerNamesResponse.json(); // Should return a dictionary { bbrefId: fullName }
  
        // Create a lookup for pitcher trends
        const trendsLookup = pitcherTrends.reduce((acc, trend) => {
          const hasMessage = trend.message && trend.message.trim();
          acc[trend.pitcher] = hasMessage
            ? trend
            : { performanceStatus: "Unknown", message: "No data available" };
          return acc;
        }, {});
  
        // Merge data
        const mergedData = gamePreviews.map((game) => {
          const homePitcherTrend = trendsLookup[game.homePitcher] || {
            performanceStatus: "N/A",
            message: "No data available",
          };
          const awayPitcherTrend = trendsLookup[game.awayPitcher] || {
            performanceStatus: "N/A",
            message: "No data available",
          };
  
          return {
            date: formatDate(game.date),
            time: game.time,
            homeTeam: game.homeTeam,
            awayTeam: game.awayTeam,
            venue: game.venue,
            homePitcher: playerNames[game.homePitcher] || game.homePitcher, // Use full name if available
            homePitcherMessage: homePitcherTrend.message,
            homePitcherStatus: extractStatus(homePitcherTrend.message),
            awayPitcher: playerNames[game.awayPitcher] || game.awayPitcher, // Use full name if available
            awayPitcherMessage: awayPitcherTrend.message,
            awayPitcherStatus: extractStatus(awayPitcherTrend.message),
            homePercentage: extractPercentage(homePitcherTrend.message),
            awayPercentage: extractPercentage(awayPitcherTrend.message),
            previewLink: game.previewLink, // Add the preview link here
          };
        });
  
        setData(mergedData);
      } catch (error) {
        setError("Failed to fetch data.");
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
  
    fetchData();
  }, [date]);  

  const handleSort = (key) => {
    const direction = sortConfig.key === key && sortConfig.direction === "asc" ? "desc" : "asc";
    setSortConfig({ key, direction });

    const sortedData = [...data].sort((a, b) => {
      if (key === "homePercentage" || key === "awayPercentage") {
        return direction === "asc" ? a[key] - b[key] : b[key] - a[key];
      } else {
        return direction === "asc"
          ? a[key].localeCompare(b[key])
          : b[key].localeCompare(a[key]);
      }
    });

    setData(sortedData);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="data-box-container">
      <div className="data-box-header">
        <div>
        <div className="data-box-title">{title}</div>
        <div className="data-box-subtitle">{subtitle}</div>
        </div>
      </div>
      <div className="data-box-scrollable">
        <table className="data-box-table">
          <thead>
            <tr>
              <th onClick={() => handleSort("date")}>Date</th>
              <th onClick={() => handleSort("time")}>Time</th>
              <th onClick={() => handleSort("homeTeam")}>Home Team</th>
              <th onClick={() => handleSort("awayTeam")}>Away Team</th>
              <th>Venue</th>
              <th>Home Pitcher</th>
              <th>Pitcher Status</th>
              <th onClick={() => handleSort("homePercentage")}>Home %</th>
              <th>Away Pitcher</th>
              <th>Pitcher Status</th>
              <th onClick={() => handleSort("awayPercentage")}>Away %</th>
            </tr>
          </thead>
          <tbody>
  {data.map((row, index) => (
    <tr key={index}>
      <td>
        <a
          href={row.previewLink} // Add the preview link
          target="_blank" // Open in a new tab
          rel="noopener noreferrer" // Ensure security
        >
          {row.date}
        </a>
      </td>
      <td>{row.time}</td>
      <td>{row.homeTeam}</td>
      <td>{row.awayTeam}</td>
      <td>{row.venue}</td>
      <td>{row.homePitcher}</td>
      <td>{row.homePitcherStatus}</td>
      <td>{getTooltipIcon(row.homePitcherMessage)}</td>
      <td>{row.awayPitcher}</td>
      <td>{row.awayPitcherStatus}</td>
      <td>{getTooltipIcon(row.awayPitcherMessage)}</td>
    </tr>
  ))}
</tbody>

        </table>
      </div>
    </div>
  );
};

export default ProbablePitcherMetrics;
