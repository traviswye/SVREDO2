using Microsoft.AspNetCore.Mvc;
using SharpVizAPI.Services;
using SharpVizAPI.Data;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using System;
using System.Linq;
using System.Collections.Generic;
using SharpVizAPI.Models;
using SharpVizAPI.Helpers;
using static SharpVizAPI.Services.BlendingService;
using Microsoft.CSharp.RuntimeBinder;
using Microsoft.Extensions.Logging;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class BlendingController : ControllerBase
    {
        private readonly BlendingService _blendingService;
        private readonly BullpenAnalysisService _bullpenService;
        private readonly NrfidbContext _context;
        private readonly ILogger<BlendingController> _logger;

        public BlendingController(BlendingService blendingService, BullpenAnalysisService bullpenService, NrfidbContext context, ILogger<BlendingController> logger)
        {
            _blendingService = blendingService;
            _context = context;
            _bullpenService = bullpenService;
            _logger = logger;
        }

        // This method returns the default weights structure
        [HttpGet("defaultWeights")]
        public IActionResult GetDefaultWeights()
        {
            // Define the default weights as per your current logic
            var defaultWeights = new Dictionary<string, double>
        {
            {"AB/R", 1},
            {"AB/H", 1},
            {"PA/HR", 1},
            {"AB/SB", 0.01},
            {"SB/SB+CS", 0.5}, // Lower is better
            {"PA/BB", 1},
            {"AB/SO", 0.5}, // Lower is better
            {"SOW", 0.5},
            {"BA", 1},  // Lower is better
            {"OBP", 1}, // Lower is better
            {"SLG", 1}, // Lower is better
            {"OPS", 1}, // Lower is better
            {"PA/TB", 1},
            {"AB/GDP", 0.5},
            {"BAbip", 1}, // Lower is better
            {"tOPSPlus", 1},
            {"sOPSPlus", 1}
        };

            return Ok(defaultWeights);
        }

        [HttpGet("todaysSPHistoryVsRecency")]
        public async Task<IActionResult> GetPitchersBlendingResults([FromQuery] string date = null)
        {
            DateTime selectedDate;

            // Parse the input date or default to today's date
            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
            {
                selectedDate = DateTime.Parse(date);
            }
            else
            {
                selectedDate = DateTime.Today;
            }

            // Retrieve games from the gamePreview table for the selected date
            var gamesOnDate = await _context.GamePreviews
                                            .Where(g => g.Date == selectedDate)
                                            .ToListAsync();

            if (gamesOnDate == null || !gamesOnDate.Any())
            {
                return NotFound($"No games found for the date {selectedDate.ToString("yyyy-MM-dd")}.");
            }

            var blendingResults = new List<object>();

            // Loop through each game and get the pitchers
            foreach (var game in gamesOnDate)
            {
                if (!string.IsNullOrEmpty(game.HomePitcher))
                {
                    var homePitcherTrends = await _blendingService.GetBlendingResultsForPitcher(game.HomePitcher);
                    if (homePitcherTrends != null)
                    {
                        var analysisResult = _blendingService.AnalyzeTrends(game.HomePitcher, homePitcherTrends);
                        blendingResults.Add(analysisResult);
                    }
                    else
                    {
                        blendingResults.Add(new { Pitcher = game.HomePitcher, Results = "No data available" });
                    }
                }

                if (!string.IsNullOrEmpty(game.AwayPitcher))
                {
                    var awayPitcherTrends = await _blendingService.GetBlendingResultsForPitcher(game.AwayPitcher);
                    if (awayPitcherTrends != null)
                    {
                        var analysisResult = _blendingService.AnalyzeTrends(game.AwayPitcher, awayPitcherTrends);
                        blendingResults.Add(analysisResult);
                    }
                    else
                    {
                        blendingResults.Add(new { Pitcher = game.AwayPitcher, Results = "No data available" });
                    }
                }
            }

            return Ok(blendingResults);
        }

        // New endpoint for calculating the starting pitcher advantage
        [HttpGet("startingPitcherAdvantage")]
        public async Task<IActionResult> GetStartingPitcherAdvantage([FromQuery] string date = null)
        {
            DateTime selectedDate;

            // Parse the input date or default to today's date
            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
            {
                selectedDate = DateTime.Parse(date);
            }
            else
            {
                selectedDate = DateTime.Today;
            }

            // Call the BlendingService method to calculate the starting pitcher advantage
            var advantageResults = await _blendingService.CalculateStartingPitcherAdvantage(selectedDate);

            if (advantageResults == null || !advantageResults.Any())
            {
                return NotFound($"No advantages found for the date {selectedDate.ToString("yyyy-MM-dd")}.");
            }

            return Ok(advantageResults);
        }



        // New Compare2SP endpoint
        [HttpGet("compare2sp")]
        public async Task<IActionResult> Compare2SP([FromQuery] string pitchera, [FromQuery] string pitcherb)
        {
            // Ensure both pitcher IDs are provided
            if (string.IsNullOrEmpty(pitchera) || string.IsNullOrEmpty(pitcherb))
            {
                return BadRequest("Both pitcherA and pitcherB bbrefId are required.");
            }

            // Call the service method to compare the two pitchers
            var comparisonResult = await _blendingService.Compare2SP(pitchera, pitcherb);

            if (comparisonResult == null || comparisonResult.ContainsKey("message"))
            {
                return NotFound(comparisonResult["message"]);
            }

            // Return the comparison result as JSON
            return Ok(comparisonResult);
        }


        // This is the compare2spCustom method that accepts custom weights
        [HttpGet("compare2spCustom")]
        public async Task<IActionResult> Compare2SPCustom([FromQuery] string pitcheraId, [FromQuery] string pitcherbId, [FromQuery] CustomWeights2SP weights)
        {
            // Define the default weights
            var defaultWeights = new Dictionary<string, double>
    {
        {"AB/R", 1},
        {"AB/H", 1},
        {"PA/HR", 1},
        {"AB/SB", 0.01},
        {"SB/SB+CS", 0.5}, // Lower is better
        {"PA/BB", 1},
        {"AB/SO", 0.5}, // Lower is better
        {"SOW", 0.5},
        {"BA", 1},  // Lower is better
        {"OBP", 1}, // Lower is better
        {"SLG", 1}, // Lower is better
        {"OPS", 1}, // Lower is better
        {"PA/TB", 1},
        {"AB/GDP", 0.5},
        {"BAbip", 1}, // Lower is better
        {"tOPSPlus", 1},
        {"sOPSPlus", 1}
    };

            // Create the custom weights dictionary
            var weightsDict = new Dictionary<string, double>
    {
        {"AB/R", weights.AB_R != 0 ? weights.AB_R : defaultWeights["AB/R"]},
        {"AB/H", weights.AB_H != 0 ? weights.AB_H : defaultWeights["AB/H"]},
        {"PA/HR", weights.PA_HR != 0 ? weights.PA_HR : defaultWeights["PA/HR"]},
        {"AB/SB", weights.AB_SB != 0 ? weights.AB_SB : defaultWeights["AB/SB"]},
        {"SB/SB+CS", weights.SB_SB_CS != 0 ? weights.SB_SB_CS : defaultWeights["SB/SB+CS"]},
        {"PA/BB", weights.PA_BB != 0 ? weights.PA_BB : defaultWeights["PA/BB"]},
        {"AB/SO", weights.AB_SO != 0 ? weights.AB_SO : defaultWeights["AB/SO"]},
        {"SOW", weights.SOW != 0 ? weights.SOW : defaultWeights["SOW"]},
        {"BA", weights.BA != 0 ? weights.BA : defaultWeights["BA"]},
        {"OBP", weights.OBP != 0 ? weights.OBP : defaultWeights["OBP"]},
        {"SLG", weights.SLG != 0 ? weights.SLG : defaultWeights["SLG"]},
        {"OPS", weights.OPS != 0 ? weights.OPS : defaultWeights["OPS"]},
        {"PA/TB", weights.PA_TB != 0 ? weights.PA_TB : defaultWeights["PA/TB"]},
        {"AB/GDP", weights.AB_GDP != 0 ? weights.AB_GDP : defaultWeights["AB/GDP"]},
        {"BAbip", weights.BAbip != 0 ? weights.BAbip : defaultWeights["BAbip"]},
        {"tOPSPlus", weights.tOPSPlus != 0 ? weights.tOPSPlus : defaultWeights["tOPSPlus"]},
        {"sOPSPlus", weights.sOPSPlus != 0 ? weights.sOPSPlus : defaultWeights["sOPSPlus"]}
    };

            var result = await _blendingService.Compare2SPCustom(pitcheraId, pitcherbId, weightsDict);

            if (result.ContainsKey("message"))
            {
                return NotFound(result["message"]);
            }

            return Ok(result);
        }

        [HttpGet("dailyPitcherRankings")]
        public async Task<IActionResult> GetDailyPitcherRankings([FromQuery] string date = null)
        {
            DateTime selectedDate;
            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
            {
                selectedDate = DateTime.Parse(date);
            }
            else
            {
                selectedDate = DateTime.Today;
            }

            var rankings = await _blendingService.GetDailyPitcherRankings(selectedDate);

            if (!rankings.Any())
            {
                return NotFound($"No pitcher rankings found for {selectedDate:yyyy-MM-dd}");
            }

            return Ok(rankings);
        }

        [HttpGet("enhancedDailyPitcherRankings")]
        public async Task<IActionResult> GetEnhancedDailyPitcherRankings([FromQuery] string date = null)
        {
            DateTime selectedDate;
            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
            {
                selectedDate = DateTime.Parse(date);
            }
            else
            {
                selectedDate = DateTime.Today;
            }

            var standardRankings = await _blendingService.GetDailyPitcherRankings(selectedDate);
            var enhancedRankings = await _blendingService.GetEnhancedDailyPitcherRankings(selectedDate);

            if (!enhancedRankings.Any())
            {
                return NotFound($"No enhanced pitcher rankings found for {selectedDate:yyyy-MM-dd}");
            }

            var comparisonData = new
            {
                Date = selectedDate.ToString("yyyy-MM-dd"),
                StandardRankings = standardRankings,
                EnhancedRankings = enhancedRankings,
                Notes = "Enhanced rankings factor in opponent lineup strength, park effects, and weather conditions"
            };

            return Ok(comparisonData);
        }

        [HttpGet("lineupStrength")]
        public async Task<IActionResult> GetLineupStrength([FromQuery] string date = null, [FromQuery] string pitcherId = null)
        {
            DateTime selectedDate;
            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
            {
                selectedDate = DateTime.Parse(date);
            }
            else
            {
                selectedDate = DateTime.Today;
            }

            // Get game preview to find teams
            var gamePreview = await _context.GamePreviews
                .FirstOrDefaultAsync(g => g.Date.Date == selectedDate.Date &&
                    (g.HomePitcher == pitcherId || g.AwayPitcher == pitcherId));

            if (gamePreview == null)
            {
                return NotFound($"No game found for pitcher {pitcherId} on {selectedDate:yyyy-MM-dd}");
            }

            bool isHome = gamePreview.HomePitcher == pitcherId;
            var lineup = await _blendingService.GetLineupForGame(selectedDate, pitcherId, isHome);

            // Get detailed batter stats
            var batterDetails = new List<object>();
            var totalLineupOPS = 0.0;
            var totalRecentOPS = 0.0;
            var validBatterCount = 0;

            foreach (var batterId in lineup)
            {
                var seasonStats = await _context.TrailingGameLogSplits
                    .Where(t => t.BbrefId == batterId && t.Split == "Season")
                    .OrderByDescending(t => t.DateUpdated)
                    .FirstOrDefaultAsync();

                var recentStats = await _context.TrailingGameLogSplits
                    .Where(t => t.BbrefId == batterId && t.Split == "Last7G")
                    .OrderByDescending(t => t.DateUpdated)
                    .FirstOrDefaultAsync();

                if (seasonStats != null)
                {
                    validBatterCount++;
                    totalLineupOPS += seasonStats.OPS;
                    var recentOPS = recentStats?.OPS ?? seasonStats.OPS;
                    totalRecentOPS += recentOPS;

                    batterDetails.Add(new
                    {
                        BatterId = batterId,
                        Position = lineup.IndexOf(batterId) + 1,
                        SeasonStats = new
                        {
                            BA = seasonStats.BA,
                            OBP = seasonStats.OBP,
                            SLG = seasonStats.SLG,
                            OPS = seasonStats.OPS,
                            PA = seasonStats.PA,
                            AB = seasonStats.AB,
                            HR = seasonStats.HR,
                            BB = seasonStats.BB,
                            SO = seasonStats.SO
                        },
                        Last7Stats = recentStats == null ? null : new
                        {
                            BA = recentStats.BA,
                            OBP = recentStats.OBP,
                            SLG = recentStats.SLG,
                            OPS = recentStats.OPS,
                            PA = recentStats.PA,
                            AB = recentStats.AB,
                            HR = recentStats.HR,
                            BB = recentStats.BB,
                            SO = recentStats.SO
                        },
                        WeightedOPS = (seasonStats.OPS * 0.6) + (recentOPS * 0.4),
                        HasRecentStats = recentStats != null
                    });
                }
            }

            // Get league averages
            var leagueStats = await _context.TeamTotalBattingTracking
                .Where(t => t.TeamName == "AL Average" && t.Year == selectedDate.Year)
                .FirstOrDefaultAsync();

            double leagueAverageOPS = leagueStats?.onbase_plus_slugging.HasValue ?? false ?
                Convert.ToDouble(leagueStats.onbase_plus_slugging.Value) : 0.720;
            double avgSeasonOPS = validBatterCount > 0 ? totalLineupOPS / validBatterCount : 0;
            double avgRecentOPS = validBatterCount > 0 ? totalRecentOPS / validBatterCount : 0;
            double blendedLineupOPS = (avgSeasonOPS * 0.6) + (avgRecentOPS * 0.4);

            var result = new
            {
                Date = selectedDate.ToString("yyyy-MM-dd"),
                PitcherId = pitcherId,
                IsHome = isHome,
                OpposingTeam = isHome ? gamePreview.AwayTeam : gamePreview.HomeTeam,
                BatterDetails = batterDetails,
                LineupAverages = new
                {
                    SeasonOPS = avgSeasonOPS,
                    Last7OPS = avgRecentOPS,
                    BlendedOPS = blendedLineupOPS,
                    Weight = new { Season = "70%", Recent = "30%" }
                },
                LeagueAverageOPS = leagueAverageOPS,
                ComparedToLeague = ((blendedLineupOPS - leagueAverageOPS) / leagueAverageOPS * 100).ToString("F1") + "%",
                Warnings = validBatterCount < 9 ? new[] { $"Only found stats for {validBatterCount} out of 9 batters" } : Array.Empty<string>()
            };

            return Ok(result);
        }

        [HttpGet("dailyLineupStrength")]
        public async Task<IActionResult> GetDailyLineupStrength([FromQuery] string date = null)
        {
            DateTime selectedDate;
            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
            {
                selectedDate = DateTime.Parse(date);
            }
            else
            {
                selectedDate = DateTime.Today;
            }

            // Get all games for the selected date
            var gamePreviews = await _context.GamePreviews
                .Where(g => g.Date.Date == selectedDate.Date)
                .ToListAsync();

            if (!gamePreviews.Any())
            {
                return NotFound($"No games found for date {selectedDate:yyyy-MM-dd}");
            }

            // Get league averages for context
            var leagueStats = await _context.TeamTotalBattingTracking
                .Where(t => t.TeamName == "AL Average" && t.Year == selectedDate.Year)
                .FirstOrDefaultAsync();

            double leagueAverageOBP = leagueStats?.onbase_perc.HasValue ?? false ?
                Convert.ToDouble(leagueStats.onbase_perc.Value) : 0.310;

            double leagueAverageSLG = leagueStats?.slugging_perc.HasValue ?? false ?
                Convert.ToDouble(leagueStats.slugging_perc.Value) : 0.390;

            // Calculate oOPS using the formula 1.6 * onbase_perc + slugging_perc
            double leagueAverageOPS = ((1.6 * leagueAverageOBP) + leagueAverageSLG);
                

            var gameLineups = new List<GameLineupAnalysis>();

            foreach (var game in gamePreviews)
            {
                // For each game, get both lineups - the home team is facing the away pitcher and vice versa
                var homeLineup = await _blendingService.GetLineupForGame(selectedDate, game.AwayPitcher, false);
                var awayLineup = await _blendingService.GetLineupForGame(selectedDate, game.HomePitcher, true);

                var homeLineupStats = await AnalyzeLineup(homeLineup, selectedDate);
                var awayLineupStats = await AnalyzeLineup(awayLineup, selectedDate);

                gameLineups.Add(new GameLineupAnalysis
                {
                    GameId = game.Id,
                    Date = selectedDate.ToString("yyyy-MM-dd"),
                    HomeTeam = new TeamLineupAnalysis
                    {
                        Team = game.HomeTeam,
                        OpposingPitcher = game.AwayPitcher,
                        LineupStats = homeLineupStats,
                        ComparedToLeague = ((homeLineupStats.BlendedOPS - leagueAverageOPS) / leagueAverageOPS * 100).ToString("F1") + "%"
                    },
                    AwayTeam = new TeamLineupAnalysis
                    {
                        Team = game.AwayTeam,
                        OpposingPitcher = game.HomePitcher,
                        LineupStats = awayLineupStats,
                        ComparedToLeague = ((awayLineupStats.BlendedOPS - leagueAverageOPS) / leagueAverageOPS * 100).ToString("F1") + "%"
                    },
                    HeadToHead = OPSHelper.CompareLineups(homeLineupStats.BlendedOPS, game.HomeTeam,
                                                        awayLineupStats.BlendedOPS, game.AwayTeam,
                                                        homeLineupStats, awayLineupStats)
                });
            }

            var result = new DailyLineupStrengthResponse
            {
                Date = selectedDate.ToString("yyyy-MM-dd"),
                GamesAnalyzed = gamePreviews.Count,
                LeagueAverageOPS = leagueAverageOPS,
                Games = gameLineups.OrderBy(g => g.GameId).ToList(),
                DailyOverview = new DailyLineupOverview
                {
                    StrongestLineup = gameLineups
                        .SelectMany(g => new[]
                        {
                    new TeamOPS { Team = g.HomeTeam.Team, OPS = g.HomeTeam.LineupStats.BlendedOPS },
                    new TeamOPS { Team = g.AwayTeam.Team, OPS = g.AwayTeam.LineupStats.BlendedOPS }
                        })
                        .OrderByDescending(t => t.OPS)
                        .First(),
                    WeakestLineup = gameLineups
                        .SelectMany(g => new[]
                        {
                    new TeamOPS { Team = g.HomeTeam.Team, OPS = g.HomeTeam.LineupStats.BlendedOPS },
                    new TeamOPS { Team = g.AwayTeam.Team, OPS = g.AwayTeam.LineupStats.BlendedOPS }
                        })
                        .OrderBy(t => t.OPS)
                        .First()
                }
            };

            return Ok(result);
        }

        private async Task<LineupStats> AnalyzeLineup(List<string> lineup, DateTime selectedDate)
        {
            var batterDetails = new List<BatterDetail>();
            var validBatterCount = 0;

            // Track total weighted OPS*PA and total PA for both season and recent
            var seasonOPSxPA = 0.0;
            var seasonTotalPA = 0;
            var recentOPSxPA = 0.0;
            var recentTotalPA = 0;

            foreach (var batterId in lineup)
            {
                var seasonStats = await _context.TrailingGameLogSplits
                    .Where(t => t.BbrefId == batterId && t.Split == "Season")
                    .OrderByDescending(t => t.DateUpdated)
                    .FirstOrDefaultAsync();

                var recentStats = await _context.TrailingGameLogSplits
                    .Where(t => t.BbrefId == batterId && t.Split == "Last7G")
                    .OrderByDescending(t => t.DateUpdated)
                    .FirstOrDefaultAsync();

                if (seasonStats != null)
                {
                    validBatterCount++;

                    // Calculate optimized OPS values (1.6 * OBP + SLG)
                    double seasonOOPS = (1.6 * seasonStats.OBP) + seasonStats.SLG;
                    double recentOOPS = recentStats != null ?
                        (1.6 * recentStats.OBP) + recentStats.SLG :
                        seasonOOPS;

                    // Add to season totals
                    seasonOPSxPA += (seasonOOPS * seasonStats.PA);
                    seasonTotalPA += seasonStats.PA;

                    // Add to recent totals if available
                    if (recentStats != null)
                    {
                        recentOPSxPA += (recentOOPS * recentStats.PA);
                        recentTotalPA += recentStats.PA;
                    }

                    batterDetails.Add(new BatterDetail
                    {
                        BatterId = batterId,
                        Position = lineup.IndexOf(batterId) + 1,
                        SeasonStats = new BattingStats
                        {
                            BA = seasonStats.BA,
                            OBP = seasonStats.OBP,
                            SLG = seasonStats.SLG,
                            OPS = seasonOOPS,  // Store optimized OPS here
                            PA = seasonStats.PA,
                            AB = seasonStats.AB,
                            HR = seasonStats.HR,
                            BB = seasonStats.BB,
                            SO = seasonStats.SO
                        },
                        Last7Stats = recentStats == null ? null : new BattingStats
                        {
                            BA = recentStats.BA,
                            OBP = recentStats.OBP,
                            SLG = recentStats.SLG,
                            OPS = recentOOPS,  // Store optimized OPS here
                            PA = recentStats.PA,
                            AB = recentStats.AB,
                            HR = recentStats.HR,
                            BB = recentStats.BB,
                            SO = recentStats.SO
                        },
                        WeightedOPS = (seasonOOPS * 0.7) + (recentOOPS * 0.3),
                        HasRecentStats = recentStats != null
                    });
                }
            }

            // Calculate PA-weighted averages using optimized OPS
            double avgSeasonOPS = seasonTotalPA > 0 ? seasonOPSxPA / seasonTotalPA : 0;
            double avgRecentOPS = recentTotalPA > 0 ? recentOPSxPA / recentTotalPA : 0;

            // If we don't have recent stats for some reason, use season OPS
            if (recentTotalPA == 0)
            {
                avgRecentOPS = avgSeasonOPS;
            }

            // Calculate blended OPS using the weighted averages
            double blendedLineupOPS = (avgSeasonOPS * 0.7) + (avgRecentOPS * 0.3);

            return new LineupStats
            {
                BatterDetails = batterDetails,
                SeasonOPS = avgSeasonOPS,
                Last7OPS = avgRecentOPS,
                BlendedOPS = blendedLineupOPS,
                Weight = new WeightDistribution { Season = "70%", Recent = "30%" },
                Warnings = validBatterCount < 9 ? new[] { $"Only found stats for {validBatterCount} out of 9 batters" } : Array.Empty<string>()
            };
        }

        [HttpGet("adjustedRunExpectancyF5")]
        public async Task<IActionResult> GetAdjustedRunExpectancy([FromQuery] string date = null)
        {
            try
            {
                DateTime selectedDate;
                if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
                {
                    selectedDate = DateTime.Parse(date);
                }
                else
                {
                    selectedDate = DateTime.Today;
                }

                // Get lineup strength data
                var lineupData = await GetDailyLineupStrength(date);
                if (lineupData is not OkObjectResult okLineupResult)
                {
                    return NotFound("No lineup data available");
                }
                var dailyLineupResponse = (DailyLineupStrengthResponse)okLineupResult.Value;

                // Get pitcher data
                var pitcherData = await GetEnhancedDailyPitcherRankings(date);
                if (pitcherData is not OkObjectResult okPitcherResult)
                {
                    return NotFound("No pitcher data available");
                }

                // Safely extract enhanced rankings
                var pitcherRankings = GetEnhancedRankings(okPitcherResult.Value);
                if (pitcherRankings == null || !pitcherRankings.Any())
                {
                    return NotFound("No pitcher rankings available");
                }

                // Define constants
                var LEAGUE_AVERAGE_OPS = 0.886; // League average oOPS baseline
                const double FIVE_INNING_SCALAR = 5.0 / 9.0;
                var adjustedGames = new List<object>();

                // Default OBP/SLG values for missing data
                const double DEFAULT_OBP = 0.330;
                const double DEFAULT_SLG = 0.420;

                // Process each game
                foreach (var game in dailyLineupResponse.Games)
                {
                    try
                    {
                        // Find pitchers for this game using dynamic object
                        dynamic homePitcher = null;
                        dynamic awayPitcher = null;
                        string homePitcherId = game.AwayTeam.OpposingPitcher;
                        string awayPitcherId = game.HomeTeam.OpposingPitcher;

                        // Log pitcher IDs for debugging
                        _logger.LogInformation($"Looking for home pitcher ID: {homePitcherId}, away pitcher ID: {awayPitcherId}");

                        foreach (dynamic pitcher in pitcherRankings)
                        {
                            string pitcherId = (string)pitcher.PitcherId;

                            if (pitcherId == awayPitcherId)
                                awayPitcher = pitcher;
                            if (pitcherId == homePitcherId)
                                homePitcher = pitcher;
                        }

                        // Check if we found the pitchers
                        if (homePitcher == null || awayPitcher == null)
                        {
                            _logger.LogWarning($"Missing pitcher data for game {game.GameId} - " +
                                $"Home pitcher ({homePitcherId}): {(homePitcher == null ? "NOT FOUND" : "FOUND")}, " +
                                $"Away pitcher ({awayPitcherId}): {(awayPitcher == null ? "NOT FOUND" : "FOUND")}");

                            // Skip this game or continue with default values
                            continue;
                        }

                        // Safely access BlendedStats with fallback values
                        double homeOBP = GetSafeBlendedStat(homePitcher, "OBP", DEFAULT_OBP);
                        double homeSLG = GetSafeBlendedStat(homePitcher, "SLG", DEFAULT_SLG);
                        double awayOBP = GetSafeBlendedStat(awayPitcher, "OBP", DEFAULT_OBP);
                        double awaySLG = GetSafeBlendedStat(awayPitcher, "SLG", DEFAULT_SLG);

                        // Calculate pitcher oOPS
                        double homeOOPS = (1.6 * homeOBP) + homeSLG;
                        double awayOOPS = (1.6 * awayOBP) + awaySLG;

                        // Adjust runs based on OPPOSING pitcher's oOPS
                        double homeAdjustedRuns = game.HeadToHead.ExpectedRuns.Team1.ExpectedRuns * (awayOOPS / LEAGUE_AVERAGE_OPS);
                        double awayAdjustedRuns = game.HeadToHead.ExpectedRuns.Team2.ExpectedRuns * (homeOOPS / LEAGUE_AVERAGE_OPS);

                        adjustedGames.Add(new
                        {
                            GameId = game.GameId,
                            HomeTeam = new
                            {
                                Team = game.HomeTeam.Team,
                                OriginalExpectedRuns = game.HeadToHead.ExpectedRuns.Team1.ExpectedRuns * FIVE_INNING_SCALAR,  // Scale to 5 innings
                                AdjustedExpectedRuns = homeAdjustedRuns * FIVE_INNING_SCALAR,  // Scale to 5 innings
                                HomePitcherOOPS = homeOOPS
                            },
                            AwayTeam = new
                            {
                                Team = game.AwayTeam.Team,
                                OriginalExpectedRuns = game.HeadToHead.ExpectedRuns.Team2.ExpectedRuns * FIVE_INNING_SCALAR,  // Scale to 5 innings
                                AdjustedExpectedRuns = awayAdjustedRuns * FIVE_INNING_SCALAR,  // Scale to 5 innings
                                AwayPitcherOOPS = awayOOPS
                            },
                            RunDifferential = (homeAdjustedRuns - awayAdjustedRuns) * FIVE_INNING_SCALAR  // Scale differential to 5 innings
                        });
                    }
                    catch (Exception ex)
                    {
                        // Log error and continue with next game
                        _logger.LogError(ex, $"Error processing game {game.GameId}: {ex.Message}");
                        continue;
                    }
                }

                // Check if we processed any games
                if (!adjustedGames.Any())
                {
                    return NotFound("Could not process any games with the available data");
                }

                return Ok(new
                {
                    Date = selectedDate.ToString("yyyy-MM-dd"),
                    GamesAnalyzed = adjustedGames.Count,
                    LeagueAverageOOPS = LEAGUE_AVERAGE_OPS,
                    Games = adjustedGames
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in GetAdjustedRunExpectancy: " + ex.Message);
                return StatusCode(500, "An error occurred while calculating adjusted run expectancy");
            }
        }

        [HttpGet("adjustedRunExpectancy")]
        public async Task<IActionResult> GetFullGameAdjustedRunExpectancy([FromQuery] string date = null)
        {
            try
            {
                DateTime selectedDate;
                if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
                {
                    selectedDate = DateTime.Parse(date);
                }
                else
                {
                    selectedDate = DateTime.Today;
                }

                // Get lineup strength data
                var lineupData = await GetDailyLineupStrength(date);
                if (lineupData is not OkObjectResult okLineupResult)
                {
                    return NotFound("No lineup data available");
                }
                var dailyLineupResponse = (DailyLineupStrengthResponse)okLineupResult.Value;

                // Get pitcher data
                var pitcherData = await GetEnhancedDailyPitcherRankings(date);
                if (pitcherData is not OkObjectResult okPitcherResult)
                {
                    return NotFound("No pitcher data available");
                }

                // Safely extract enhanced rankings
                var pitcherRankings = GetEnhancedRankings(okPitcherResult.Value);
                if (pitcherRankings == null || !pitcherRankings.Any())
                {
                    return NotFound("No pitcher rankings available");
                }

                // Define constants
                var LEAGUE_AVERAGE_OPS = 0.886; // League average oOPS baseline
                const double STARTER_INNINGS = 5.0 / 9.0;
                const double BULLPEN_INNINGS = 4.0 / 9.0;
                var adjustedGames = new List<object>();

                // Default OBP/SLG values for missing data
                const double DEFAULT_OBP = 0.330;
                const double DEFAULT_SLG = 0.420;
                const double DEFAULT_BULLPEN_OOPS = 0.750;

                // Process each game
                foreach (var game in dailyLineupResponse.Games)
                {
                    try
                    {
                        // Find starting pitchers
                        dynamic homePitcher = null;
                        dynamic awayPitcher = null;
                        string homePitcherId = game.AwayTeam.OpposingPitcher;
                        string awayPitcherId = game.HomeTeam.OpposingPitcher;

                        // Log pitcher IDs for debugging
                        _logger.LogInformation($"Looking for home pitcher ID: {homePitcherId}, away pitcher ID: {awayPitcherId}");

                        foreach (dynamic pitcher in pitcherRankings)
                        {
                            string pitcherId = (string)pitcher.PitcherId;

                            if (pitcherId == awayPitcherId)
                                awayPitcher = pitcher;
                            if (pitcherId == homePitcherId)
                                homePitcher = pitcher;
                        }

                        // Check if we found the pitchers
                        if (homePitcher == null || awayPitcher == null)
                        {
                            _logger.LogWarning($"Missing pitcher data for game {game.GameId} - " +
                                $"Home pitcher ({homePitcherId}): {(homePitcher == null ? "NOT FOUND" : "FOUND")}, " +
                                $"Away pitcher ({awayPitcherId}): {(awayPitcher == null ? "NOT FOUND" : "FOUND")}");

                            // Skip this game or continue with default values
                            continue;
                        }

                        // Get bullpen stats for both teams with error handling
                        var homeTeamAbbrev = TeamNameMapper.GetAbbreviation(game.HomeTeam.Team);
                        var awayTeamAbbrev = TeamNameMapper.GetAbbreviation(game.AwayTeam.Team);

                        _logger.LogInformation($"Getting bullpen stats for {homeTeamAbbrev} and {awayTeamAbbrev}");

                        var homeBullpenStats = await GetBullpenStatsWithFallback(selectedDate.Year, homeTeamAbbrev, selectedDate);
                        var awayBullpenStats = await GetBullpenStatsWithFallback(selectedDate.Year, awayTeamAbbrev, selectedDate);

                        // Safely access BlendedStats with fallback values
                        double homeOBP = GetSafeBlendedStat(homePitcher, "OBP", DEFAULT_OBP);
                        double homeSLG = GetSafeBlendedStat(homePitcher, "SLG", DEFAULT_SLG);
                        double awayOBP = GetSafeBlendedStat(awayPitcher, "OBP", DEFAULT_OBP);
                        double awaySLG = GetSafeBlendedStat(awayPitcher, "SLG", DEFAULT_SLG);

                        // Calculate starter oOPS
                        double homeStarterOOPS = (1.6 * homeOBP) + homeSLG;
                        double awayStarterOOPS = (1.6 * awayOBP) + awaySLG;

                        // Calculate adjusted runs for first 5 innings (starters)
                        double homeFirstFive = game.HeadToHead.ExpectedRuns.Team1.ExpectedRuns * (awayStarterOOPS / LEAGUE_AVERAGE_OPS) * STARTER_INNINGS;
                        double awayFirstFive = game.HeadToHead.ExpectedRuns.Team2.ExpectedRuns * (homeStarterOOPS / LEAGUE_AVERAGE_OPS) * STARTER_INNINGS;

                        // Get safe bullpen OOPS values with validation against infinity/NaN
                        double homeBullpenOOPS = GetSafeOOPSValue(homeBullpenStats?.OOPS, DEFAULT_BULLPEN_OOPS);
                        double awayBullpenOOPS = GetSafeOOPSValue(awayBullpenStats?.OOPS, DEFAULT_BULLPEN_OOPS);

                        // Calculate adjusted runs for last 4 innings (bullpen)
                        double homeLastFour = game.HeadToHead.ExpectedRuns.Team1.ExpectedRuns *
                            SafeDivide(awayBullpenOOPS, LEAGUE_AVERAGE_OPS) * BULLPEN_INNINGS;

                        double awayLastFour = game.HeadToHead.ExpectedRuns.Team2.ExpectedRuns *
                            SafeDivide(homeBullpenOOPS, LEAGUE_AVERAGE_OPS) * BULLPEN_INNINGS;

                        // Combine for full game expectations
                        double homeTotalAdjusted = homeFirstFive + homeLastFour;
                        double awayTotalAdjusted = awayFirstFive + awayLastFour;

                        adjustedGames.Add(new
                        {
                            GameId = game.GameId,
                            HomeTeam = new
                            {
                                Team = game.HomeTeam.Team,
                                OriginalExpectedRuns = game.HeadToHead.ExpectedRuns.Team1.ExpectedRuns,
                                AdjustedExpectedRuns = homeTotalAdjusted,
                                StarterOOPS = homeStarterOOPS,
                                BullpenOOPS = homeBullpenOOPS
                            },
                            AwayTeam = new
                            {
                                Team = game.AwayTeam.Team,
                                OriginalExpectedRuns = game.HeadToHead.ExpectedRuns.Team2.ExpectedRuns,
                                AdjustedExpectedRuns = awayTotalAdjusted,
                                StarterOOPS = awayStarterOOPS,
                                BullpenOOPS = awayBullpenOOPS
                            },
                            RunDifferential = homeTotalAdjusted - awayTotalAdjusted
                        });
                    }
                    catch (Exception ex)
                    {
                        // Log error and continue with next game
                        _logger.LogError(ex, $"Error processing game {game.GameId}: {ex.Message}");
                        continue;
                    }
                }

                // Check if we processed any games
                if (!adjustedGames.Any())
                {
                    return NotFound("Could not process any games with the available data");
                }

                return Ok(new
                {
                    Date = selectedDate.ToString("yyyy-MM-dd"),
                    GamesAnalyzed = adjustedGames.Count,
                    LeagueAverageOOPS = LEAGUE_AVERAGE_OPS,
                    Games = adjustedGames
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in GetFullGameAdjustedRunExpectancy: " + ex.Message);
                return StatusCode(500, "An error occurred while calculating adjusted run expectancy");
            }
        }

        // Helper methods for safer access to dynamic objects and properties


        private double GetSafeOOPSValue(dynamic oopsValue, double defaultValue)
        {
            try
            {
                if (oopsValue == null)
                    return defaultValue;

                double value = Convert.ToDouble(oopsValue);

                // Check for invalid values
                if (double.IsInfinity(value) || double.IsNaN(value) || value <= 0 || value > 2.0)
                {
                    _logger.LogWarning($"Invalid OOPS value: {value}, using default");
                    return defaultValue;
                }

                return value;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error converting OOPS value: {ex.Message}");
                return defaultValue;
            }
        }

        private double SafeDivide(double numerator, double denominator)
        {
            // Avoid division by zero and other problematic cases
            if (denominator == 0 || double.IsInfinity(denominator) || double.IsNaN(denominator))
                return 1.0; // Neutral value

            if (double.IsInfinity(numerator) || double.IsNaN(numerator))
                return 1.0; // Neutral value

            double result = numerator / denominator;

            // Check if result is valid
            if (double.IsInfinity(result) || double.IsNaN(result))
                return 1.0; // Neutral value

            // Limit extreme values
            if (result > 3.0) return 3.0;
            if (result < 0.1) return 0.1;

            return result;
        }


        // Helper method to create a default bullpen stats object
        private dynamic CreateDefaultBullpenStats()
        {
            // Create an anonymous object with default values
            return new
            {
                OOPS = 0.750,  // League average-ish value
                ERA = 4.00,
                WHIP = 1.30,
                IsDefault = true  // Flag to indicate this is default data
            };
        }
        // Helper methods for safer access to dynamic objects and properties

        private IEnumerable<dynamic> GetEnhancedRankings(dynamic resultValue)
        {
            try
            {
                var rankings = resultValue?.EnhancedRankings as IEnumerable<dynamic>;
                if (rankings == null)
                {
                    _logger.LogWarning("Enhanced rankings property not found or is null");
                    return Enumerable.Empty<dynamic>();
                }
                return rankings;
            }
            catch (RuntimeBinderException ex)
            {
                _logger.LogError(ex, "Error accessing EnhancedRankings property");
                return Enumerable.Empty<dynamic>();
            }
        }

        //private double GetSafeBlendedStat(dynamic pitcher, string statName, double defaultValue)
        //{
        //    try
        //    {
        //        if (pitcher == null)
        //            return defaultValue;

        //        var blendedStats = pitcher.BlendedStats as IDictionary<string, object>;
        //        if (blendedStats == null || !blendedStats.ContainsKey(statName))
        //            return defaultValue;

        //        return Convert.ToDouble(blendedStats[statName]);
        //    }
        //    catch (Exception ex)
        //    {
        //        _logger.LogError(ex, $"Error accessing BlendedStats[{statName}]");
        //        return defaultValue;
        //    }
        //}

        private double GetSafeBlendedStat(dynamic pitcher, string statName, double defaultValue)
        {
            try
            {
                if (pitcher == null)
                {
                    _logger.LogWarning($"Pitcher object is null when trying to access {statName}");
                    return defaultValue;
                }

                // Log the type of the pitcher object
                _logger.LogInformation($"Pitcher type: {pitcher.GetType().FullName}");

                // Try to access BlendedStats and log its type
                var blendedStatsObj = pitcher.BlendedStats;
                if (blendedStatsObj == null)
                {
                    _logger.LogWarning($"BlendedStats is null for pitcher {pitcher.PitcherId}");
                    return defaultValue;
                }

                _logger.LogInformation($"BlendedStats type: {blendedStatsObj.GetType().FullName}");

                var blendedStats = blendedStatsObj as IDictionary<string, object>;
                if (blendedStats == null)
                {
                    _logger.LogWarning($"Failed to cast BlendedStats to IDictionary<string, object> for pitcher {pitcher.PitcherId}");

                    // Try a different approach - maybe it's a different dictionary type or a dynamic object
                    try
                    {
                        var value = blendedStatsObj[statName];
                        _logger.LogInformation($"Successfully retrieved {statName}={value} directly from BlendedStats");
                        return Convert.ToDouble(value);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, $"Failed alternative access method for BlendedStats[{statName}]");
                        return defaultValue;
                    }
                }

                if (!blendedStats.ContainsKey(statName))
                {
                    _logger.LogWarning($"BlendedStats does not contain key '{statName}' for pitcher {pitcher.PitcherId}");
                    return defaultValue;
                }

                var statValue = blendedStats[statName];
                _logger.LogInformation($"Successfully retrieved {statName}={statValue} for pitcher {pitcher.PitcherId}");
                return Convert.ToDouble(statValue);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error accessing BlendedStats[{statName}]");
                return defaultValue;
            }
        }

        private async Task<dynamic> GetBullpenStatsWithFallback(int year, string teamAbbrev, DateTime date)
        {
            try
            {
                if (string.IsNullOrEmpty(teamAbbrev))
                {
                    _logger.LogWarning($"Team abbreviation is null or empty for date {date}");
                    return null;
                }

                var bullpenStats = await _bullpenService.GetBullpenAnalysis(year, teamAbbrev, date);

                // Log if we couldn't find bullpen stats
                if (bullpenStats == null)
                {
                    _logger.LogWarning($"No bullpen stats found for {teamAbbrev} on {date}");
                }

                return bullpenStats;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting bullpen stats for {teamAbbrev} on {date}");
                return null;
            }
        }

        [HttpGet("calculateWoba")]
        public async Task<IActionResult> CalculateWoba([FromQuery] string bbrefId)
        {


            // Get season and recent splits
            var seasonSplit = await _context.TrailingGameLogSplits
                .Where(t => t.BbrefId == bbrefId && t.Split == "Season")
                .OrderByDescending(t => t.DateUpdated)
                .FirstOrDefaultAsync();

            var last7Split = await _context.TrailingGameLogSplits
                .Where(t => t.BbrefId == bbrefId && t.Split == "Last7G")
                .OrderByDescending(t => t.DateUpdated)
                .FirstOrDefaultAsync();

            if (seasonSplit == null)
            {
                return NotFound($"No stats found for player {bbrefId}");
            }

            // Calculate wOBA for season stats
            double seasonWoba = WobaCalculator.CalculateWoba(seasonSplit);
            double? last7Woba = last7Split != null ? WobaCalculator.CalculateWoba(last7Split) : null;

            // Calculate blended wOBA if we have both splits (70/30 weight)
            double? blendedWoba = last7Split != null ?
                (seasonWoba * 0.7) + (last7Woba.Value * 0.3) :
                seasonWoba;

            var result = new
            {
                BbrefId = bbrefId,
                SeasonStats = new
                {
                    wOBA = seasonWoba,
                    PA = seasonSplit.PA,
                    Singles = seasonSplit.H - (seasonSplit.HR + seasonSplit.Doubles + seasonSplit.Triples),
                    Doubles = seasonSplit.Doubles,
                    Triples = seasonSplit.Triples,
                    HR = seasonSplit.HR,
                    BB = seasonSplit.BB,
                    HBP = seasonSplit.HBP,
                    SF = seasonSplit.SF
                },
                Last7Stats = last7Split != null ? new
                {
                    wOBA = last7Woba.Value,
                    PA = last7Split.PA,
                    Singles = last7Split.H - (last7Split.HR + last7Split.Doubles + last7Split.Triples),
                    Doubles = last7Split.Doubles,
                    Triples = last7Split.Triples,
                    HR = last7Split.HR,
                    BB = last7Split.BB,
                    HBP = last7Split.HBP,
                    SF = last7Split.SF
                } : null,
                BlendedWoba = blendedWoba,
                WeightDistribution = new { Season = "70%", Recent = "30%" }
            };

            return Ok(result);
        }


        [HttpPost("calculateWobaMultiple")]
        public async Task<IActionResult> CalculateWobaMultiple([FromBody] List<string> bbrefIds)
        {
            if (bbrefIds == null || !bbrefIds.Any())
            {
                return BadRequest("No player IDs provided");
            }

            var results = new List<object>();

            // Get all relevant splits in one query for better performance
            var seasonSplits = await _context.TrailingGameLogSplits
                .Where(t => bbrefIds.Contains(t.BbrefId) && t.Split == "Season")
                .OrderByDescending(t => t.DateUpdated)
                .ToListAsync();

            var last7Splits = await _context.TrailingGameLogSplits
                .Where(t => bbrefIds.Contains(t.BbrefId) && t.Split == "Last7G")
                .OrderByDescending(t => t.DateUpdated)
                .ToListAsync();

            foreach (var bbrefId in bbrefIds)
            {
                var seasonSplit = seasonSplits.FirstOrDefault(s => s.BbrefId == bbrefId);
                var last7Split = last7Splits.FirstOrDefault(s => s.BbrefId == bbrefId);

                if (seasonSplit == null)
                {
                    results.Add(new
                    {
                        BbrefId = bbrefId,
                        Error = $"No stats found for player {bbrefId}"
                    });
                    continue;
                }

                // Calculate wOBA for season stats
                double seasonWoba = WobaCalculator.CalculateWoba(seasonSplit);
                double? last7Woba = last7Split != null ? WobaCalculator.CalculateWoba(last7Split) : null;

                // Calculate blended wOBA if we have both splits (70/30 weight)
                double? blendedWoba = last7Split != null ?
                    (seasonWoba * 0.7) + (last7Woba.Value * 0.3) :
                    seasonWoba;

                results.Add(new
                {
                    BbrefId = bbrefId,
                    SeasonStats = new
                    {
                        wOBA = seasonWoba,
                        PA = seasonSplit.PA,
                        Singles = seasonSplit.H - (seasonSplit.HR + seasonSplit.Doubles + seasonSplit.Triples),
                        Doubles = seasonSplit.Doubles,
                        Triples = seasonSplit.Triples,
                        HR = seasonSplit.HR,
                        BB = seasonSplit.BB,
                        HBP = seasonSplit.HBP,
                        SF = seasonSplit.SF
                    },
                    Last7Stats = last7Split != null ? new
                    {
                        wOBA = last7Woba.Value,
                        PA = last7Split.PA,
                        Singles = last7Split.H - (last7Split.HR + last7Split.Doubles + last7Split.Triples),
                        Doubles = last7Split.Doubles,
                        Triples = last7Split.Triples,
                        HR = last7Split.HR,
                        BB = last7Split.BB,
                        HBP = last7Split.HBP,
                        SF = last7Split.SF
                    } : null,
                    BlendedWoba = blendedWoba,
                    WeightDistribution = new { Season = "70%", Recent = "30%" }
                });
            }

            return Ok(new
            {
                ProcessedPlayers = results.Count,
                Results = results
            });
        }
    }
    public static class TeamNameMapper
    {
        private static readonly Dictionary<string, string> FullNameToAbbrev = new Dictionary<string, string>
    {
        { "Yankees", "NYY" },
        { "Red Sox", "BOS" },
        { "Blue Jays", "TOR" },
        { "Rays", "TBR" },
        { "Orioles", "BAL" },
        { "White Sox", "CHW" },
        { "Guardians", "CLE" },
        { "Tigers", "DET" },
        { "Royals", "KCR" },
        { "Twins", "MIN" },
        { "Angels", "LAA" },
        { "Astros", "HOU" },
        { "Athletics", "OAK" },
        { "Mariners", "SEA" },
        { "Rangers", "TEX" },
        { "Braves", "ATL" },
        { "Marlins", "MIA" },
        { "Mets", "NYM" },
        { "Phillies", "PHI" },
        { "Nationals", "WSN" },
        { "Cubs", "CHC" },
        { "Reds", "CIN" },
        { "Brewers", "MIL" },
        { "Pirates", "PIT" },
        { "Cardinals", "STL" },
        { "Diamondbacks", "ARI" },
        { "Rockies", "COL" },
        { "Dodgers", "LAD" },
        { "Padres", "SDP" },
        { "Giants", "SFG" }
    };

        public static string GetAbbreviation(string fullName)
        {
            // Try to get exact match first
            if (FullNameToAbbrev.TryGetValue(fullName, out string abbrev))
                return abbrev;

            // If not found, try removing leading/trailing spaces and try again
            fullName = fullName.Trim();
            if (FullNameToAbbrev.TryGetValue(fullName, out abbrev))
                return abbrev;

            // If still not found, throw an exception with details
            throw new ArgumentException($"Team name '{fullName}' not found in mapping dictionary.");
        }
    }
}
