using SharpVizAPI.Data;
using SharpVizAPI.Models;
using SharpVizAPI.Controllers;
using SharpVizAPI.Services;

using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Net.Http;
using SharpVizAPI.DTO;
using System.Text;

public class EvaluationService
{
    private readonly NrfidbContext _context;
    private readonly HttpClient _httpClient;
    private readonly BlendingService _blendingService;
    private readonly ILogger<EvaluationService> _logger;
    private const double SingleRunValue = 0.47;
    private const double TripleRunValue = 1.051;
    private const double DoubleRunValue = 0.776;
    private const double HomeRunValue = 1.377;
    private const double WalkRunValue = 0.222;
    private const double StrikeoutRunValue = -0.25;
    private const double flyoutRunValue = -0.097;
    private const double groundOutRunValue = -0.15;




    public EvaluationService(NrfidbContext context, ILogger<EvaluationService> logger, HttpClient httpClient, BlendingService blendingService)
    {
        _context = context;
        _httpClient = httpClient;
        _logger = logger;
        _blendingService = blendingService;
    }
    public async Task<object> Calculate1stInningRunExpectancy(string date)
    {
        _logger.LogInformation("Calculating 1st Inning Run Expectancy...");

        var gamePreviews = await _context.GamePreviews
            .Where(g => g.Date.Date == DateTime.Parse(date).Date)
            .ToListAsync();

        if (gamePreviews == null || gamePreviews.Count == 0)
        {
            _logger.LogInformation("No game previews found.");
            return null;
        }

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
                _logger.LogInformation($"Failed to retrieve lineups for {game.HomeTeam} vs {game.AwayTeam}");
                continue;
            }

            _logger.LogInformation("Fetched lineups.");

            // Fetch pitcher season stats
            var homePitcherStats = await _context.Pitchers
                .Where(p => p.BbrefId == game.HomePitcher || game.HomePitcher == "Unannounced")
                .FirstOrDefaultAsync();

            if (homePitcherStats == null)
            {
                _logger.LogInformation($"Home pitcher {game.HomePitcher} does not have Season stats... using average starter stats.");
                homePitcherStats = await _context.Pitchers
                    .Where(p => p.BbrefId == "Unannounced")
                    .FirstOrDefaultAsync();
            }

            var awayPitcherStats = await _context.Pitchers
                .Where(p => p.BbrefId == game.AwayPitcher || game.AwayPitcher == "Unannounced")
                .FirstOrDefaultAsync();

            if (awayPitcherStats == null)
            {
                _logger.LogInformation($"Away pitcher {game.AwayPitcher} does not have Season stats... using average starter stats.");
                awayPitcherStats = await _context.Pitchers
                    .Where(p => p.BbrefId == "Unannounced")
                    .FirstOrDefaultAsync();
            }

            _logger.LogInformation("Fetched season pitcher stats.");
            //first inning stats
            var homePitcherFirstInningStats = await _context.Pitcher1stInnings
                .Where(p => p.BbrefId == game.HomePitcher || game.HomePitcher == "Unannounced")
                .FirstOrDefaultAsync();

            if (homePitcherFirstInningStats == null)
            {
                _logger.LogInformation($"Home pitcher {game.HomePitcher} does not have first inning stats... using average first inning stats.");
                homePitcherFirstInningStats = await _context.Pitcher1stInnings
                    .Where(p => p.BbrefId == "Unannounced")
                    .FirstOrDefaultAsync();
            }

            var awayPitcherFirstInningStats = await _context.Pitcher1stInnings
                .Where(p => p.BbrefId == game.AwayPitcher || game.AwayPitcher == "Unannounced")
                .FirstOrDefaultAsync();

            if (awayPitcherFirstInningStats == null)
            {
                _logger.LogInformation($"Away pitcher {game.AwayPitcher} does not have first inning stats... using average first inning stats.");
                awayPitcherFirstInningStats = await _context.Pitcher1stInnings
                    .Where(p => p.BbrefId == "Unannounced")
                    .FirstOrDefaultAsync();
            }

            _logger.LogInformation("Fetched first inning pitcher stats.");

            var homePitcherStatsAtHome = await _context.PitcherHomeAwaySplits
                .Where(p => p.bbrefID == game.HomePitcher || game.HomePitcher == "Unannounced")
                .FirstOrDefaultAsync();

            if (homePitcherStatsAtHome == null)
            {
                _logger.LogInformation($"Home pitcher {game.HomePitcher} does not have home stats... using average first inning stats.");
                homePitcherStatsAtHome = await _context.PitcherHomeAwaySplits
                    .Where(p => p.bbrefID == "Unannounced")
                    .FirstOrDefaultAsync();
            }

            var AwayPitcherStatsAtAway = await _context.PitcherHomeAwaySplits
                .Where(p => p.bbrefID == game.AwayPitcher || game.AwayPitcher == "Unannounced")
                .FirstOrDefaultAsync();

            if (AwayPitcherStatsAtAway == null)
            {
                _logger.LogInformation($"Away pitcher {game.AwayPitcher} does not have Away stats... using average first inning stats.");
                AwayPitcherStatsAtAway = await _context.PitcherHomeAwaySplits
                    .Where(p => p.bbrefID == "Unannounced")
                    .FirstOrDefaultAsync();
            }

            _logger.LogInformation("Fetched home/away pitcher stats.");

            // Get blended stats for home pitcher
            var homePitcherBlendedStats = await _blendingService.Blend1stInningWithPlatoonStats(game.HomePitcher);
            if (homePitcherBlendedStats.ContainsKey("message"))
            {
                _logger.LogInformation($"Blended stats not available for home pitcher {game.HomePitcher}.");
            }

            // Get blended stats for away pitcher
            var awayPitcherBlendedStats = await _blendingService.Blend1stInningWithPlatoonStats(game.AwayPitcher);
            if (awayPitcherBlendedStats.ContainsKey("message"))
            {
                _logger.LogInformation($"Blended stats not available for away pitcher {game.AwayPitcher}.");
            }


            // Get hitters' stats based on the lineups
            var (homeHittersStats, homeMissingHitters) = await GetHittersStatsForLineup(homeLineup.Lineup);
            var (awayHittersStats, awayMissingHitters) = await GetHittersStatsForLineup(awayLineup.Lineup);

            _logger.LogInformation("Fetched hitter stats.");

            // Calculate expected runs
            var homePitcherHandedness = homePitcherStats.Throws; // LHP or RHP
            var awayPitcherHandedness = awayPitcherStats.Throws; // LHP or RHP
            //var expectedRunsSeason = CalculateExpectedRuns(homePitcherStats, awayPitcherStats, homeHittersStats, awayHittersStats);
            //var expectedRuns1stRAW = CalculateExpectedRuns(homePitcherFirstInningStats, awayPitcherFirstInningStats, homeHittersStats, awayHittersStats);
            var expectedRuns1st = CalculateExpectedRuns(homePitcherBlendedStats, awayPitcherBlendedStats, homeHittersStats, awayHittersStats, homePitcherHandedness, awayPitcherHandedness);

            //var expectedRunsHAsplits = CalculateExpectedRuns(homePitcherStatsAtHome, AwayPitcherStatsAtAway, homeHittersStats, awayHittersStats);

            var totalAvg = expectedRuns1st;
            //var totalAvg = (expectedRuns1st  + expectedRunsHAsplits) / 3; //+ expectedRunsSeason

            _logger.LogInformation($"Expected runs for {game.HomeTeam} vs {game.AwayTeam}: {totalAvg}");


            var gameData = new
            {
                game.Time,
                game.HomeTeam,
                game.AwayTeam,
                game.Venue,
                HomeLineup = homeLineup.Lineup,
                AwayLineup = awayLineup.Lineup,
                IsHomeLineupActual = homeLineup.IsActual,
                IsAwayLineupActual = awayLineup.IsActual,
                HomePitcher = new { Stats = homePitcherStats, FirstInningStats = homePitcherFirstInningStats },
                AwayPitcher = new { Stats = awayPitcherStats, FirstInningStats = awayPitcherFirstInningStats },
                homePitcherThrows = homePitcherHandedness,
                awayPitcherThrows = awayPitcherHandedness,
                ExpectedRuns = totalAvg,
                //ExpectedRunsFromSeason = expectedRunsSeason,
                expectedRunsFrom1st = expectedRuns1st,
                //expectedRunsFromHAsplits = expectedRunsHAsplits,

                HomeMissingHitters = homeMissingHitters,
                AwayMissingHitters = awayMissingHitters
            };

            results.Add(gameData);
        }

        return results;
    }

    private async Task<(object Lineup, bool IsActual)> GetLineupForTeam(int gameId, string team, bool isHomeTeam)
    {
        // Retrieve the actual lineup first
        var actualLineup = await _context.ActualLineups
            .Where(l => l.GamePreviewId == gameId && l.Team == team) // Ensure team matching
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
            return (actualLineup, true);  // True indicates it's an actual lineup
        }

        // Retrieve the predicted lineup if actual lineup is not found or incomplete
        var predictedLineup = await _context.LineupPredictions
            .Where(l => l.GamePreviewId == gameId && l.Team == team) // Ensure team matching
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

        return (predictedLineup, false);  // False indicates it's a predicted lineup
    }


    private bool HasNullInFirstSixBatters(object lineup)
    {
        // Adjust this method to work with the anonymous type representing the lineup
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
        //if more types of hitter stand create another list and make two lists to pass
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
                        // Calculate the WalkPercentage and KPercentage
                        double walkPercentage = hitter.PA > 0 ? (double)hitter.BB / hitter.PA : 0;
                        double kPercentage = hitter.PA > 0 ? (double)hitter.SO / hitter.PA : 0;
                        double SinglePercentage = hitter.H > 0 ? ((double)hitter.H - hitter.Doubles - hitter.Triples - hitter.HR) / hitter.H : 0;
                        double DoublePercentage = hitter.H > 0 ? (double)hitter.Doubles / hitter.H : 0;
                        double TriplePercentage = hitter.H > 0 ? (double)hitter.Triples / hitter.H : 0; 
                        double homeRunPercentage = hitter.H > 0 ? (double)hitter.HR / hitter.H : 0;
                        String bats = hitter.Bats;


                        // Map the Hitter data to HitterStatsDto
                        var hitterStatsDto = new HitterStatsDto
                        {
                            bbrefId = hitter.bbrefId,
                            BA = hitter.BA,
                            OBP = hitter.OBP,
                            SLG = hitter.SLG,
                            KPercentage = kPercentage,
                            BBPercentage = walkPercentage,
                            SinglePercentage = SinglePercentage,
                            DoublePercentage = DoublePercentage,
                            TriplePercentage = TriplePercentage,
                            homeRunPercentage = homeRunPercentage,
                            Bats = bats
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



    private List<string> ConvertLineupToList(object lineup)
    {
        // Convert lineup to a list of bbrefIds based on its type
        // You'll need to implement this based on the actual structure of ActualLineup and PredictedLineup
        // Example:
        if (lineup is ActualLineup actual)
        {
            return new List<string>
            {
                actual.Batting1st,
                actual.Batting2nd,
                actual.Batting3rd,
                actual.Batting4th,
                actual.Batting5th,
                actual.Batting6th
            };
        }
        if (lineup is LineupPrediction predicted)
        {
            return new List<string>
            {
                predicted.Batting1st,
                predicted.Batting2nd,
                predicted.Batting3rd,
                predicted.Batting4th,
                predicted.Batting5th,
                predicted.Batting6th
            };
        }

        return new List<string>();
    }
    private double CalculateProbability(double hitterStat, double pitcherStat)
    {
        return (hitterStat + pitcherStat) / 2.0;
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
    private double CalculateExpectedRunsForHitter(HitterStatsDto hitterStats, Dictionary<string, object> pitcherBlendedStats, string pitcherHandedness, int outs)
    {
        var isSwitchHitter = hitterStats.Bats == "S";
        var isLeftHandedHitter = hitterStats.Bats == "LH";
        var isRightHandedHitter = hitterStats.Bats == "RH";

        // Determine which blended stats to use
        dynamic relevantBlendedStats = null;

        try
        {
            if (isSwitchHitter)
            {
                relevantBlendedStats = pitcherHandedness == "LHP" ? pitcherBlendedStats["blendedRHBStats"] : pitcherBlendedStats["blendedLHBStats"];
            }
            else if (isLeftHandedHitter)
            {
                relevantBlendedStats = pitcherBlendedStats["blendedLHBStats"];
            }
            else // Right-handed hitter
            {
                relevantBlendedStats = pitcherBlendedStats["blendedRHBStats"];
            }
        }
        catch (KeyNotFoundException ex)
        {
            _logger.LogError($"Blended stats key not found: {ex.Message}");
            return 0; // or handle this case as needed
        }

        // Now calculate the probability using relevantBlendedStats instead of raw firstInningStats
        double P_K = CalculateProbability(hitterStats.KPercentage, relevantBlendedStats.K_Percentage);
        double P_BB = CalculateProbability(hitterStats.BBPercentage, relevantBlendedStats.BB_Percentage);
        double P_H = CalculateProbability(hitterStats.BA, relevantBlendedStats.BA) * (1 - P_K);
        double P_XBH = CalculateProbability(hitterStats.SLG, relevantBlendedStats.SLG);
        double P_OUT = 1 - P_H - P_BB;  // Probability of an out

        double singleRunValue = SingleRunValue * GetRunExpectancy(0, outs);
        double doubleRunValue = DoubleRunValue * GetRunExpectancy(0, outs);
        double walkRunValue = WalkRunValue * GetRunExpectancy(0, outs);
        double strikeoutRunValue = StrikeoutRunValue * GetRunExpectancy(0, outs);
        double flyoutRunValueAdjusted = flyoutRunValue * GetRunExpectancy(0, outs);
        double groundOutRunValueAdjusted = groundOutRunValue * GetRunExpectancy(0, outs);

        return P_H * singleRunValue +
               P_XBH * doubleRunValue +
               P_BB * walkRunValue +
               P_K * strikeoutRunValue +
               P_OUT * (flyoutRunValueAdjusted + groundOutRunValueAdjusted);
    }

    private (int, int) UpdateBaseStateForSingle(int baseState)
    {
        int runsScored = 0; // Track the number of runs scored
        Random rand = new Random();
        double randomValue = rand.NextDouble(); // Generates a number between 0.0 and 1.0

        switch (baseState)
        {
            case 0: // Bases empty
                return (1, runsScored); // Runner on 1st, no runs scored

            case 1: // Runner on 1st
                if (randomValue < 0.6678) // 66.78% chance the runner reaches 2nd base
                {
                    return (4, runsScored); // Runners on 1st and 2nd, no runs scored
                }
                else if (randomValue < 0.6678 + 0.3183) // 31.83% chance the runner reaches 3rd base
                {
                    return (6, runsScored); // Runners on 1st and 3rd, no runs scored
                }
                else // 1.38% chance the runner is thrown out trying to advance
                {
                    return (0, runsScored); // Bases empty, 1 out added
                }

            case 2: // Runner on 2nd
                if (randomValue < 0.3583) // 35.83% chance the runner reaches 3rd base
                {
                    return (6, runsScored); // Runners on 1st and 3rd, no runs scored
                }
                else if (randomValue < 0.3583 + 0.6083) // 60.83% chance the runner scores
                {
                    runsScored++; // Runner on 2nd scores
                    return (4, runsScored); // Runner on 1st and 2nd
                }
                else // 3.32% chance the runner is thrown out trying to score
                {
                    return (1, runsScored); // Runner on 1st, 1 out added
                }

            case 3: // Runner on 3rd
                runsScored++; // Runner on 3rd scores
                return (5, runsScored); // Runners on 1st and 3rd

            case 4: // Runners on 1st and 2nd
                if (randomValue < 0.3583) // 35.83% chance the runner on 2nd reaches 3rd base
                {
                    return (7, runsScored); // Bases loaded
                }
                else if (randomValue < 0.3583 + 0.6083) // 60.83% chance the runner on 2nd scores
                {
                    runsScored++; // Runner on 2nd scores
                    return (6, runsScored); // Runners on 1st and 3rd
                }
                else // 3.32% chance the runner on 2nd is thrown out trying to score
                {
                    return (4, runsScored); // Runners on 1st and 2nd, 1 out added
                }

            case 5: // Runners on 1st and 3rd
                if (randomValue < 0.6678) // 66.78% chance the runner on 1st reaches 2nd base
                {
                    return (7, runsScored); // Bases loaded
                }
                else if (randomValue < 0.6678 + 0.3183) // 31.83% chance the runner on 1st reaches 3rd base
                {
                    return (7, runsScored); // Bases loaded (Runner on 3rd holds)
                }
                else // 1.38% chance the runner on 1st is thrown out trying to advance
                {
                    return (3, runsScored); // Runner on 3rd, 1 out added
                }

            case 6: // Runners on 2nd and 3rd
                if (randomValue < 0.6083) // 60.83% chance the runner on 2nd scores
                {
                    runsScored++; // Runner on 2nd scores
                    return (5, runsScored); // Runners on 1st and 3rd
                }
                else if (randomValue < 0.6083 + 0.3583) // 35.83% chance the runner on 2nd reaches 3rd base
                {
                    return (7, runsScored); // Bases loaded
                }
                else // 3.32% chance the runner on 2nd is thrown out trying to score
                {
                    return (5, runsScored); // Runners on 1st and 3rd, 1 out added
                }

            case 7: // Bases loaded
                runsScored++; // Runner on 3rd scores
                return (7, runsScored); // Bases remain loaded

            default:
                return (baseState, runsScored); // Default to current base state
        }
    }

    private (int, int) UpdateBaseStateForDouble(int baseState)
    {
        int runsScored = 0; // Track the number of runs scored
        Random rand = new Random();
        double randomValue = rand.NextDouble(); // Generates a number between 0.0 and 1.0

        switch (baseState)
        {
            case 0: // Bases empty
                return (2, runsScored); // Runner on 2nd, no runs scored

            case 1: // Runner on 1st
                if (randomValue < 0.4145) // 41.45% chance the runner scores
                {
                    runsScored++; // Runner on 1st scores
                    return (2, runsScored); // Runner on 2nd
                }
                else if (randomValue < 0.4145 + 0.5455) // 54.55% chance the runner goes to 3rd
                {
                    return (6, runsScored); // Runners on 2nd and 3rd
                }
                else // 4% chance the runner is thrown out trying to score
                {
                    return (0, runsScored); // Bases empty, 1 out added
                }

            case 2: // Runner on 2nd
                runsScored++; // Runner on 2nd scores
                return (2, runsScored); // Runner on 2nd

            case 3: // Runner on 3rd
                runsScored++; // Runner on 3rd scores
                return (2, runsScored); // Runner on 2nd

            case 4: // Runners on 1st and 2nd
                if (randomValue < 0.4145) // 41.45% chance the runner on 1st scores
                {
                    runsScored++; // Runner on 1st scores
                    return (6, runsScored); // Runner on 2nd and 3rd
                }
                else if (randomValue < 0.4145 + 0.5455) // 54.55% chance the runner on 1st goes to 3rd
                {
                    return (7, runsScored); // Bases loaded
                }
                else // 4% chance the runner on 1st is thrown out trying to score
                {
                    return (2, runsScored); // Runner on 2nd, 1 out added
                }

            case 5: // Runners on 1st and 3rd
                if (randomValue < 0.4145) // 41.45% chance the runner on 1st scores
                {
                    runsScored++; // Runner on 1st scores
                    return (6, runsScored); // Runner on 2nd and 3rd
                }
                else if (randomValue < 0.4145 + 0.5455) // 54.55% chance the runner on 1st goes to 3rd
                {
                    return (7, runsScored); // Bases loaded
                }
                else // 4% chance the runner on 1st is thrown out trying to score
                {
                    return (3, runsScored); // Runner on 3rd, 1 out added
                }

            case 6: // Runners on 2nd and 3rd
                runsScored++; // Runner on 2nd scores
                return (6, runsScored); // Runners stay on 2nd and 3rd

            case 7: // Bases loaded
                runsScored++; // Runner on 3rd scores
                return (6, runsScored); // Runners on 2nd and 3rd

            default:
                return (baseState, runsScored); // Default to current base state
        }
    }

    private (int, int) UpdateBaseStateForTriple(int baseState)
    {
        int runsScored = 0; // Track the number of runs scored

        switch (baseState)
        {
            case 0: // Bases empty
                return (3, runsScored); // Runner on 3rd, no runs scored

            case 1: // Runner on 1st
                runsScored++; // Runner on 1st scores
                return (3, runsScored); // Runner on 3rd

            case 2: // Runner on 2nd
                runsScored++; // Runner on 2nd scores
                return (3, runsScored); // Runner on 3rd

            case 3: // Runner on 3rd
                runsScored++; // Runner on 3rd scores
                return (3, runsScored); // Runner on 3rd

            case 4: // Runners on 1st and 2nd
                runsScored += 2; // Both runners score
                return (3, runsScored); // Runner on 3rd

            case 5: // Runners on 1st and 3rd
                runsScored += 2; // Both runners score
                return (3, runsScored); // Runner on 3rd

            case 6: // Runners on 2nd and 3rd
                runsScored += 2; // Both runners score
                return (3, runsScored); // Runner on 3rd

            case 7: // Bases loaded
                runsScored += 3; // All runners score
                return (3, runsScored); // Runner on 3rd

            default:
                return (baseState, runsScored); // Default to current base state
        }
    }

    private (int, int) UpdateBaseStateForHomeRun(int baseState)
    {
        int runsScored = 0;

        switch (baseState)
        {
            case 0: // Bases empty
                runsScored = 1; // Home run with bases empty scores 1 run
                break;
            case 1: // Runner on 1st
                runsScored = 2; // Home run with runner on 1st scores 2 runs
                break;
            case 2: // Runner on 2nd
                runsScored = 2; // Home run with runner on 2nd scores 2 runs
                break;
            case 3: // Runner on 3rd
                runsScored = 2; // Home run with runner on 3rd scores 2 runs
                break;
            case 4: // Runners on 1st and 2nd
                runsScored = 3; // Home run with runners on 1st and 2nd scores 3 runs
                break;
            case 5: // Runners on 1st and 3rd
                runsScored = 3; // Home run with runners on 1st and 3rd scores 3 runs
                break;
            case 6: // Runners on 2nd and 3rd
                runsScored = 3; // Home run with runners on 2nd and 3rd scores 3 runs
                break;
            case 7: // Bases loaded
                runsScored = 4; // Grand slam scores 4 runs
                break;
        }

        return (0, runsScored); // Home run clears the bases, so the new base state is always 0 (bases empty)
    }

    private (int newBaseState, int runsScored) UpdateBaseStateForWalk(int baseState)
    {
        int runsScored = 0;

        switch (baseState)
        {
            case 0:  // Bases empty
                return (1, runsScored);  // Runner on 1st (000 -> 001)
            case 1:  // Runner on 1st
                return (3, runsScored);  // Runners on 1st and 2nd (001 -> 011)
            case 2:  // Runner on 2nd
                return (5, runsScored);  // Runners on 1st and 3rd (010 -> 101)
            case 3:  // Runners on 1st and 2nd
                return (7, runsScored);  // Bases loaded (011 -> 111)
            case 4:  // Runner on 3rd
                return (5, runsScored);  // Runners on 1st and 3rd (100 -> 101)
            case 5:  // Runners on 1st and 3rd
                return (7, runsScored);  // Bases loaded (101 -> 111)
            case 6:  // Runners on 2nd and 3rd
                return (7, runsScored);  // Bases loaded (110 -> 111)
            case 7:  // Bases loaded
                runsScored = 1;  // A run is scored when bases are loaded and a walk occurs
                return (7, runsScored);  // Bases remain loaded (111 -> 111)
            default:
                return (baseState, runsScored);  // In case of an unexpected state, return the current state
        }
    }
    public async Task<object> CalculateInningWithBaseState(string date, int numSimulations = 1000)
    {
        _logger.LogInformation("Calculating inning with base state...");

        var gamePreviews = await _context.GamePreviews
            .Where(g => g.Date.Date == DateTime.Parse(date).Date)
            .ToListAsync();

        if (gamePreviews == null || gamePreviews.Count == 0)
        {
            _logger.LogInformation("No game previews found.");
            return null;
        }

        var results = new List<object>();

        foreach (var game in gamePreviews)
        {
            _logger.LogInformation($"Processing game: {game.HomeTeam} vs {game.AwayTeam}");

            // Get lineups for both home and away teams (actual or predicted)
            var homeLineup = await GetLineupForTeam(game.Id, game.HomeTeam, true);
            var awayLineup = await GetLineupForTeam(game.Id, game.AwayTeam, false);

            // Check if lineups were fetched successfully
            if (homeLineup.Lineup == null || awayLineup.Lineup == null)
            {
                _logger.LogInformation($"Failed to retrieve lineups for {game.HomeTeam} vs {game.AwayTeam}");
                continue;
            }

            // Fetch blended stats for home and away pitchers
            var homePitcherBlendedStats = await _blendingService.Blend1stInningWithPlatoonStats(game.HomePitcher);
            var awayPitcherBlendedStats = await _blendingService.Blend1stInningWithPlatoonStats(game.AwayPitcher);

            if (homePitcherBlendedStats == null || awayPitcherBlendedStats == null)
            {
                _logger.LogInformation($"Blended stats not found for one or both pitchers in {game.HomeTeam} vs {game.AwayTeam}");
                continue;
            }

            // Get the Throws value for the pitchers (RHP or LHP)
            var homePitcherThrows = await _context.Pitchers
                .Where(p => p.BbrefId == game.HomePitcher)
                .Select(p => p.Throws)
                .FirstOrDefaultAsync();

            var awayPitcherThrows = await _context.Pitchers
                .Where(p => p.BbrefId == game.AwayPitcher)
                .Select(p => p.Throws)
                .FirstOrDefaultAsync();

            if (homePitcherThrows == null || awayPitcherThrows == null)
            {
                _logger.LogInformation($"Throws not found for one or both pitchers in {game.HomeTeam} vs {game.AwayTeam}");
                continue;
            }

            // Get hitter stats for both home and away teams
            var (homeHittersStats, homeMissingHitters) = await GetHittersStatsForLineup(homeLineup.Lineup);
            var (awayHittersStats, awayMissingHitters) = await GetHittersStatsForLineup(awayLineup.Lineup);

            _logger.LogInformation("Fetched hitter stats.");

            // Initialize accumulators for total runs over all simulations
            double totalHomeRuns = 0.0;
            double totalAwayRuns = 0.0;

            // Run simulations
            double awayScored = 0;
            double homeScored = 0;
            for (int sim = 0; sim < numSimulations; sim++)
            {
                // Start with base state 0 (bases empty) and 0 outs for the home team
                int baseState = 0;
                int outs = 0;

                // Calculate expected runs for home team in this simulation
                double homeExpectedRuns = 0.0;

                for (int i = 0; i < homeHittersStats.Count; i++)
                {
                    double tempH= CalculateExpectedRunsForHitterWithBaseState(
                        homeHittersStats[i],
                        awayPitcherBlendedStats,
                        awayPitcherThrows,
                        ref outs,
                        ref baseState
                    );
                    if (tempH > 0)
                    {
                        homeScored++;
                    }
                    homeExpectedRuns += tempH;
                    // Break if 3 outs are reached
                    if (outs >= 3) break;
                }

                // Reset base state and outs for the away team
                baseState = 0;
                outs = 0;

                // Calculate expected runs for away team in this simulation
                double awayExpectedRuns = 0.0;

                for (int i = 0; i < awayHittersStats.Count; i++)
                {
                    double tempA= CalculateExpectedRunsForHitterWithBaseState(
                        awayHittersStats[i],
                        homePitcherBlendedStats,
                        homePitcherThrows,
                        ref outs,
                        ref baseState
                    );
                    if (tempA > 0)
                    {
                        awayScored++;
                    }
                    awayExpectedRuns += tempA;

                    // Break if 3 outs are reached
                    if (outs >= 3) break;
                }

                // Accumulate the results for this simulation

                totalHomeRuns += homeExpectedRuns;
                totalAwayRuns += awayExpectedRuns;
            }

            // Calculate the average expected runs across all simulations
            double averageHomeRuns = totalHomeRuns / numSimulations;
            double averageAwayRuns = totalAwayRuns / numSimulations;
            double homeScorePerc = homeScored / numSimulations;
            double awayScorePerc = awayScored / numSimulations;


            // Add the results for this game to the final list
            results.Add(new
            {
                Game = $"{game.HomeTeam} vs {game.AwayTeam}",
                HomeExpectedRunsPerSim = averageHomeRuns,
                AwayExpectedRunsPerSim = averageAwayRuns,
                HomeLineupActual = homeLineup.IsActual,
                AwayLineupActual = awayLineup.IsActual,
                HomeScoringPer = homeScorePerc,
                AwayScoringPer = awayScorePerc,
                ProbOfYRFISimulated1000x = homeScorePerc + awayScorePerc - (homeScorePerc * awayScorePerc)
            });
        }

        return results;
    }

    private double CalculateExpectedRunsForHitterWithBaseState(
        HitterStatsDto hitterStats,
        Dictionary<string, object> pitcherBlendedStats,
        string pitcherHandedness,
        ref int outs,
        ref int baseState)
    {
        // Determine the relevant blended stats
        dynamic relevantBlendedStats = null;

        try
        {
            if (hitterStats.Bats == "S") // Switch Hitter
            {
                relevantBlendedStats = pitcherHandedness == "LHP" ? pitcherBlendedStats["blendedRHBStats"] : pitcherBlendedStats["blendedLHBStats"];
            }
            else if (hitterStats.Bats == "LH") // Left-Handed Hitter
            {
                relevantBlendedStats = pitcherBlendedStats["blendedLHBStats"];
            }
            else // Right-Handed Hitter
            {
                relevantBlendedStats = pitcherBlendedStats["blendedRHBStats"];
            }
        }
        catch (KeyNotFoundException ex)
        {
            _logger.LogError($"Blended stats key not found: {ex.Message}");
            return 0; // Return 0 or handle this case as needed
        }

        // Calculate probabilities for the hitter's outcomes
        double P_K = CalculateProbability(hitterStats.KPercentage, relevantBlendedStats.K_Percentage);
        double P_BB = CalculateProbability(hitterStats.BBPercentage, relevantBlendedStats.BB_Percentage);
        double P_H = CalculateProbability(hitterStats.BA, relevantBlendedStats.BA) * (1 - P_K);
        double P_HR = P_H * hitterStats.homeRunPercentage;  // Probability of a home run given a hit
        double P_Double = P_H * hitterStats.DoublePercentage;  // Probability of a double given a hit
        double P_Triple = P_H * hitterStats.TriplePercentage;  // Probability of a triple given a hit
        double P_Single = P_H - P_HR - P_Double - P_Triple;  // Probability of a single given a hit
        double P_OUT = 1 - P_H - P_BB;  // Probability of an out (when no hit or walk)

        // Log probabilities for each outcome
        //_logger.LogInformation($"Pitcher: {} vs. Hitter {hitterStats.bbrefId}:");
        //_logger.LogInformation($"Probability of Single: {P_Single:F4}");
        //_logger.LogInformation($"Probability of Double: {P_Double:F4}");
        //_logger.LogInformation($"Probability of Triple: {P_Triple:F4}");
        //_logger.LogInformation($"Probability of Home Run: {P_HR:F4}");
        //_logger.LogInformation($"Probability of Strikeout: {P_K:F4}");
        //_logger.LogInformation($"Probability of Walk: {P_BB:F4}");
        //_logger.LogInformation($"Probability of Out: {P_OUT:F4}");

        // Initialize run value adjustments for different outcomes
        double runValue = 0;

        // Adjust probability selection process
        double randomValue = new Random().NextDouble();

        if (randomValue < P_HR)
        {
            _logger.LogInformation("Outcome: Home Run");
            var result = UpdateBaseStateForHomeRun(baseState);
            baseState = result.Item1;
            runValue += result.Item2;
        }
        else if (randomValue < P_HR + P_Double)
        {
            _logger.LogInformation("Outcome: Double");
            var result = UpdateBaseStateForDouble(baseState);
            baseState = result.Item1;
            runValue += result.Item2;
        }
        else if (randomValue < P_HR + P_Double + P_Triple)
        {
            _logger.LogInformation("Outcome: Triple");
            var result = UpdateBaseStateForTriple(baseState);
            baseState = result.Item1;
            runValue += result.Item2;
        }
        else if (randomValue < P_HR + P_Double + P_Triple + P_Single)
        {
            _logger.LogInformation("Outcome: Single");
            var result = UpdateBaseStateForSingle(baseState);
            baseState = result.Item1;
            runValue += result.Item2;
        }
        else if (randomValue < P_HR + P_Double + P_Triple + P_Single + P_BB)
        {
            _logger.LogInformation("Outcome: Walk");
            var result = UpdateBaseStateForWalk(baseState);
            baseState = result.Item1;
            runValue += result.Item2;
        }
        else
        {
            _logger.LogInformation("Outcome: Out");
            outs++;
            if (outs >= 3)
            {
                outs = 0;
                baseState = 0;
                return runValue;
            }
        }

        return runValue;
    }



    private double AdjustForFactors(double totalExpectedRuns, double ballparkFactor, double handednessFactor, double weatherFactor)
    {
        return totalExpectedRuns * ballparkFactor * handednessFactor * weatherFactor;
    }
    private double CalculateExpectedRuns(Dictionary<string, object> homePitcherBlendedStats, Dictionary<string, object> awayPitcherBlendedStats, List<HitterStatsDto> homeHittersStats, List<HitterStatsDto> awayHittersStats, String homePitcherHandedness, String awayPitcherHandedness)
    {
        double totalExpectedRuns = 0.0;
        double awayExpectedRuns = 0.0;
        double homeExpectedRuns = 0.0;

        int outs = 0;

        // Calculate expected runs for the home team
        foreach (var hitterStats in homeHittersStats)
        {
            //string homePitcherHandedness = homePitcherHandedness; // Replace with actual logic to get handedness
            double expectedRunsForHitter = CalculateExpectedRunsForHitter(hitterStats, awayPitcherBlendedStats, awayPitcherHandedness, outs);
            homeExpectedRuns += expectedRunsForHitter;

            _logger.LogInformation($"Home Hitter {hitterStats.bbrefId} contributed {expectedRunsForHitter} runs to the total.");

            outs = (outs + 1) % 3; // Increment outs, reset to 0 after 3 outs
        }

        outs = 0; // Reset for the away team

        // Calculate expected runs for the away team
        foreach (var hitterStats in awayHittersStats)
        {
            //string awayPitcherHandedness = "RHP"; // Replace with actual logic to get handedness
            double expectedRunsForHitter = CalculateExpectedRunsForHitter(hitterStats, homePitcherBlendedStats, homePitcherHandedness, outs);
            awayExpectedRuns += expectedRunsForHitter;

            _logger.LogInformation($"Away Hitter {hitterStats.bbrefId} contributed {expectedRunsForHitter} runs to the total.");

            outs = (outs + 1) % 3; // Increment outs, reset to 0 after 3 outs
        }
        totalExpectedRuns = (homeExpectedRuns + awayExpectedRuns) - (homeExpectedRuns * awayExpectedRuns);
        return totalExpectedRuns;
    }





}
