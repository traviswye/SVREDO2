using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Threading.Tasks;
using SharpVizAPI.Models; // Directly import the GamePreview class
using SharpVizAPI.Data; // Directly import the GamePreview class

[Route("api/[controller]")]
[ApiController]
public class PitchersController : ControllerBase
{
    private readonly NrfidbContext _context;

    public PitchersController(NrfidbContext context)
    {
        _context = context;
    }

    // POST: api/Pitchers
    [HttpPost]
    public async Task<IActionResult> CreatePitcher([FromBody] Pitcher pitcher)
    {
        if (pitcher == null)
        {
            return BadRequest("Invalid data.");
        }

        // Check if pitcher already exists
        var existingPitcher = await _context.Pitchers.FindAsync(pitcher.BbrefId, pitcher.Year, pitcher.Team);
        if (existingPitcher != null)
        {
            // Update existing pitcher
            _context.Entry(existingPitcher).CurrentValues.SetValues(pitcher);
        }
        else
        {
            // Add new pitcher
            _context.Pitchers.Add(pitcher);
        }

        await _context.SaveChangesAsync();
        return Ok(pitcher);
    }

    // POST: api/Pitchers/Basic
    [HttpPost("Basic")]
    public async Task<IActionResult> CreateBasicPitcher([FromBody] CreatePitcherDto pitcherDto)
    {
        if (pitcherDto == null)
        {
            return BadRequest("Invalid data.");
        }

        // Map the DTO to the Pitcher entity
        var pitcher = new Pitcher
        {
            BbrefId = pitcherDto.BbrefId,
            Team = pitcherDto.Team,
            Age = pitcherDto.Age,
            Lg = pitcherDto.Lg
        };

        _context.Pitchers.Add(pitcher);
        await _context.SaveChangesAsync();

        return Ok(pitcher);
    }

    // PUT: api/Pitchers/{bbrefID}
    [HttpPut("{bbrefID}")]
    public async Task<IActionResult> UpdatePitcher(string bbrefID, [FromBody] Pitcher pitcher)
    {
        if (pitcher == null || bbrefID != pitcher.BbrefId)
        {
            return BadRequest("Invalid data.");
        }

        var existingPitcher = await _context.Pitchers.FirstOrDefaultAsync(p => p.BbrefId == bbrefID);
        if (existingPitcher == null)
        {
            return NotFound("Pitcher not found.");
        }

        // If the Throws field is not set in the incoming request, keep the existing value
        if (string.IsNullOrEmpty(pitcher.Throws))
        {
            pitcher.Throws = existingPitcher.Throws;
        }

        // Update the existing pitcher's data with the new values
        _context.Entry(existingPitcher).CurrentValues.SetValues(pitcher);
        await _context.SaveChangesAsync();

        return Ok(existingPitcher);
    }

    // GET: api/Pitchers/bullpens
    [HttpGet("bullpens")]
    public async Task<IActionResult> GetBullpenPitchers([FromQuery] int year, [FromQuery] string team)
    {
        if (string.IsNullOrEmpty(team))
        {
            return BadRequest("Team is required.");
        }

        try
        {
            // Get all pitchers for the team and year where G > GS (indicating relief/bullpen appearances)
            var bullpenPitchers = await _context.Pitchers
                .Where(p => p.Team == team && p.Year == year && p.G > p.GS)
                .ToListAsync();

            if (bullpenPitchers == null || !bullpenPitchers.Any())
            {
                return NotFound($"No bullpen pitchers found for team {team} in year {year}.");
            }

            // Calculate aggregate bullpen stats
            double totalIP = bullpenPitchers.Sum(p => p.IP);
            int totalER = bullpenPitchers.Sum(p => p.ER);
            int totalH = bullpenPitchers.Sum(p => p.H);
            int totalBB = bullpenPitchers.Sum(p => p.BB);
            int totalSO = bullpenPitchers.Sum(p => p.SO);
            int totalHR = bullpenPitchers.Sum(p => p.HR);

            // Calculate derived statistics
            double era = totalIP > 0 ? (totalER / totalIP) * 9.0 : 0;
            double whip = totalIP > 0 ? (totalH + totalBB) / totalIP : 0;
            double k9 = totalIP > 0 ? (totalSO / totalIP) * 9.0 : 0;
            double bb9 = totalIP > 0 ? (totalBB / totalIP) * 9.0 : 0;
            double hr9 = totalIP > 0 ? (totalHR / totalIP) * 9.0 : 0;

            // FIP calculation: ((13*HR) + (3*BB) - (2*K)) / IP + constant
            // The constant is typically around 3.2
            double fip = totalIP > 0 ? ((13 * totalHR) + (3 * totalBB) - (2 * totalSO)) / totalIP + 3.2 : 0;

            var bullpenStats = new
            {
                Team = team,
                Year = year,
                PitcherCount = bullpenPitchers.Count,
                TotalIP = totalIP,
                TotalER = totalER,
                Era = era,
                Whip = whip,
                K9 = k9,
                BB9 = bb9,
                HR9 = hr9,
                Fip = fip,
                // No OPS in the model, so we'll leave it out
                // Get last 5 most recently used bullpen pitchers
                LastUsed = bullpenPitchers
                    .OrderByDescending(p => p.DateModified)
                    .Take(5)
                    .Select(p => new
                    {
                        Name = p.BbrefId,
                        IP = p.IP,
                        // Calculate days rest based on current date and DateModified
                        DaysRest = (DateTime.Now - p.DateModified).Days
                    })
                    .ToList()
            };

            return Ok(bullpenStats);
        }
        catch (Exception ex)
        {
            return StatusCode(500, $"Internal server error: {ex.Message}");
        }
    }
    // GET: api/Pitchers/{bbrefID}/{year}/{team}
    [HttpGet("{bbrefID}/{year}/{team}")]
    public async Task<IActionResult> GetPitcher(string bbrefID, int year, string team)
    {
        var pitcher = await _context.Pitchers.FindAsync(bbrefID, year, team);

        if (pitcher == null)
        {
            return NotFound("Pitcher not found.");
        }

        return Ok(pitcher);
    }

    [HttpGet("{bbrefID}")]
    public async Task<IActionResult> GetPitcherByBbrefId(string bbrefID)
    {
        var pitcher = await _context.Pitchers
            .Where(p => p.BbrefId == bbrefID)
            .OrderByDescending(p => p.Year)
            .FirstOrDefaultAsync();

        if (pitcher == null)
        {
            return NotFound("Pitcher not found.");
        }

        return Ok(pitcher);
    }

    // GET: api/Pitchers/exists/{bbrefID}
    [HttpGet("exists/{bbrefID}")]
    public async Task<IActionResult> GetPitcherExists(string bbrefID)
    {
        var pitcher = await _context.Pitchers
            .Where(p => p.BbrefId == bbrefID)
            .Select(p => new { p.BbrefId, p.Team })
            .FirstOrDefaultAsync();

        if (pitcher == null)
        {
            return NotFound("Pitcher not found.");
        }

        return Ok(pitcher);
    }

    // PUT: api/Pitchers/{bbrefID}/{year}/{team}
    [HttpPut("{bbrefID}/{year}/{team}")]
    public async Task<IActionResult> UpdatePitcher(string bbrefID, int year, string team, [FromBody] Pitcher pitcher)
    {
        if (pitcher == null || bbrefID != pitcher.BbrefId || year != pitcher.Year || team != pitcher.Team)
        {
            return BadRequest("Invalid data.");
        }

        var existingPitcher = await _context.Pitchers.FindAsync(bbrefID, year, team);
        if (existingPitcher == null)
        {
            return NotFound("Pitcher not found.");
        }

        // If the Throws field is not set in the incoming request, keep the existing value
        if (string.IsNullOrEmpty(pitcher.Throws))
        {
            pitcher.Throws = existingPitcher.Throws;
        }

        // Update the existing pitcher's data with the new values
        _context.Entry(existingPitcher).CurrentValues.SetValues(pitcher);
        await _context.SaveChangesAsync();

        return Ok(existingPitcher);
    }
    // GET: api/Pitchers/year/{year}
    [HttpGet("year/{year}")]
    public async Task<IActionResult> GetPitchersByYear(int year)
    {
        try
        {
            var pitchers = await _context.Pitchers
                .Where(p => p.Year == year)
                .ToListAsync();

            if (pitchers == null || !pitchers.Any())
            {
                return NotFound($"No pitchers found for year {year}.");
            }

            return Ok(pitchers);
        }
        catch (Exception ex)
        {
            return StatusCode(500, $"Internal server error: {ex.Message}");
        }
    }


    // DELETE: api/Pitchers/{bbrefID}
    [HttpDelete("{bbrefID}")]
    public async Task<IActionResult> DeletePitcher(string bbrefID)
    {
        var pitcher = await _context.Pitchers.FirstOrDefaultAsync(p => p.BbrefId == bbrefID);
        if (pitcher == null)
        {
            return NotFound("Pitcher not found.");
        }

        _context.Pitchers.Remove(pitcher);
        await _context.SaveChangesAsync();

        return NoContent();
    }

    [HttpGet("pitchersByDate/{date}")]
    public async Task<IActionResult> GetPitchersByDate(string date)
    {
        // Validate the date format
        if (!DateTime.TryParseExact(date, "yy-MM-dd", null, System.Globalization.DateTimeStyles.None, out var parsedDate))
        {
            return BadRequest("Invalid date format. Please use 'yy-MM-dd'.");
        }

        // Get all HomePitcher IDs for the given date
        var homePitchers = await _context.GamePreviews
                                         .Where(gp => gp.Date == parsedDate)
                                         .Select(gp => gp.HomePitcher)
                                         .ToListAsync();

        // Get all AwayPitcher IDs for the given date
        var awayPitchers = await _context.GamePreviews
                                         .Where(gp => gp.Date == parsedDate)
                                         .Select(gp => gp.AwayPitcher)
                                         .ToListAsync();

        // Combine and remove duplicates
        var pitcherIds = homePitchers.Concat(awayPitchers).Distinct().ToList();

        if (!pitcherIds.Any())
        {
            return NotFound("No pitchers found for the specified date.");
        }

        // Query the Pitchers table for all the retrieved pitcher IDs
        var pitchers = await _context.Pitchers
                                      .Where(p => pitcherIds.Contains(p.BbrefId))
                                      .ToListAsync();

        if (!pitchers.Any())
        {
            return NotFound("No pitcher data found for the specified IDs.");
        }

        return Ok(pitchers);
    }


    public class CreatePitcherDto
    {
        public string BbrefId { get; set; }
        public string Team { get; set; }
        public int Age { get; set; }
        public string Lg { get; set; }
    }
}
