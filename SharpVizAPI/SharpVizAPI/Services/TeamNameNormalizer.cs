public static class TeamNameNormalizer
{
    private static readonly Dictionary<string, string> TeamNameMapping = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
    {
        { "D-backs", "Diamondbacks" },
        { "D'backs", "Diamondbacks" },
        { "dbacks", "Diamondbacks" },
        { "diamondbacks", "Diamondbacks" },
        // Add more mappings as needed


                // City abbreviations
        //{ "Atl", "Braves" },
        { "ATL", "Braves" },
        //{ "Bos", "Red Sox" },
        { "BOS", "Red Sox" },
        { "NYY", "Yankees" },
        //{ "Nyy", "Yankees" },
        //{ "NYM", "Mets" },
        //{ "ChC", "Cubs" },
        { "CHC", "Cubs" },
        //{ "ChW", "White Sox" },
        { "CHW", "White Sox" },
        { "CWS", "White Sox" },
        //{ "Cle", "Guardians" },
        { "CLE", "Guardians" },
        //{ "Det", "Tigers" },
        { "DET", "Tigers" },
        //{ "Hou", "Astros" },
        { "HOU", "Astros" },
        { "KC", "Royals" },
        { "KCR", "Royals" },
        { "LA", "Dodgers" },
        { "LAD", "Dodgers" },
        { "LAA", "Angels" },
        //{ "MIA", "Marlins" },
        { "MIA", "Marlins" },
        //{ "Mil", "Brewers" },
        { "MIL", "Brewers" },
        //{ "Min", "Twins" },
        { "MIN", "Twins" },
        { "NYM", "Mets" },
        //{ "Oak", "Athletics" },
        { "OAK", "Athletics" },
        //{ "Phi", "Phillies" },
        { "PHI", "Phillies" },
        //{ "Pit", "Pirates" },
        { "PIT", "Pirates" },
        { "SD", "Padres" },
        { "SDP", "Padres" },
        { "SEA", "Mariners" },
        { "SF", "Giants" },
        { "SFG", "Giants" },
        { "STL", "Cardinals" },
        { "TB", "Rays" },
        { "TBR", "Rays" },
        //{ "Tex", "Rangers" },
        { "TEX", "Rangers" },
        //{ "Tor", "Blue Jays" },
        { "TOR", "Blue Jays" },
        //{ "Was", "Nationals" },
        { "WAS", "Nationals" },
        { "WSH", "Nationals" },
    };

    public static string NormalizeTeamName(string teamName)
    {
        if (string.IsNullOrEmpty(teamName))
            return teamName;

        if (TeamNameMapping.TryGetValue(teamName, out string normalizedName))
        {
            return normalizedName;
        }

        return teamName; // Return the original name if no match is found
    }
}
