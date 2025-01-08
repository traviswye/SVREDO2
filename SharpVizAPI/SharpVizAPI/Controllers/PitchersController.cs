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

    public class CreatePitcherDto
    {
        public string BbrefId { get; set; }
        public string Team { get; set; }
        public int Age { get; set; }
        public string Lg { get; set; }
    }
}
