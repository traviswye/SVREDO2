using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using SharpVizAPI.Services;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class LineupsController : ControllerBase
    {
        private readonly NrfidbContext _context;
        private readonly HttpClient _httpClient;
        private readonly LineupService _lineupService;


        public LineupsController(NrfidbContext context, HttpClient httpClient, LineupService lineupService)
        {
            _context = context;
            _httpClient = httpClient;
            _lineupService = lineupService;  // Add this line
        }

        // GET: api/Lineups
        [HttpGet]
        public async Task<IActionResult> GetLineups()
        {
            var lineups = await _context.Lineups.ToListAsync();
            return Ok(lineups);
        }

        // GET: api/Lineups/{id}
        [HttpGet("{id}")]
        public async Task<IActionResult> GetLineup(int id)
        {
            var lineup = await _context.Lineups.FindAsync(id);

            if (lineup == null)
            {
                return NotFound();
            }

            return Ok(lineup);
        }

        // GET: api/Lineups/{team}
        [HttpGet("team/{team}")]
        public async Task<IActionResult> GetLineupsByTeam(string team)
        {
            var lineups = await _context.Lineups
                .Where(l => l.Team == team)
                .OrderBy(l => l.GameNumber)
                .ToListAsync();

            if (lineups == null || lineups.Count == 0)
            {
                return NotFound($"No lineups found for team: {team}");
            }

            return Ok(lineups);
        }

        // GET: api/Lineups/last10/{team}
        [HttpGet("last10/{team}")]
        public async Task<IActionResult> GetLast10LineupsByTeam(string team)
        {
            var lineups = await _context.Lineups
                .Where(l => l.Team == team)
                .OrderByDescending(l => l.GameNumber)
                .Take(10)
                .ToListAsync();

            if (lineups == null || lineups.Count == 0)
            {
                return NotFound($"No lineups found for team: {team}");
            }

            return Ok(lineups);
        }

        // GET: api/Lineups/predictLineup/{team}
        [HttpGet("predictLineup/{team}")]
        public async Task<IActionResult> PredictLineup(string team, int recentGames = 8, int weightRecent = 3, string throwHand = null, int? year = null)
        {
            // If year is not provided, use current year
            int targetYear = year ?? DateTime.Now.Year;

            // Fetch injury summary from the Injury API
            var injuryResponse = await _httpClient.GetAsync("https://localhost:44346/api/Injury/summary");
            var injuryData = new List<InjurySummary>();

            if (injuryResponse.IsSuccessStatusCode)
            {
                var jsonString = await injuryResponse.Content.ReadAsStringAsync();
                injuryData = JsonSerializer.Deserialize<List<InjurySummary>>(jsonString);
            }

            // Retrieve all lineups for the team, sorted by year (newest first) and game number (newest first)
            var allLineups = await _context.Lineups
                .Where(l => l.Team == team)
                .OrderByDescending(l => l.Year)
                .ThenByDescending(l => l.GameNumber)
                .ToListAsync();

            if (allLineups == null || allLineups.Count == 0)
            {
                return NotFound($"No lineups found for team: {team}");
            }

            // Get current year lineups
            var currentYearLineups = allLineups.Where(l => l.Year == targetYear).ToList();

            // If we don't have enough current year lineups, use previous year's data
            List<Lineup> lineupPool;
            int yearWeight = 2; // Weight multiplier for current year lineups

            // If there are fewer than 3 lineups from the current year, include previous year data
            if (currentYearLineups.Count < 3)
            {
                lineupPool = allLineups;
                // Use all available lineups but make sure to still give priority to current year lineups
            }
            else
            {
                // We have enough current year lineups, so use only those
                lineupPool = currentYearLineups;
            }

            // Extract the most recent lineups based on the 'recentGames' parameter
            // This now respects the year ordering from above
            var recentLineups = lineupPool.Take(recentGames).ToList();

            // Predict lineup for both LHP and RHP
            var predictedLineupLHP = PredictLineup(recentLineups, lineupPool, facingLHP: true, weightRecent, injuryData, targetYear, yearWeight);
            var predictedLineupRHP = PredictLineup(recentLineups, lineupPool, facingLHP: false, weightRecent, injuryData, targetYear, yearWeight);

            // Check for the 'throwHand' parameter and return the appropriate lineup
            if (!string.IsNullOrEmpty(throwHand))
            {
                if (throwHand.ToUpper() == "LHP")
                {
                    return Ok(new { vsLHP = predictedLineupLHP });
                }
                else if (throwHand.ToUpper() == "RHP")
                {
                    return Ok(new { vsRHP = predictedLineupRHP });
                }
                else
                {
                    return BadRequest("Invalid value for throw parameter. Must be either 'LHP' or 'RHP'.");
                }
            }

            // Return both lineups if 'throwHand' is not specified
            return Ok(new
            {
                vsLHP = predictedLineupLHP,
                vsRHP = predictedLineupRHP
            });
        }

        // POST: api/Lineups
        [HttpPost]
        public async Task<IActionResult> PostLineup([FromBody] Lineup lineup)
        {
            if (lineup == null)
            {
                return BadRequest("Lineup data is null.");
            }

            // Add the lineup to the context
            _context.Lineups.Add(lineup);

            // Save the changes to the database
            await _context.SaveChangesAsync();

            // Return the created lineup with a 201 status code
            return CreatedAtAction(nameof(GetLineup), new { id = lineup.Id }, lineup);
        }

        private Dictionary<string, string> PredictLineup(List<Lineup> recentLineups, List<Lineup> allLineups, bool facingLHP, int weightRecent, List<InjurySummary> injuryData, int targetYear, int yearWeight)
        {
            // Filter lineups by LHP/RHP
            var relevantLineups = allLineups.Where(l => l.LHP == facingLHP).ToList();
            var recentRelevantLineups = recentLineups.Where(l => l.LHP == facingLHP).ToList();

            // Gather players who appeared in the recent games
            var recentPlayers = new HashSet<string>();
            for (int i = 1; i <= 9; i++)
            {
                foreach (var lineup in recentRelevantLineups)
                {
                    var battingPosition = GetBattingPosition(lineup, i);
                    if (!string.IsNullOrEmpty(battingPosition))
                    {
                        recentPlayers.Add(battingPosition);
                    }
                }
            }

            // Aggregate batting positions for all relevant lineups, giving extra weight to recent lineups
            var battingPositions = new Dictionary<string, List<string>>();
            for (int i = 1; i <= 9; i++)
            {
                battingPositions[$"batting{i}"] = new List<string>();
            }

            // Add recent lineups with weight
            foreach (var lineup in recentRelevantLineups)
            {
                // Calculate the weight - giving extra weight to current year lineups
                int weight = weightRecent;
                if (lineup.Year == targetYear)
                {
                    weight *= yearWeight; // Apply additional weight to current year lineups
                }

                for (int i = 1; i <= 9; i++)
                {
                    var battingPosition = GetBattingPosition(lineup, i);
                    if (!string.IsNullOrEmpty(battingPosition))
                    {
                        battingPositions[$"batting{i}"].AddRange(Enumerable.Repeat(battingPosition, weight));
                    }
                }
            }

            // Add older lineups
            foreach (var lineup in relevantLineups)
            {
                // Skip if already included in recent lineups
                if (recentRelevantLineups.Contains(lineup))
                    continue;

                // Apply year weighting to older lineups too
                int weight = 1; // Base weight for older lineups
                if (lineup.Year == targetYear)
                {
                    weight = yearWeight; // Give current year lineups more weight
                }

                for (int i = 1; i <= 9; i++)
                {
                    var battingPosition = GetBattingPosition(lineup, i);
                    if (!string.IsNullOrEmpty(battingPosition))
                    {
                        battingPositions[$"batting{i}"].AddRange(Enumerable.Repeat(battingPosition, weight));
                    }
                }
            }

            // Predict the lineup, ensuring no duplicates, excluding injured players, and restricting to recent players
            var predictedLineup = new Dictionary<string, string>();
            var selectedPlayers = new HashSet<string>();

            for (int i = 1; i <= 9; i++)
            {
                var candidates = battingPositions[$"batting{i}"]
                    .GroupBy(x => x)
                    .OrderByDescending(g => g.Count())
                    .Select(g => g.Key)
                    .Where(player => recentPlayers.Contains(player) && !selectedPlayers.Contains(player))
                    .ToList();

                // Exclude injured players
                candidates = candidates.Where(player => !IsPlayerInjured(player, injuryData)).ToList();

                if (candidates.Any())
                {
                    var mostCommonPlayer = candidates.First();
                    predictedLineup[$"batting{i}"] = mostCommonPlayer;
                    selectedPlayers.Add(mostCommonPlayer);
                }
                else
                {
                    predictedLineup[$"batting{i}"] = null;  // No eligible player for this position
                }
            }

            return predictedLineup;
        }

        private string GetBattingPosition(Lineup lineup, int position)
        {
            return position switch
            {
                1 => lineup.Batting1st,
                2 => lineup.Batting2nd,
                3 => lineup.Batting3rd,
                4 => lineup.Batting4th,
                5 => lineup.Batting5th,
                6 => lineup.Batting6th,
                7 => lineup.Batting7th,
                8 => lineup.Batting8th,
                9 => lineup.Batting9th,
                _ => null,
            };
        }

        private bool IsPlayerInjured(string playerName, List<InjurySummary> injuryData)
        {
            return injuryData.Any(injury => injury.bbrefId == playerName);
        }

        // POST: api/Lineups/Predictions
        [HttpPost("Predictions")]
        public async Task<IActionResult> CreateLineupPrediction([FromBody] LineupPrediction lineupPrediction)
        {
            if (lineupPrediction == null)
            {
                return BadRequest("Lineup prediction data is null.");
            }

            _context.LineupPredictions.Add(lineupPrediction);
            await _context.SaveChangesAsync();

            return Ok(lineupPrediction);
        }

        // GET: api/Lineups/Predictions/{id}
        [HttpGet("Predictions/{id}")]
        public async Task<IActionResult> GetLineupPrediction(int id)
        {
            var lineupPrediction = await _context.LineupPredictions.FindAsync(id);

            if (lineupPrediction == null)
            {
                return NotFound();
            }

            return Ok(lineupPrediction);
        }

        // POST: api/Lineups/Actual
        [HttpPost("Actual")]
        public async Task<IActionResult> CreateActualLineup([FromBody] ActualLineup actualLineup)
        {
            if (actualLineup == null)
            {
                return BadRequest("Actual lineup data is null.");
            }

            _context.ActualLineups.Add(actualLineup);
            await _context.SaveChangesAsync();

            return Ok(actualLineup);
        }

        //// GET: api/Lineups/Actual/{id}
        //[HttpGet("Actual/{id}")]
        //public async Task<IActionResult> GetActualLineup(int id)
        //{
        //    var actualLineup = await _context.ActualLineups.FindAsync(id);

        //    if (actualLineup == null)
        //    {
        //        return NotFound();
        //    }

        //    return Ok(actualLineup);
        //}

        // GET: api/Lineups/Predictions/{date}
        [HttpGet("Predictions/date/{date}")]
        public async Task<IActionResult> GetLineupPredictionsByDate(DateTime date)
        {
            var lineupPredictions = await _context.LineupPredictions
                .Where(lp => lp.Date == date)
                .Select(lp => new
                {
                    lp.Id,
                    lp.Team,
                    lp.Date,
                    lp.Opponent,
                    lp.OpposingSP,
                    lp.LHP,
                    Batting1st = lp.Batting1st ?? "N/A",
                    Batting2nd = lp.Batting2nd ?? "N/A",
                    Batting3rd = lp.Batting3rd ?? "N/A",
                    Batting4th = lp.Batting4th ?? "N/A",
                    Batting5th = lp.Batting5th ?? "N/A",
                    Batting6th = lp.Batting6th ?? "N/A",
                    Batting7th = lp.Batting7th ?? "N/A",
                    Batting8th = lp.Batting8th ?? "N/A",
                    Batting9th = lp.Batting9th ?? "N/A",
                    // Handle other fields similarly
                })
                .ToListAsync();

            if (lineupPredictions == null || lineupPredictions.Count == 0)
            {
                return NotFound($"No lineup predictions found for date: {date.ToShortDateString()}");
            }

            return Ok(lineupPredictions);
        }


        // GET: api/Lineups/Actual/{date}
        [HttpGet("Actual/{date}")]
        public async Task<IActionResult> GetActualLineupsByDate(DateTime date)
        {
            var actualLineups = await _context.ActualLineups
                .Where(al => al.Date == date)
                .ToListAsync();

            if (actualLineups == null || actualLineups.Count == 0)
            {
                return NotFound($"No actual lineups found for date: {date.ToShortDateString()}");
            }

            return Ok(actualLineups);
        }


        [HttpPost("fetchActualLineups")]
        public async Task<IActionResult> FetchAndStoreActualLineups()
        {
            await _lineupService.FetchAndPostActualLineupsAsync();
            return Ok("Actual lineups fetched and stored successfully.");
        }

        // PUT: api/Lineups/Actual/{id}/FetchedLogs
        [HttpPut("Actual/{id}/FetchedLogs")]
        public async Task<IActionResult> UpdateFetchedLogs(int id)
        {
            var actualLineup = await _context.ActualLineups.FindAsync(id);

            if (actualLineup == null)
            {
                return NotFound("Actual lineup not found for the given ID.");
            }

            // Update FetchedLogs to true
            actualLineup.FetchedLogs = true;

            // Save changes to the database
            _context.Entry(actualLineup).State = EntityState.Modified;
            await _context.SaveChangesAsync();

            return NoContent(); // Return 204 No Content on successful update
        }




        // InjurySummary class to deserialize the injury data
        private class InjurySummary
        {
            public string bbrefId { get; set; }
            public string CurrentTeam { get; set; }
        }
    }
}
