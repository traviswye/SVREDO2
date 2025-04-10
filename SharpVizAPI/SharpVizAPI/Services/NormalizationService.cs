using System.Linq;
using System.Threading.Tasks;
using SharpVizAPI.Models;
using SharpVizAPI.Data;
using Microsoft.EntityFrameworkCore;

namespace SharpVizAPI.Services
{

    public class NormalizationService
    {
        private readonly NrfidbContext _context;

        private readonly Dictionary<string, string> _teamAbbreviationMap = new Dictionary<string, string>
    {
        { "MIL", "Brewers" },
        { "SFG", "Giants" },
        { "CIN", "Reds" },
        { "ATL", "Braves" },
        { "LAD", "Dodgers" },
        { "STL", "Cardinals" },
        { "PHI", "Phillies" },
        { "MIA", "Marlins" },
        { "CLE", "Guardians" },
        { "WSN", "Nationals" },
        { "TEX", "Rangers" },
        { "CHC", "Cubs" },
        { "PIT", "Pirates" },
        { "NYY", "Yankees" },
        { "LAA", "Angels" },
        { "COL", "Rockies" },
        { "SEA", "Mariners" },
        { "SDP", "Padres" },
        { "ARI", "Diamondbacks" },
        { "CHW", "White Sox" },
        { "TOR", "Blue Jays" },
        { "TBR", "Rays" },
        // Add other mappings as needed
        { "NYM", "Mets" },
        { "BAL", "Orioles" },
        { "OAK", "Athletics" },
        { "ATH", "Athletics" },
        { "KCR", "Royals" },
        { "BOS", "Red Sox" },
        { "DET", "Tigers" },
        { "HOU", "Astros" },
        { "MIN", "Twins" }
    };

        public NormalizationService(NrfidbContext context)
        {
            _context = context;
        }
        public async Task<NormalizeResult> NormalizeParkFactors(string bbrefId, List<string> oppIds, int homeGames)
        {
            // Fetch hitter data by bbrefId
            var hitter = await _context.Hitters.FirstOrDefaultAsync(h => h.bbrefId == bbrefId);
            if (hitter == null)
            {
                throw new Exception("Hitter not found.");
            }

            // Get hitter's team and find its home park factor
            if (!_teamAbbreviationMap.ContainsKey(hitter.Team))
            {
                throw new Exception($"Team abbreviation {hitter.Team} does not have a corresponding full team name mapping.");
            }

            var fullTeamName = _teamAbbreviationMap[hitter.Team];

            var homeParkFactor = await _context.ParkFactors
                .Where(p => p.Team == fullTeamName)
                .Select(p => p.ParkFactorRating)
                .FirstOrDefaultAsync();

            if (homeParkFactor == 0)
            {
                throw new Exception("Home park factor not found.");
            }

            double avgAwayParkFactor = 0;

            // If oppIds is not empty, calculate avgAwayParkFactor
            if (oppIds != null && oppIds.Any())
            {
                // Validate that all oppIds have a mapping
                if (!oppIds.All(opp => _teamAbbreviationMap.ContainsKey(opp)))
                {
                    throw new Exception("One or more opponent IDs do not have a corresponding team name mapping.");
                }

                // Map oppIds to full team names
                var fullTeamNames = oppIds
                    .Select(opp => _teamAbbreviationMap[opp])
                    .ToList();

                // Get park factors for away teams
                var awayParkFactors = await _context.ParkFactors
                    .Where(p => fullTeamNames.Contains(p.Team))
                    .Select(p => new { p.Team, p.ParkFactorRating })
                    .ToListAsync();

                if (awayParkFactors.Any())
                {
                    // Map oppIds to park factor ratings
                    var parkFactorValues = oppIds
                        .Select(opp => awayParkFactors.FirstOrDefault(pf => pf.Team == _teamAbbreviationMap[opp])?.ParkFactorRating ?? 0)
                        .ToList();

                    if (parkFactorValues.Any(pf => pf == 0))
                    {
                        throw new Exception("Missing park factor for one or more away teams.");
                    }

                    avgAwayParkFactor = parkFactorValues.Average();
                }
            }

            // Calculate total number of games
            int totalGames = homeGames + (oppIds?.Count ?? 0);

            // Calculate weights
            double weightForHome = (double)homeGames / totalGames;
            double weightForAway = (double)(oppIds?.Count ?? 0) / totalGames;

            // Calculate total park factor
            var totalParkFactor = weightForHome * homeParkFactor + weightForAway * avgAwayParkFactor;

            return new NormalizeResult
            {
                AvgAwayParkFactor = avgAwayParkFactor,
                HomeParkFactor = homeParkFactor,
                TotalParkFactor = totalParkFactor
            };
        }
        public async Task<double> AdjustValueByParkFactor(double value, string teamAbbreviation)
        {
            // Check if the team abbreviation exists in the mapping
            if (!_teamAbbreviationMap.ContainsKey(teamAbbreviation))
            {
                throw new Exception($"Team abbreviation {teamAbbreviation} does not have a corresponding full team name mapping.");
            }

            // Get the full team name from the mapping
            var fullTeamName = _teamAbbreviationMap[teamAbbreviation];

            // Retrieve the park factor for the team
            var parkFactor = await _context.ParkFactors
                .Where(p => p.Team == fullTeamName)
                .Select(p => p.ParkFactorRating)
                .FirstOrDefaultAsync();

            // Handle missing park factors
            if (parkFactor == 0)
            {
                throw new Exception($"Park factor not found or is zero for team {teamAbbreviation} ({fullTeamName}).");
            }

            // Log the retrieved park factor for debugging
            Console.WriteLine($"Park factor for {fullTeamName} ({teamAbbreviation}): {parkFactor}");

            // Adjust the value based on the park factor
            double adjustedValue = value * (parkFactor / 100.0);
            Console.WriteLine($"adjusted for: {parkFactor}. Your new value should be {adjustedValue}");

            return adjustedValue;
        }



    }

    public class NormalizeResult
    {
        public double AvgAwayParkFactor { get; set; }
        public double HomeParkFactor { get; set; }
        public double TotalParkFactor { get; set; }
    }

}
