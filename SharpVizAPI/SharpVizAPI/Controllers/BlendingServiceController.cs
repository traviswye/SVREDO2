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

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class BlendingController : ControllerBase
    {
        private readonly BlendingService _blendingService;
        private readonly NrfidbContext _context;

        public BlendingController(BlendingService blendingService, NrfidbContext context)
        {
            _blendingService = blendingService;
            _context = context;
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

            // Calculate oOPS using the formula 1.77 * onbase_perc + slugging_perc
            double leagueAverageOPS = ((1.77 * leagueAverageOBP) + leagueAverageSLG);
                

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

                    // Calculate optimized OPS values (1.77 * OBP + SLG)
                    double seasonOOPS = (1.77 * seasonStats.OBP) + seasonStats.SLG;
                    double recentOOPS = recentStats != null ?
                        (1.77 * recentStats.OBP) + recentStats.SLG :
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

        [HttpGet("adjustedRunExpectancy")]
        public async Task<IActionResult> GetAdjustedRunExpectancy([FromQuery] string date = null)
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
            var lineupData = await GetDailyLineupStrength(date); // Pass the string date
            if (lineupData is not OkObjectResult okLineupResult)
            {
                return NotFound("No lineup data available");
            }
            var dailyLineupResponse = (DailyLineupStrengthResponse)okLineupResult.Value;

            // Get pitcher data
            var pitcherData = await GetEnhancedDailyPitcherRankings(date); // Pass the string date
            if (pitcherData is not OkObjectResult okPitcherResult)
            {
                return NotFound("No pitcher data available");
            }

            // Cast the dynamic object to a concrete type
            var pitcherRankings = ((dynamic)okPitcherResult.Value).EnhancedRankings as IEnumerable<dynamic>;
            if (pitcherRankings == null)
            {
                return NotFound("No pitcher rankings available");
            }

            var LEAGUE_AVERAGE_OPS = 0.950; // League average oOPS baseline
            var adjustedGames = new List<object>();

            foreach (var game in dailyLineupResponse.Games)
            {
                // Find pitchers for this game using dynamic object
                dynamic homePitcher = null;
                dynamic awayPitcher = null;

                foreach (dynamic pitcher in pitcherRankings)
                {
                    if ((string)pitcher.PitcherId == game.HomeTeam.OpposingPitcher)
                        awayPitcher = pitcher;  // SWAP: This is now awayPitcher
                    if ((string)pitcher.PitcherId == game.AwayTeam.OpposingPitcher)
                        homePitcher = pitcher;  // SWAP: This is now homePitcher
                }

                // Calculate pitcher oOPS
                double homeOOPS = (1.77 * (double)homePitcher.BlendedStats["OBP"]) + (double)homePitcher.BlendedStats["SLG"];
                double awayOOPS = (1.77 * (double)awayPitcher.BlendedStats["OBP"]) + (double)awayPitcher.BlendedStats["SLG"];

                // Adjust runs based on OPPOSING pitcher's oOPS (this is what changes)
                double homeAdjustedRuns = game.HeadToHead.ExpectedRuns.Team1.ExpectedRuns * (awayOOPS / LEAGUE_AVERAGE_OPS);
                double awayAdjustedRuns = game.HeadToHead.ExpectedRuns.Team2.ExpectedRuns * (homeOOPS / LEAGUE_AVERAGE_OPS);


                adjustedGames.Add(new
                {
                    GameId = game.GameId,
                    HomeTeam = new
                    {
                        Team = game.HomeTeam.Team,
                        OriginalExpectedRuns = game.HeadToHead.ExpectedRuns.Team1.ExpectedRuns,
                        AdjustedExpectedRuns = homeAdjustedRuns,
                        HomePitcherOOPS = homeOOPS  // This stays with home team
                    },
                    AwayTeam = new
                    {
                        Team = game.AwayTeam.Team,
                        OriginalExpectedRuns = game.HeadToHead.ExpectedRuns.Team2.ExpectedRuns,
                        AdjustedExpectedRuns = awayAdjustedRuns,
                        AwayPitcherOOPS = awayOOPS  // This stays with away team
                    },
                    RunDifferential = homeAdjustedRuns - awayAdjustedRuns
                });
                //// Calculate implied probabilities
                //double totalAdjustedRuns = homeAdjustedRuns + awayAdjustedRuns;
                //double homeProbability = homeAdjustedRuns / totalAdjustedRuns;
                //double awayProbability = awayAdjustedRuns / totalAdjustedRuns;

                //// Convert to American odds
                //int homeOdds = homeProbability > 0.5
                //    ? (int)(-100 * (homeProbability / (1 - homeProbability)))
                //    : (int)(100 * ((1 / homeProbability) - 1));
                //int awayOdds = awayProbability > 0.5
                //    ? (int)(-100 * (awayProbability / (1 - awayProbability)))
                //    : (int)(100 * ((1 / awayProbability) - 1));

                //adjustedGames.Add(new
                //{
                //    GameId = game.GameId,
                //    HomeTeam = new
                //    {
                //        Team = game.HomeTeam.Team,
                //        OriginalExpectedRuns = game.HeadToHead.ExpectedRuns.Team1.ExpectedRuns,
                //        AdjustedExpectedRuns = homeAdjustedRuns,
                //        HomePitcherOOPS = homeOOPS,
                //        ImpliedProbability = homeProbability,
                //        MoneyLine = homeOdds
                //    },
                //    AwayTeam = new
                //    {
                //        Team = game.AwayTeam.Team,
                //        OriginalExpectedRuns = game.HeadToHead.ExpectedRuns.Team2.ExpectedRuns,
                //        AdjustedExpectedRuns = awayAdjustedRuns,
                //        AwayPitcherOOPS = awayOOPS,
                //        ImpliedProbability = awayProbability,
                //        MoneyLine = awayOdds
                //    },
                //    RunDifferential = homeAdjustedRuns - awayAdjustedRuns,
                //    TotalExpectedRuns = totalAdjustedRuns
                //});
            }

            return Ok(new
            {
                Date = selectedDate.ToString("yyyy-MM-dd"),
                GamesAnalyzed = adjustedGames.Count,
                LeagueAverageOOPS = LEAGUE_AVERAGE_OPS,
                Games = adjustedGames
            });
        }
    }
}
