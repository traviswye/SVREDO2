using SharpVizAPI.Data;
using SharpVizAPI.Models;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Net.Http;
using SharpVizAPI.DTO;
using Microsoft.Extensions.Logging;

namespace SharpVizAPI.Services
{


    public class SimulationService
    {
        private readonly NrfidbContext _context;
        private readonly HttpClient _httpClient;
        private readonly ILogger<SimulationService> _logger;
        private const double SingleRunValue = 0.47;
        private const double TripleRunValue = 1.051;
        private const double DoubleRunValue = 0.776;
        private const double HomeRunValue = 1.377;
        private const double WalkRunValue = 0.222;
        private const double StrikeoutRunValue = -0.25;
        private const double flyoutRunValue = -0.097;
        private const double groundOutRunValue = -0.15;


        public async Task<object> SimulateGames(string date)
        {
            try
            {
                _logger.LogInformation("Simulating games...");

                _logger.LogInformation("Querying GamePreviews for date: {date}");
                var gamePreviews = await _context.GamePreviews
                    .Where(g => g.Date.Date == DateTime.Parse(date).Date)
                    .ToListAsync();

                if (gamePreviews == null || gamePreviews.Count == 0)
                {
                    _logger.LogWarning("No game previews found.");
                    return null;
                }

                _logger.LogInformation($"Found {gamePreviews.Count} game previews for date: {date}");

                var results = new List<object>();

                foreach (var game in gamePreviews)
                {
                    _logger.LogInformation($"Processing game: {game.HomeTeam} vs {game.AwayTeam}");

                    // Get the lineups (Actual or Predicted based on null check) for both home and away teams
                    var homeLineup = await GetLineupForTeam(game.Id, game.HomeTeam, true);
                    var awayLineup = await GetLineupForTeam(game.Id, game.AwayTeam, false);

                    // Check if lineups were fetched successfully
                    if (homeLineup.Lineup == null || awayLineup.Lineup == null)
                    {
                        _logger.LogWarning($"Failed to retrieve lineups for {game.HomeTeam} vs {game.AwayTeam}");
                        continue;
                    }

                    // Fetch pitcher stats
                    var homePitcherStats = await _context.Pitchers
                        .Where(p => p.BbrefId == game.HomePitcher || game.HomePitcher == "Unannounced")
                        .FirstOrDefaultAsync();

                    if (homePitcherStats == null)
                    {
                        _logger.LogWarning($"Home pitcher {game.HomePitcher} does not have stats... using average starter stats.");
                        homePitcherStats = await _context.Pitchers
                            .Where(p => p.BbrefId == "Unannounced")
                            .FirstOrDefaultAsync();
                    }

                    var awayPitcherStats = await _context.Pitchers
                        .Where(p => p.BbrefId == game.AwayPitcher || game.AwayPitcher == "Unannounced")
                        .FirstOrDefaultAsync();

                    if (awayPitcherStats == null)
                    {
                        _logger.LogWarning($"Away pitcher {game.AwayPitcher} does not have stats... using average starter stats.");
                        awayPitcherStats = await _context.Pitchers
                            .Where(p => p.BbrefId == "Unannounced")
                            .FirstOrDefaultAsync();
                    }

                    _logger.LogInformation("Fetched season pitcher stats.");

                    var homePitcherFirstInningStats = await _context.Pitcher1stInnings
                        .Where(p => p.BbrefId == game.HomePitcher || game.HomePitcher == "Unannounced")
                        .FirstOrDefaultAsync();

                    if (homePitcherFirstInningStats == null)
                    {
                        _logger.LogWarning($"Home pitcher {game.HomePitcher} does not have first inning stats... using average first inning stats.");
                        homePitcherFirstInningStats = await _context.Pitcher1stInnings
                            .Where(p => p.BbrefId == "Unannounced")
                            .FirstOrDefaultAsync();
                    }

                    var awayPitcherFirstInningStats = await _context.Pitcher1stInnings
                        .Where(p => p.BbrefId == game.AwayPitcher || game.AwayPitcher == "Unannounced")
                        .FirstOrDefaultAsync();

                    if (awayPitcherFirstInningStats == null)
                    {
                        _logger.LogWarning($"Away pitcher {game.AwayPitcher} does not have first inning stats... using average first inning stats.");
                        awayPitcherFirstInningStats = await _context.Pitcher1stInnings
                            .Where(p => p.BbrefId == "Unannounced")
                            .FirstOrDefaultAsync();
                    }

                    _logger.LogInformation("Fetched first inning pitcher stats.");

                    if (homePitcherStats == null || awayPitcherStats == null)
                    {
                        _logger.LogWarning($"Failed to retrieve pitcher stats for {game.HomeTeam} or {game.AwayTeam}");
                        continue;
                    }

                    // Fetch hitter stats for both lineups
                    var (homeHittersStats, homeMissingHitters) = await GetHittersStatsForLineup(homeLineup.Lineup);
                    var (awayHittersStats, awayMissingHitters) = await GetHittersStatsForLineup(awayLineup.Lineup);

                    if (homeHittersStats == null || awayHittersStats == null)
                    {
                        _logger.LogWarning($"Failed to retrieve hitter stats for {game.HomeTeam} or {game.AwayTeam}");
                        continue;
                    }

                    // Run the simulation
                    double homeAverageRuns = SimulateGame(50000, homeHittersStats, homePitcherFirstInningStats);
                    double awayAverageRuns = SimulateGame(50000, awayHittersStats, awayPitcherFirstInningStats);

                    _logger.LogInformation($"Simulated game between {game.HomeTeam} and {game.AwayTeam}: Home Avg Runs = {homeAverageRuns}, Away Avg Runs = {awayAverageRuns}");

                    var gameData = new
                    {
                        game.HomeTeam,
                        game.AwayTeam,
                        HomeTeamAvgRunExpectancy = homeAverageRuns,
                        AwayTeamAvgRunExpectancy = awayAverageRuns,
                        AverageRunExpectancy = (homeAverageRuns + awayAverageRuns) / 2
                    };

                    results.Add(gameData);
                }

                return results;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while simulating games.");
                return null;
            }
        }


        private async Task<(object Lineup, bool IsActual)> GetLineupForTeam(int gameId, string team, bool isHomeTeam)
        {
            var actualLineup = await _context.ActualLineups
                .Where(l => l.GamePreviewId == gameId && l.Team == team)
                .Select(l => new
                {
                    Batting1st = l.Batting1st ?? string.Empty,
                    Batting2nd = l.Batting2nd ?? string.Empty,
                    Batting3rd = l.Batting3rd ?? string.Empty,
                    Batting4th = l.Batting4th ?? string.Empty,
                    Batting5th = l.Batting5th ?? string.Empty,
                    Batting6th = l.Batting6th ?? string.Empty
                })
                .FirstOrDefaultAsync();

            if (actualLineup != null && !HasNullInFirstSixBatters(actualLineup))
            {
                return (actualLineup, true);
            }

            var predictedLineup = await _context.LineupPredictions
                .Where(l => l.GamePreviewId == gameId && l.Team == team)
                .Select(l => new
                {
                    Batting1st = l.Batting1st ?? string.Empty,
                    Batting2nd = l.Batting2nd ?? string.Empty,
                    Batting3rd = l.Batting3rd ?? string.Empty,
                    Batting4th = l.Batting4th ?? string.Empty,
                    Batting5th = l.Batting5th ?? string.Empty,
                    Batting6th = l.Batting6th ?? string.Empty
                })
                .FirstOrDefaultAsync();

            return (predictedLineup, false);
        }

        private bool HasNullInFirstSixBatters(object lineup)
        {
            var lineupDict = lineup as dynamic;
            return string.IsNullOrEmpty(lineupDict.Batting1st) ||
                   string.IsNullOrEmpty(lineupDict.Batting2nd) ||
                   string.IsNullOrEmpty(lineupDict.Batting3rd) ||
                   string.IsNullOrEmpty(lineupDict.Batting4th) ||
                   string.IsNullOrEmpty(lineupDict.Batting5th) ||
                   string.IsNullOrEmpty(lineupDict.Batting6th);
        }

        private async Task<(List<HitterStatsDto>, List<string>)> GetHittersStatsForLineup(object lineup)
        {
            var hittersStats = new List<HitterStatsDto>();
            var missingHitters = new List<string>();
            var lineupType = lineup.GetType();
            var lineupPositions = new List<string> { "Batting1st", "Batting2nd", "Batting3rd", "Batting4th", "Batting5th", "Batting6th" };

            foreach (var position in lineupPositions)
            {
                var hitterId = (string)lineupType.GetProperty(position)?.GetValue(lineup);
                if (!string.IsNullOrEmpty(hitterId))
                {
                    _logger.LogInformation($"Fetching hitter stats for {hitterId}");
                    var response = await _httpClient.GetAsync($"https://localhost:44346/api/Hitters/{hitterId}");
                    if (response.IsSuccessStatusCode)
                    {
                        var hitter = await response.Content.ReadFromJsonAsync<Hitter>();
                        if (hitter != null)
                        {
                            double walkPercentage = hitter.PA > 0 ? (double)hitter.BB / hitter.PA : 0;
                            double kPercentage = hitter.PA > 0 ? (double)hitter.SO / hitter.PA : 0;
                            double singlePercentage = hitter.H > 0 ? ((double)hitter.H - hitter.Doubles - hitter.Triples - hitter.HR) / hitter.H : 0;
                            double doublePercentage = hitter.H > 0 ? (double)hitter.Doubles / hitter.H : 0;
                            double triplePercentage = hitter.H > 0 ? (double)hitter.Triples / hitter.H : 0;
                            double homeRunPercentage = hitter.H > 0 ? (double)hitter.HR / hitter.H : 0;

                            var hitterStatsDto = new HitterStatsDto
                            {
                                bbrefId = hitter.bbrefId,
                                BA = hitter.BA,
                                OBP = hitter.OBP,
                                SLG = hitter.SLG,
                                KPercentage = kPercentage,
                                BBPercentage = walkPercentage,
                                SinglePercentage = singlePercentage,
                                DoublePercentage = doublePercentage,
                                TriplePercentage = triplePercentage,
                                homeRunPercentage = homeRunPercentage
                            };

                            hittersStats.Add(hitterStatsDto);
                        }
                    }
                    else
                    {
                        _logger.LogInformation($"Failed to retrieve stats for hitter: {hitterId}");
                        missingHitters.Add(hitterId);
                    }
                }
            }

            return (hittersStats, missingHitters);
        }


        private double SimulateGame(int iterations, List<HitterStatsDto> lineup, Pitcher1stInning pitcherStats)
        {
            double totalRuns = 0.0;

            for (int i = 0; i < iterations; i++)
            {
                int outs = 0;
                int baseState = 0; // Bases empty
                double runs = 0.0;
                int hitterIndex = 0;

                while (outs < 3)
                {
                    var hitter = lineup[hitterIndex];
                    double outcome = GenerateRandomOutcome(hitter, pitcherStats);

                    if (outcome == 1) // Single
                    {
                        runs += GetRunExpectancy(baseState, outs);
                        baseState = UpdateBaseStateForSingle(baseState);
                    }
                    else if (outcome == 2) // Double
                    {
                        runs += GetRunExpectancy(baseState, outs);
                        baseState = UpdateBaseStateForDouble(baseState);
                    }
                    else if (outcome == 3) // Triple
                    {
                        runs += GetRunExpectancy(baseState, outs);
                        baseState = UpdateBaseStateForTriple(baseState);
                    }
                    else if (outcome == 4) // HomeRun
                    {
                        // Calculate the runs scored based on the base state
                        runs += 1 + CountRunnersOnBase(baseState); // 1 for the hitter, plus any runners on base

                        baseState = UpdateBaseStateForHomeRun(baseState); // Clears the bases
                    }
                    else if (outcome == 0) // Walk
                    {
                        baseState = UpdateBaseState(baseState, 0);
                    }
                    else // Out (strikeout or other)
                    {
                        outs++;
                    }

                    hitterIndex = (hitterIndex + 1) % lineup.Count;
                }

                totalRuns += runs;
            }

            return totalRuns / iterations; // Average runs scored
        }

        private double CalculateProbability(double hitterStat, double pitcherStat)
        {
            return (hitterStat + pitcherStat) / 2.0;
        }

        private double GenerateRandomOutcome(HitterStatsDto hitter, Pitcher1stInning pitcherStats)
        {
            Random rand = new Random();
            double randomValue = rand.NextDouble();

            // Overall hit probability (based on batting average)
            double hitProbability = CalculateProbability(hitter.BA, pitcherStats.BA);
            double walkProbability = CalculateProbability(hitter.BBPercentage, pitcherStats.BB / pitcherStats.PA);
            double strikeoutProbability = CalculateProbability(hitter.KPercentage, pitcherStats.SO / pitcherStats.PA);

            // If hit occurs, determine the type of hit
            if (randomValue < hitProbability)
            {
                double singleProbability = CalculateProbability(hitter.SinglePercentage,
                    pitcherStats.H > 0 ? (pitcherStats.H - pitcherStats.TwoB - pitcherStats.ThreeB - pitcherStats.HR) / pitcherStats.H : 0);
                double doubleProbability = pitcherStats.H > 0 ?
                    CalculateProbability(hitter.DoublePercentage, pitcherStats.TwoB / pitcherStats.H) :
                    FallbackDoubleProbability(hitter, pitcherStats);
                double tripleProbability = pitcherStats.H > 0 ?
                    CalculateProbability(hitter.TriplePercentage, pitcherStats.ThreeB / pitcherStats.H) :
                    FallbackTripleProbability(hitter, pitcherStats);
                double homeRunProbability = pitcherStats.H > 0 ?
                    CalculateProbability(hitter.homeRunPercentage, pitcherStats.HR / pitcherStats.H) :
                    FallbackHomeRunProbability(hitter, pitcherStats);

                // Adjust probabilities cumulatively
                if (randomValue < singleProbability) return 1;  // Single
                if (randomValue < singleProbability + doubleProbability) return 2;  // Double
                if (randomValue < singleProbability + doubleProbability + tripleProbability) return 3;  // Triple
                return 4;  // HomeRun
            }

            // If not a hit, decide between walk, strikeout, or generic out
            if (randomValue < hitProbability + walkProbability) return 0;  // Walk
            if (randomValue < hitProbability + walkProbability + strikeoutProbability) return -1;  // Strikeout
            return -2;  // Generic out (flyout or groundout)
        }
        private int UpdateBaseState(int baseState, int eventType)
        {
            switch (eventType)
            {
                case 0: // Walk
                    return baseState == 7 ? 7 : baseState + 1; // If bases loaded, stays loaded
                case 1: // Single
                    return UpdateBaseStateForSingle(baseState);
                case 2: // Double
                    return UpdateBaseStateForDouble(baseState);
                case 3: // Triple
                    return UpdateBaseStateForTriple(baseState);
                case 4: // Home Run
                    return UpdateBaseStateForHomeRun(baseState);
                default:
                    return baseState; // Default to current base state
            }
        }

        private int UpdateBaseStateForSingle(int baseState)
        {
            Random rand = new Random();
            double randomValue = rand.NextDouble(); // Generates a number between 0.0 and 1.0

            switch (baseState)
            {
                case 0: // Bases empty
                    return 1; // Runner on 1st

                case 1: // Runner on 1st
                    if (randomValue < 0.6678) // 66.78% chance the runner reaches 2nd base
                    {
                        return 4; // Runners on 1st and 2nd
                    }
                    else if (randomValue < 0.6678 + 0.3183) // 31.83% chance the runner reaches 3rd base
                    {
                        return 6; // Runners on 1st and 3rd
                    }
                    else // 1.38% chance the runner is thrown out trying to advance
                    {
                        return 0; // Bases empty, 1 out added
                    }

                case 2: // Runner on 2nd
                    if (randomValue < 0.3583) // 35.83% chance the runner reaches 3rd base
                    {
                        return 6; // Runners on 1st and 3rd
                    }
                    else if (randomValue < 0.3583 + 0.6083) // 60.83% chance the runner scores
                    {
                        return 4; // Runner on 1st and 2nd (Runner on 2nd scores)
                    }
                    else // 3.32% chance the runner is thrown out trying to score
                    {
                        return 1; // Runner on 1st, 1 out added
                    }

                case 3: // Runner on 3rd
                    return 5; // Runners on 1st and 3rd (Runner on 3rd holds)

                case 4: // Runners on 1st and 2nd
                    if (randomValue < 0.3583) // 35.83% chance the runner on 2nd reaches 3rd base
                    {
                        return 7; // Bases loaded
                    }
                    else if (randomValue < 0.3583 + 0.6083) // 60.83% chance the runner on 2nd scores
                    {
                        return 6; // Runners on 1st and 3rd (Runner on 2nd scores)
                    }
                    else // 3.32% chance the runner on 2nd is thrown out trying to score
                    {
                        return 4; // Runners on 1st and 2nd, 1 out added
                    }

                case 5: // Runners on 1st and 3rd
                    if (randomValue < 0.6678) // 66.78% chance the runner on 1st reaches 2nd base
                    {
                        return 7; // Bases loaded
                    }
                    else if (randomValue < 0.6678 + 0.3183) // 31.83% chance the runner on 1st reaches 3rd base
                    {
                        return 7; // Bases loaded (Runner on 3rd holds)
                    }
                    else // 1.38% chance the runner on 1st is thrown out trying to advance
                    {
                        return 3; // Runner on 3rd, 1 out added
                    }

                case 6: // Runners on 2nd and 3rd
                    if (randomValue < 0.6083) // 60.83% chance the runner on 2nd scores
                    {
                        return 5; // Runners on 1st and 3rd (Runner on 2nd scores)
                    }
                    else if (randomValue < 0.6083 + 0.3583) // 35.83% chance the runner on 2nd reaches 3rd base
                    {
                        return 7; // Bases loaded
                    }
                    else // 3.32% chance the runner on 2nd is thrown out trying to score
                    {
                        return 5; // Runners on 1st and 3rd, 1 out added
                    }

                case 7: // Bases loaded
                    return 7; // Bases remain loaded

                default:
                    return baseState; // Default to current base state
            }
        }

        private int UpdateBaseStateForDouble(int baseState)
        {
            Random rand = new Random();
            double randomValue = rand.NextDouble(); // Generates a number between 0.0 and 1.0

            switch (baseState)
            {
                case 0: // Bases empty
                    return 2; // Runner on 2nd

                case 1: // Runner on 1st
                    if (randomValue < 0.4145) // 41.45% chance the runner scores
                    {
                        return 2; // Runner on 2nd, runner on 1st scores
                    }
                    else if (randomValue < 0.4145 + 0.5455) // 54.55% chance the runner goes to 3rd
                    {
                        return 6; // Runners on 2nd and 3rd
                    }
                    else // 4% chance the runner is thrown out trying to score
                    {
                        return 0; // Bases empty, 1 out added
                    }

                case 2: // Runner on 2nd
                    return 2; // Runner on 2nd (Runner on 2nd scores)

                case 3: // Runner on 3rd
                    return 2; // Runner on 2nd (Runner on 3rd scores)

                case 4: // Runners on 1st and 2nd
                    if (randomValue < 0.4145) // 41.45% chance the runner on 1st scores
                    {
                        return 6; // Runner on 2nd and 3rd (Runner on 1st scores)
                    }
                    else if (randomValue < 0.4145 + 0.5455) // 54.55% chance the runner on 1st goes to 3rd
                    {
                        return 7; // Bases loaded
                    }
                    else // 4% chance the runner on 1st is thrown out trying to score
                    {
                        return 2; // Runner on 2nd, 1 out added
                    }

                case 5: // Runners on 1st and 3rd
                    if (randomValue < 0.4145) // 41.45% chance the runner on 1st scores
                    {
                        return 6; // Runner on 2nd and 3rd (Runner on 1st scores)
                    }
                    else if (randomValue < 0.4145 + 0.5455) // 54.55% chance the runner on 1st goes to 3rd
                    {
                        return 7; // Bases loaded
                    }
                    else // 4% chance the runner on 1st is thrown out trying to score
                    {
                        return 3; // Runner on 3rd, 1 out added
                    }

                case 6: // Runners on 2nd and 3rd
                    return 6; // Runners stay on 2nd and 3rd

                case 7: // Bases loaded
                    return 6; // Runners on 2nd and 3rd (Runner on 3rd scores)

                default:
                    return baseState; // Default to current base state
            }
        }

        private int UpdateBaseStateForTriple(int baseState)
        {
            switch (baseState)
            {
                case 0: // Bases empty
                    return 3; // Runner on 3rd
                case 1: // Runner on 1st
                    return 3; // Runner on 3rd (Runner on 1st scores)
                case 2: // Runner on 2nd
                    return 3; // Runner on 3rd (Runner on 2nd scores)
                case 3: // Runner on 3rd
                    return 3; // Runner on 3rd (Runner on 3rd scores)
                case 4: // Runners on 1st and 2nd
                    return 3; // Runner on 3rd (Both runners score)
                case 5: // Runners on 1st and 3rd
                    return 3; // Runner on 3rd (Both runners score)
                case 6: // Runners on 2nd and 3rd
                    return 3; // Runner on 3rd (Both runners score)
                case 7: // Bases loaded
                    return 3; // Runner on 3rd (All runners score)
                default:
                    return baseState; // Default case
            }
        }

        private int UpdateBaseStateForHomeRun(int baseState)
        {
            // Home run clears the bases, so the new base state is always 0 (bases empty)
            return 0;
        }

        private int CountRunnersOnBase(int baseState)
        {
            // Base states are represented as follows:
            // 0 = Bases empty
            // 1 = Runner on 1st
            // 2 = Runner on 2nd
            // 3 = Runner on 3rd
            // 4 = Runners on 1st and 2nd
            // 5 = Runners on 1st and 3rd
            // 6 = Runners on 2nd and 3rd
            // 7 = Bases loaded

            switch (baseState)
            {
                case 0: return 0; // Bases empty
                case 1: return 1; // Runner on 1st
                case 2: return 1; // Runner on 2nd
                case 3: return 1; // Runner on 3rd
                case 4: return 2; // Runners on 1st and 2nd
                case 5: return 2; // Runners on 1st and 3rd
                case 6: return 2; // Runners on 2nd and 3rd
                case 7: return 3; // Bases loaded
                default: return 0; // Should never happen, but just in case
            }
        }

        private readonly double[,] re24Matrix = new double[8, 3]
{
    { 0.476, 0.254, 0.097 },  // Bases empty
    { 0.865, 0.508, 0.205 },  // Runner on 1st
    { 1.073, 0.667, 0.308 },  // Runner on 2nd
    { 1.272, 0.974, 0.377 },  // Runner on 3rd
    { 1.435, 0.902, 0.440 },  // Runners on 1st and 2nd
    { 1.753, 1.147, 0.500 },  // Runners on 1st and 3rd
    { 2.005, 1.390, 0.548 },  // Runners on 2nd and 3rd
    { 2.367, 1.508, 0.767 }   // Bases loaded
};
        private double GetRunExpectancy(int baseState, int outs)
        {
            return re24Matrix[baseState, outs];
        }


        private double FallbackDoubleProbability(HitterStatsDto hitter, Pitcher1stInning pitcherStats)
        {
            // Example assumption: Use a percentage of SLG for doubles if no specific data is available
            return CalculateProbability(hitter.DoublePercentage, pitcherStats.SLG * 0.2); // Adjust multiplier based on analysis
        }

        private double FallbackTripleProbability(HitterStatsDto hitter, Pitcher1stInning pitcherStats)
        {
            // Example assumption: Use a smaller percentage of SLG for triples
            return CalculateProbability(hitter.TriplePercentage, pitcherStats.SLG * 0.05); // Adjust multiplier based on analysis
        }

        private double FallbackHomeRunProbability(HitterStatsDto hitter, Pitcher1stInning pitcherStats)
        {
            // Example assumption: Use a percentage of SLG for home runs
            return CalculateProbability(hitter.homeRunPercentage, pitcherStats.SLG * 0.3); // Adjust multiplier based on analysis
        }



    }


}