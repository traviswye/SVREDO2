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

        _context.Pitchers.Add(pitcher);
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

    // GET: api/Pitchers/{bbrefID}
    [HttpGet("{bbrefID}")]
    public async Task<IActionResult> GetPitcher(string bbrefID)
    {
        var pitcher = await _context.Pitchers.FirstOrDefaultAsync(p => p.BbrefId == bbrefID);

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
