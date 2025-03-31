using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class HittersController : ControllerBase
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<HittersController> _logger;

        public HittersController(NrfidbContext context, ILogger<HittersController> logger)
        {
            _context = context;
            _logger = logger;
        }

        // Team name to abbreviation conversion dictionary
        private static readonly Dictionary<string, string> TeamNameToAbbreviation = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            { "Diamondbacks", "ARI" },
            { "Braves", "ATL" },
            { "Orioles", "BAL" },
            { "Red Sox", "BOS" },
            { "Cubs", "CHC" },
            { "White Sox", "CHW" },
            { "Reds", "CIN" },
            { "Guardians", "CLE" },
            { "Rockies", "COL" },
            { "Tigers", "DET" },
            { "Astros", "HOU" },
            { "Royals", "KCR" },
            { "Angels", "LAA" },
            { "Dodgers", "LAD" },
            { "Marlins", "MIA" },
            { "Brewers", "MIL" },
            { "Twins", "MIN" },
            { "Mets", "NYM" },
            { "Yankees", "NYY" },
            { "Athletics", "ATH" },
            { "Phillies", "PHI" },
            { "Pirates", "PIT" },
            { "Padres", "SDP" },
            { "Mariners", "SEA" },
            { "Giants", "SFG" },
            { "Cardinals", "STL" },
            { "Rays", "TBR" },
            { "Rangers", "TEX" },
            { "Blue Jays", "TOR" },
            { "Nationals", "WAS" }
        };

        // GET: api/Hitters/{bbrefId}/{year}/{team}
        [HttpGet("{bbrefId}/{year}/{team}")]
        public async Task<ActionResult<Hitter>> GetHitter(string bbrefId, int year, string team)
        {
            _logger.LogInformation($"Received GET request for bbrefId: {bbrefId}, year: {year}, team: {team}");
            var hitter = await _context.Hitters.FindAsync(bbrefId, year, team);

            if (hitter == null)
            {
                _logger.LogWarning($"Hitter with bbrefId: {bbrefId}, year: {year}, team: {team} not found.");
                return NotFound();
            }

            return hitter;
        }

        // GET: api/Hitters/{bbrefId} - Backward compatibility for HitterLast7 foreign key
        [HttpGet("{bbrefId}")]
        public async Task<ActionResult<Hitter>> GetHitterByBbrefId(string bbrefId)
        {
            _logger.LogInformation($"Received GET request for bbrefId: {bbrefId}");
            // Get the most recent hitter entry for this bbrefId
            var hitter = await _context.Hitters
                .Where(h => h.bbrefId == bbrefId)
                .OrderByDescending(h => h.Year)
                .FirstOrDefaultAsync();

            if (hitter == null)
            {
                _logger.LogWarning($"Hitter with bbrefId: {bbrefId} not found.");
                return NotFound();
            }

            return hitter;
        }

        // GET: api/Hitters/todaysHitters/{date}
        [HttpGet("todaysHitters/{date}")]
        public async Task<ActionResult<IEnumerable<string>>> GetTodaysHitters(string date)
        {
            _logger.LogInformation($"Received GET request for today's hitters with date: {date}");

            // Parse the date from the format yy-MM-dd
            if (!DateTime.TryParseExact(date, "yy-MM-dd", null, System.Globalization.DateTimeStyles.None, out var parsedDate))
            {
                _logger.LogError($"Invalid date format: {date}. Expected format: yy-MM-dd");
                return BadRequest("Invalid date format. Please use 'yy-MM-dd'.");
            }

            try
            {
                // Get the year from the parsed date
                int year = parsedDate.Year;

                // Get all HOME teams playing on the specified date from GamePreviews
                var homeTeams = await _context.GamePreviews
                    .Where(gp => gp.Date == parsedDate)
                    .Select(gp => gp.HomeTeam)
                    .ToListAsync();

                // Get all AWAY teams playing on the specified date from GamePreviews
                var awayTeams = await _context.GamePreviews
                    .Where(gp => gp.Date == parsedDate)
                    .Select(gp => gp.AwayTeam)
                    .ToListAsync();

                // Combine the lists and remove duplicates
                var teamsPlayingToday = homeTeams.Concat(awayTeams).Distinct().ToList();

                if (teamsPlayingToday == null || !teamsPlayingToday.Any())
                {
                    _logger.LogWarning($"No games found for date: {parsedDate}");
                    return NotFound($"No games found for date: {parsedDate:yyyy-MM-dd}");
                }

                _logger.LogInformation($"Found {teamsPlayingToday.Count} teams playing on {parsedDate:yyyy-MM-dd}: {string.Join(", ", teamsPlayingToday)}");

                // Convert full team names to abbreviations
                var teamAbbreviations = new List<string>();
                foreach (var team in teamsPlayingToday)
                {
                    if (TeamNameToAbbreviation.TryGetValue(team, out string abbreviation))
                    {
                        teamAbbreviations.Add(abbreviation);
                        _logger.LogInformation($"Converted team name '{team}' to abbreviation '{abbreviation}'");
                    }
                    else
                    {
                        _logger.LogWarning($"Could not find abbreviation for team name: {team}");
                        // Include the original name in case it's already an abbreviation
                        teamAbbreviations.Add(team);
                    }
                }

                // Log the team abbreviations we're searching for
                _logger.LogInformation($"Searching for hitters from teams: {string.Join(", ", teamAbbreviations)}");

                // Get all hitters from these teams for the current year
                var hittersList = await _context.Hitters
                    .Where(h => teamAbbreviations.Contains(h.Team) && h.Year == year)
                    .Select(h => h.bbrefId)
                    .Distinct()
                    .ToListAsync();

                if (hittersList == null || !hittersList.Any())
                {
                    _logger.LogWarning($"No hitters found for teams playing on {parsedDate:yyyy-MM-dd}");

                    // For debugging: check if there are any hitters in the database for the current year
                    var allHittersCount = await _context.Hitters.Where(h => h.Year == year).CountAsync();
                    _logger.LogInformation($"Total hitters in database for year {year}: {allHittersCount}");

                    // Also log the teams we're searching for and their actual values in the database
                    var teamsInDb = await _context.Hitters
                        .Where(h => h.Year == year)
                        .Select(h => h.Team)
                        .Distinct()
                        .ToListAsync();
                    _logger.LogInformation($"Teams in database for year {year}: {string.Join(", ", teamsInDb)}");

                    return NotFound($"No hitters found for teams playing on {parsedDate:yyyy-MM-dd}");
                }

                _logger.LogInformation($"Found {hittersList.Count} unique hitters playing on {parsedDate:yyyy-MM-dd}");
                return hittersList;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error retrieving hitters for date: {parsedDate:yyyy-MM-dd}");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // POST: api/Hitters
        [HttpPost]
        public async Task<ActionResult<Hitter>> PostHitter(Hitter hitter)
        {
            _logger.LogInformation($"Received POST request with data: {JsonConvert.SerializeObject(hitter)}");

            if (!ModelState.IsValid)
            {
                _logger.LogError("Model state is invalid.");
                foreach (var error in ModelState)
                {
                    _logger.LogError($"Key: {error.Key}, Error: {string.Join(", ", error.Value.Errors.Select(e => e.ErrorMessage))}");
                }
                return BadRequest(ModelState);
            }

            // Check if the hitter already exists
            var existingHitter = await _context.Hitters.FindAsync(hitter.bbrefId, hitter.Year, hitter.Team);
            if (existingHitter != null)
            {
                _logger.LogInformation($"Hitter already exists. Updating instead: {hitter.bbrefId}, {hitter.Year}, {hitter.Team}");
                // Update the existing hitter
                _context.Entry(existingHitter).CurrentValues.SetValues(hitter);
            }
            else
            {
                // Add the new hitter
                _context.Hitters.Add(hitter);
            }

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving Hitter: {ex.Message}");
                return StatusCode(500, "Internal server error");
            }

            return CreatedAtAction(nameof(GetHitter), new { bbrefId = hitter.bbrefId, year = hitter.Year, team = hitter.Team }, hitter);
        }

        // PUT: api/Hitters/{bbrefId}/{year}/{team}
        [HttpPut("{bbrefId}/{year}/{team}")]
        public async Task<IActionResult> PutHitter(string bbrefId, int year, string team, Hitter hitter)
        {
            _logger.LogInformation($"Received PUT request for bbrefId: {bbrefId}, year: {year}, team: {team}");

            if (bbrefId != hitter.bbrefId || year != hitter.Year || team != hitter.Team)
            {
                _logger.LogError("Path parameters do not match hitter entity values");
                return BadRequest("Path parameters do not match hitter entity values");
            }

            _context.Entry(hitter).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException ex)
            {
                _logger.LogError($"Concurrency error: {ex.Message}");

                if (!HitterExists(bbrefId, year, team))
                {
                    return NotFound();
                }
                else
                {
                    return StatusCode(500, "Internal server error");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving Hitter: {ex.Message}");
                return StatusCode(500, "Internal server error");
            }

            return NoContent();
        }

        private bool HitterExists(string bbrefId, int year, string team)
        {
            return _context.Hitters.Any(e => e.bbrefId == bbrefId && e.Year == year && e.Team == team);
        }
    }
}