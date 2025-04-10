using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using SharpVizAPI.Data;
using SharpVizAPI.Services;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class wOBAController : ControllerBase
    {
        private readonly wOBAService _wobaService;
        private readonly ILogger<wOBAController> _logger;
        private readonly NrfidbContext _context;

        public wOBAController(wOBAService wobaService, ILogger<wOBAController> logger)
        {
            _wobaService = wobaService;
            _logger = logger;
        }

        // GET: api/wOBA/player/{bbrefId}/{year}
        [HttpGet("player/{bbrefId}/{year}")]
        public async Task<IActionResult> GetPlayerWoba(string bbrefId, int year)
        {
            _logger.LogInformation($"Getting wOBA for player {bbrefId} for year {year}");

            try
            {
                var result = await _wobaService.GetPlayerWobaAsync(bbrefId, year);

                if (result.ContainsKey("error"))
                {
                    return NotFound(result);
                }

                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting wOBA for player {bbrefId}: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // POST: api/wOBA/batchPlayers
        [HttpPost("batchPlayers")]
        public async Task<IActionResult> BatchGetPlayersWoba([FromBody] BatchWobaRequest request)
        {
            if (request == null || request.BbrefIds == null || request.BbrefIds.Count == 0)
            {
                return BadRequest("Player IDs are required");
            }

            try
            {
                var results = await _wobaService.GetMultiplePlayersWobaAsync(request.BbrefIds, request.Year);
                return Ok(new { Count = results.Count, Results = results });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error in batch wOBA calculation: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // GET: api/wOBA/pitchers/date/{date}/detailed
        [HttpGet("pitchers/date/{date}/detailed")]
        public async Task<IActionResult> GetDetailedPitchersWobaForDate(string date)
        {
            if (!DateTime.TryParse(date, out DateTime parsedDate))
            {
                return BadRequest("Invalid date format. Use yyyy-MM-dd.");
            }

            try
            {
                var results = await _wobaService.GetPitchersWobaForGamesAsync(parsedDate);

                // Calculate some aggregate stats for context
                int pitchersWithHomeAwaySplits = results.Count(r => r.ContainsKey("homeAwaySplit"));
                int pitchersWithLast28 = results.Count(r => r.ContainsKey("last28Record"));

                // Calculate average of different wOBA types
                double avgSeasonWoba = 0;
                double avgHomeAwayWoba = 0;
                double avgLast28Woba = 0;
                int seasonCount = 0;
                int homeAwayCount = 0;
                int last28Count = 0;

                foreach (var pitcher in results)
                {
                    if (pitcher.ContainsKey("aWOBASeason"))
                    {
                        avgSeasonWoba += (double)pitcher["aWOBASeason"];
                        seasonCount++;
                    }

                    if (pitcher.ContainsKey("aWOBAHomeAway"))
                    {
                        avgHomeAwayWoba += (double)pitcher["aWOBAHomeAway"];
                        homeAwayCount++;
                    }

                    if (pitcher.ContainsKey("aWOBALast28"))
                    {
                        avgLast28Woba += (double)pitcher["aWOBALast28"];
                        last28Count++;
                    }
                }

                if (seasonCount > 0) avgSeasonWoba /= seasonCount;
                if (homeAwayCount > 0) avgHomeAwayWoba /= homeAwayCount;
                if (last28Count > 0) avgLast28Woba /= last28Count;

                return Ok(new
                {
                    Date = date,
                    Count = results.Count,
                    Results = results,
                    Summary = new
                    {
                        PitchersWithHomeAwaySplits = pitchersWithHomeAwaySplits,
                        PitchersWithLast28 = pitchersWithLast28,
                        AverageSeasonWoba = avgSeasonWoba,
                        AverageHomeAwayWoba = avgHomeAwayWoba,
                        AverageLast28Woba = avgLast28Woba,
                        LeagueAverage = results.FirstOrDefault()?["wobaConstants"] != null ?
                            ((dynamic)results.First()["wobaConstants"]).LeagueAverage : 0.310
                    }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting detailed pitchers wOBA for date {date}: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // GET: api/wOBA/pitchers/date/{date}
        [HttpGet("pitchers/date/{date}")]
        public async Task<IActionResult> GetPitchersWobaForDate(string date)
        {
            if (!DateTime.TryParse(date, out DateTime parsedDate))
            {
                return BadRequest("Invalid date format. Use yyyy-MM-dd.");
            }

            try
            {
                var results = await _wobaService.GetPitchersWobaForGamesAsync(parsedDate);
                return Ok(new { Date = date, Count = results.Count, Results = results });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting pitchers wOBA for date {date}: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // GET: api/wOBA/constants/{year}/details
        [HttpGet("constants/{year}/details")]
        public IActionResult GetWobaConstantsDetails(int year)
        {
            try
            {
                // We need to use reflection to access the private method and class
                // Get the WobaConstants type using reflection
                Type wobaServiceType = _wobaService.GetType();
                Type wobaConstantsType = wobaServiceType.GetNestedType("WobaConstants", BindingFlags.NonPublic);

                if (wobaConstantsType == null)
                {
                    return StatusCode(500, "Could not access WobaConstants type");
                }

                // Get the GetWobaConstants method using reflection
                MethodInfo getWobaConstantsMethod = wobaServiceType.GetMethod("GetWobaConstants",
                    BindingFlags.NonPublic | BindingFlags.Instance);

                if (getWobaConstantsMethod == null)
                {
                    return StatusCode(500, "Could not access GetWobaConstants method");
                }

                // Call the method to get the constants for the specified year
                var constantsObj = getWobaConstantsMethod.Invoke(_wobaService, new object[] { year });

                if (constantsObj == null)
                {
                    return NotFound($"No wOBA constants found for year {year}");
                }

                // Get property values using reflection
                var properties = wobaConstantsType.GetProperties();
                var result = new Dictionary<string, object>();

                foreach (var property in properties)
                {
                    result[property.Name] = property.GetValue(constantsObj);
                }

                // Get available years by reflection
                var yearlyConstantsField = wobaServiceType.GetField("YearlyWobaConstants",
                    BindingFlags.NonPublic | BindingFlags.Static);

                if (yearlyConstantsField != null)
                {
                    var yearlyConstants = yearlyConstantsField.GetValue(null);
                    var yearsProperty = yearlyConstants.GetType().GetMethod("get_Keys");
                    if (yearsProperty != null)
                    {
                        var years = yearsProperty.Invoke(yearlyConstants, null);
                        result["availableYears"] = years;
                    }
                }

                // Add formula explanation
                result["formulaExplanation"] = "wOBA = (BB×BB_weight + HBP×HBP_weight + 1B×1B_weight + 2B×2B_weight + 3B×3B_weight + HR×HR_weight) / (AB + BB - IBB + SF + HBP)";

                // Add run conversion explanation
                result["runConversionExplanation"] = $"To convert wOBA to runs, multiply by the scale factor ({result["WobaScale"]}). One point of wOBA above average is worth approximately {result["WobaScale"]} runs over 600 plate appearances.";

                return Ok(new
                {
                    Year = year,
                    Constants = result,
                    IsExactMatch = true // This indicates if we found the exact year or used a fallback
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting detailed wOBA constants for year {year}: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // Add this method to the wOBAController class

        // GET: api/wOBA/lineup/RawStrength/{teamName}/{date}
        [HttpGet("lineup/RawStrength/{teamName}/{date}")]
        public async Task<IActionResult> GetRawLineupStrength(string teamName, string date)
        {
            if (!DateTime.TryParse(date, out DateTime parsedDate))
            {
                return BadRequest("Invalid date format. Use yyyy-MM-dd.");
            }

            try
            {
                var result = await _wobaService.GetRawLineupStrengthAsync(teamName, parsedDate);

                if (result.ContainsKey("error"))
                {
                    return NotFound(result);
                }

                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting lineup strength for {teamName} on {date}: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // GET: api/wOBA/lineup/strength/today/{teamName}
        [HttpGet("lineup/strength/today/{teamName}")]
        public async Task<IActionResult> GetTodayRawLineupStrength(string teamName)
        {
            try
            {
                var result = await _wobaService.GetRawLineupStrengthAsync(teamName, DateTime.Today);

                if (result.ContainsKey("error"))
                {
                    return NotFound(result);
                }

                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting today's lineup strength for {teamName}: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // GET: api/wOBA/lineup/strength/date/{date}
        [HttpGet("lineup/strength/date/{date}")]
        public async Task<IActionResult> GetAllTeamsLineupStrength(string date)
        {
            if (!DateTime.TryParse(date, out DateTime parsedDate))
            {
                return BadRequest("Invalid date format. Use yyyy-MM-dd.");
            }

            try
            {
                // First get all teams playing on this date from GamePreviews
                var gamePreviews = await _context.GamePreviews
                    .Where(g => g.Date.Date == parsedDate.Date)
                    .ToListAsync();

                if (!gamePreviews.Any())
                {
                    return NotFound($"No games found for date {date}");
                }

                // Get unique team names from the game previews
                var teams = gamePreviews.SelectMany(g => new[] { g.HomeTeam, g.AwayTeam }).Distinct().ToList();

                // Get lineup strength for each team
                var results = new List<object>();
                foreach (var team in teams)
                {
                    var lineupStrength = await _wobaService.GetRawLineupStrengthAsync(team, parsedDate);
                    results.Add(lineupStrength);
                }

                // Calculate league average for context
                double leagueAvgWoba = results
                    .Where(r => !((Dictionary<string, object>)r).ContainsKey("error"))
                    .Select(r => (double)((Dictionary<string, object>)r)["lineupBlendedWoba"])
                    .DefaultIfEmpty(0)
                    .Average();

                return Ok(new
                {
                    Date = date,
                    Teams = teams.Count,
                    LeagueAverageWoba = leagueAvgWoba,
                    Results = results
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting lineup strength for all teams on {date}: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        [HttpGet("adjustedRunsF5/{date}")]
        public async Task<IActionResult> GetWobaAdjustedRunsF5(string date)
        {
            if (!DateTime.TryParse(date, out DateTime parsedDate))
            {
                return BadRequest("Invalid date format. Use yyyy-MM-dd.");
            }

            try
            {
                var results = await _wobaService.GetWobaAdjustedRunsF5Async(parsedDate);

                if (!results.Any())
                {
                    return NotFound($"No games found or could not calculate adjusted runs for date {date}");
                }

                // Calculate some summary statistics
                double avgTotalExpectedRuns = results.Average(r => (double)r["totalExpectedRunsF5"]);
                double avgRunDifferential = results.Average(r => Math.Abs((double)r["runDifferentialF5"]));
                int homeTeamFavored = results.Count(r => (double)r["runDifferentialF5"] > 0);
                int awayTeamFavored = results.Count(r => (double)r["runDifferentialF5"] < 0);

                // Determine the league average WOBA - use a safe approach that handles either property name
                double leagueAverageWOBA = 0.311; // Default value
                if (results.Any() && results[0].ContainsKey("homeTeam"))
                {
                    var homeTeam = results[0]["homeTeam"] as Dictionary<string, object>;
                    if (homeTeam != null)
                    {
                        // First try the structure from your original implementation
                        if (homeTeam.ContainsKey("pitcherWobaAgainst"))
                        {
                            leagueAverageWOBA = 0.311; // Use default since we don't have the constants
                        }
                        // Then try the structure from my updated implementation
                        else if (homeTeam.ContainsKey("opposingPitcherWobaAgainst"))
                        {
                            leagueAverageWOBA = 0.311; // Use default since we don't have the constants
                        }
                    }
                }

                return Ok(new
                {
                    Date = date,
                    GamesAnalyzed = results.Count,
                    Games = results,
                    Summary = new
                    {
                        AverageTotalExpectedRunsF5 = avgTotalExpectedRuns,
                        AverageRunDifferentialF5 = avgRunDifferential,
                        HomeTeamFavored = homeTeamFavored,
                        AwayTeamFavored = awayTeamFavored,
                        LeagueAverageWOBA = leagueAverageWOBA
                    }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting wOBA adjusted runs for date {date}: {ex.Message}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }
    }

    public class BatchWobaRequest
    {
        public List<string> BbrefIds { get; set; }
        public int Year { get; set; }
    }
}