import React, { useState, useEffect } from "react";
import GameCard from "./GameCard";
import PreviewDrawer from "./PreviewDrawer";
import "../css/GamesDisplay.css";

const GamesDisplay = ({ initialDate }) => {
  // Format date as YYYY-MM-DD
  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  // Format date as YY-MM-DD for API calls
  const formatDateForApi = (dateString) => {
    // Extract the last two digits of the year for API calls
    const parts = dateString.split('-');
    if (parts.length === 3) {
      const shortYear = parts[0].slice(-2); // Get last 2 digits of year
      return `${shortYear}-${parts[1]}-${parts[2]}`;
    }
    return dateString;
  };

  const [games, setGames] = useState([]);
  const [pitchers, setPitchers] = useState({});
  const [teamRecords, setTeamRecords] = useState({});
  const [lineups, setLineups] = useState({});
  const [predictedLineups, setPredictedLineups] = useState({});
  const [parkFactorRecords, setParkFactorRecords] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize selectedDate with current date if no initialDate provided
  const [selectedDate, setSelectedDate] = useState(
    initialDate ? formatDate(new Date(initialDate)) : formatDate(new Date())
  );
  const [selectedGame, setSelectedGame] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    console.log("Selected Date for display:", selectedDate);
    const fetchAllData = async () => {
      setLoading(true);
      setError(null);
      try {
        await fetchData(selectedDate);
        await fetchStaticData(selectedDate);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("Failed to load game data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
  }, [selectedDate]);

  const teamAbbreviations = {
    Phillies: "PHI",
    "Blue Jays": "TOR",
    Cubs: "CHC",
    Athletics: "ATH",
    Rockies: "COL",
    Diamondbacks: "ARI",
    Angels: "LAA",
    "White Sox": "CHW",
    Orioles: "BAL",
    Giants: "SFG",
    Reds: "CIN",
    Braves: "ATL",
    Guardians: "CLE",
    Twins: "MIN",
    Marlins: "MIA",
    Dodgers: "LAD",
    Padres: "SDP",
    Astros: "HOU",
    Rays: "TBR",
    "Red Sox": "BOS",
    Mets: "NYM",
    Nationals: "WSH",
    Royals: "KCR",
    Tigers: "DET",
    Brewers: "MIL",
    Cardinals: "STL",
    Pirates: "PIT",
    Rangers: "TEX",
    Mariners: "SEA",
    Yankees: "NYY",
  };

  const getTeamAbbreviation = (teamName) => teamAbbreviations[teamName] || "UNK";

  const fetchData = async (date) => {
    try {
      const shortDate = formatDateForApi(date); // Convert to 'YY-MM-DD'
      console.log("Fetching game data for:", shortDate);

      const gamesResponse = await fetch(
        `https://localhost:44346/api/GamePreviews/${shortDate}`
      );

      if (!gamesResponse.ok) {
        throw new Error(`Games API responded with status: ${gamesResponse.status}`);
      }

      const gamesData = await gamesResponse.json();

      const uniqueGames = Array.from(
        new Set(gamesData.map((game) => game.id))
      ).map((id) => gamesData.find((game) => game.id === id));

      setGames(
        uniqueGames.map((game) => ({
          ...game,
          awayTeamAbbreviation: getTeamAbbreviation(game.awayTeam),
          homeTeamAbbreviation: getTeamAbbreviation(game.homeTeam),
        }))
      );

      const pitchersResponse = await fetch(
        `https://localhost:44346/api/Pitchers/pitchersByDate/${shortDate}`
      );

      if (!pitchersResponse.ok) {
        console.warn(`Pitchers API responded with status: ${pitchersResponse.status}`);
        setPitchers({});
        return;
      }

      const pitchersData = await pitchersResponse.json();

      const pitchersMap = pitchersData.reduce((map, pitcher) => {
        if (!map[pitcher.bbrefId] || map[pitcher.bbrefId].year < pitcher.year) {
          map[pitcher.bbrefId] = pitcher;
        }
        return map;
      }, {});

      setPitchers(pitchersMap);
    } catch (error) {
      console.error("Error fetching game data:", error);
      setError("Failed to load games. Please try again later.");
      setGames([]);
      setPitchers({});
    }
  };

  const fetchStaticData = async (date) => {
    try {
      console.log("Fetching static data...");

      // Fetch Team Records
      const teamRecordsResponse = await fetch("https://localhost:44346/api/TeamRecSplits");
      const teamRecordsData = await teamRecordsResponse.json();
      setTeamRecords(teamRecordsData);

      // Fetch Park Factors
      const parkFactorsResponse = await fetch("https://localhost:44346/api/ParkFactors");
      const parkFactorsData = await parkFactorsResponse.json();
      setParkFactorRecords(parkFactorsData);

      // Fetch Actual Lineups
      const lineupsResponse = await fetch(`https://localhost:44346/api/Lineups/Actual/${date}`);
      if (lineupsResponse.ok) {
        const lineupsData = await lineupsResponse.json();
        setLineups(lineupsData);
      } else {
        console.warn("No actual lineups found for the selected date");
        setLineups({});
      }

      // Fetch Predicted Lineups
      const predictedLineupsResponse = await fetch(
        `https://localhost:44346/api/Lineups/Predictions/date/${date}`
      );
      if (predictedLineupsResponse.ok) {
        const predictedLineupsData = await predictedLineupsResponse.json();
        setPredictedLineups(predictedLineupsData);
      } else {
        console.warn("No predicted lineups found for the selected date");
        setPredictedLineups({});
      }
    } catch (error) {
      console.error("Error fetching static data:", error);
      setError("Failed to load supporting data. Some information may be missing.");
    }
  };

  const handleDateChange = (e) => {
    const inputDate = e.target.value;
    console.log("Date Selected from Input:", inputDate);
    setSelectedDate(inputDate);
  };

  const incrementDate = (days) => {
    setSelectedDate((prevDate) => {
      const parsedDate = new Date(`${prevDate}T12:00:00`); // Use noon to avoid timezone issues
      parsedDate.setDate(parsedDate.getDate() + days);
      return formatDate(parsedDate);
    });
  };

  const handleCardClick = (game) => {
    setSelectedGame(game);
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setSelectedGame(null);
  };

  const renderGameCards = () => {
    if (loading) {
      return <div className="loading-message">Loading games data...</div>;
    }

    if (error) {
      return <div className="error-message">{error}</div>;
    }

    if (games.length === 0) {
      return <div className="no-games-message">No games scheduled for this date.</div>;
    }

    return games.map((game) => {
      const homePitcher = pitchers[game.homePitcher];
      const awayPitcher = pitchers[game.awayPitcher];

      return (
        <GameCard
          key={game.id}
          game={game}
          homePitcher={homePitcher}
          awayPitcher={awayPitcher}
          onClick={() => handleCardClick(game)}
        />
      );
    });
  };

  return (
    <div className="games-display">
      <div className="date-picker-container">
        <button
          onClick={() => incrementDate(-1)}
          className="date-nav-button prev-button"
        >
          &lt; Previous Day
        </button>
        <input
          type="date"
          value={selectedDate}
          onChange={handleDateChange}
          className="date-input"
        />
        <button
          onClick={() => incrementDate(1)}
          className="date-nav-button next-button"
        >
          Next Day &gt;
        </button>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading games...</p>
        </div>
      ) : (
        <div className="games-list">{renderGameCards()}</div>
      )}

      {drawerOpen && (
        <PreviewDrawer
          game={selectedGame}
          parkFactors={parkFactorRecords}
          teamRecords={teamRecords}
          lineups={lineups}
          predictedLineups={predictedLineups}
          onClose={closeDrawer}
        />
      )}
    </div>
  );
};

export default GamesDisplay;