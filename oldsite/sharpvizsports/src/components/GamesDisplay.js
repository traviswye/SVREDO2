import React, { useState, useEffect } from "react";
import GameCard from "./GameCard";
import PreviewDrawer from "./PreviewDrawer"; // Import the new PreviewDrawer component
import "../css/GamesDisplay.css";

const formatDate = (date) => {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const day = date.getDate().toString().padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const GamesDisplay = ({ initialDate }) => {
  const [games, setGames] = useState([]);
  const [pitchers, setPitchers] = useState({});
  const [teamRecords, setTeamRecords] = useState({});
  const [lineups, setLineups] = useState({});
  const [predictedLineups, setPredictedLineups] = useState({});
  const [ParkFactorRecords, setParkFactorRecords] = useState({});

  const [selectedDate, setSelectedDate] = useState(
    initialDate ? formatDate(new Date(initialDate)) : formatDate(new Date())
  );
  const [selectedGame, setSelectedGame] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    console.log("Selected Date (Displayed):", selectedDate);
    fetchData(selectedDate);
    fetchStaticData(selectedDate);
  }, [selectedDate]);

  const teamAbbreviations = {
    Phillies: "PHI",
    "Blue Jays": "TOR",
    Cubs: "CHC",
    Athletics: "OAK",
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
      const shortDate = date.substring(2); // Convert to 'YY-MM-DD'
      console.log("Fetching data for:", shortDate);

      const gamesResponse = await fetch(
        `https://localhost:44346/api/GamePreviews/${shortDate}`
      );
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
      const pitchersData = await pitchersResponse.json();

      const pitchersMap = pitchersData.reduce((map, pitcher) => {
        if (!map[pitcher.bbrefId] || map[pitcher.bbrefId].year < pitcher.year) {
          map[pitcher.bbrefId] = pitcher;
        }
        return map;
      }, {});

      setPitchers(pitchersMap);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const fetchStaticData = async (date) => {
    try {
      console.log("Fetching static data...");

      // Fetch Team Records
      const teamRecordsResponse = await fetch("https://localhost:44346/api/TeamRecSplits");
      const teamRecordsData = await teamRecordsResponse.json();
      setTeamRecords(teamRecordsData);

      // Fetch Team Records
      const parkFactorsResponse = await fetch("https://localhost:44346/api/ParkFactors");
      const parkFactorsData = await parkFactorsResponse.json();
      setParkFactorRecords(parkFactorsData);

      // Fetch Actual Lineups
      const lineupsResponse = await fetch(`https://localhost:44346/api/Lineups/Actual/${date}`);
      const lineupsData = await lineupsResponse.json();
      setLineups(lineupsData);

      // Fetch Predicted Lineups
      const predictedLineupsResponse = await fetch(
        `https://localhost:44346/api/Lineups/Predictions/date/${date}`
      );
      const predictedLineupsData = await predictedLineupsResponse.json();
      setPredictedLineups(predictedLineupsData);
    } catch (error) {
      console.error("Error fetching static data:", error);
    }
  };

  const handleDateChange = (e) => {
    const inputDate = e.target.value;
    console.log("Date Selected from Input (Raw):", inputDate);
    setSelectedDate(inputDate);
  };

  const incrementDate = (days) => {
    setSelectedDate((prevDate) => {
      const parsedDate = new Date(`${prevDate}T00:00:00`);
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
      <div className="date-picker">
        <button onClick={() => incrementDate(-1)}>&lt; Prev</button>
        <input
          type="date"
          value={selectedDate}
          onChange={handleDateChange}
        />
        <button onClick={() => incrementDate(1)}>Next &gt;</button>
      </div>
      <div className="games-list">{renderGameCards()}</div>
      {drawerOpen && (
        <PreviewDrawer
          game={selectedGame}
          parkFactors={ParkFactorRecords}
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
