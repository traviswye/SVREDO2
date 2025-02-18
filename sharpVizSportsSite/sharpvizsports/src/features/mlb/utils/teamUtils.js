// src/features/mlb/utils/teamUtils.js
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

export const getTeamAbbreviation = (teamName) => teamAbbreviations[teamName] || "UNK";

export const getTeamFullName = (abbreviation) => {
    const entry = Object.entries(teamAbbreviations).find(([_, abbr]) => abbr === abbreviation);
    return entry ? entry[0] : "Unknown";
};

export const getAllTeams = () => Object.keys(teamAbbreviations);