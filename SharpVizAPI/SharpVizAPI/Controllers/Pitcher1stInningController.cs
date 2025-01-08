using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Threading.Tasks;
using SharpVizAPI.Models; // Directly import the GamePreview class
using SharpVizAPI.Data; // Directly import the GamePreview class

[Route("api/[controller]")]
[ApiController]
public class Pitcher1stInningController : ControllerBase
{
    private readonly NrfidbContext _context;

    public Pitcher1stInningController(NrfidbContext context)
    {
        _context = context;
    }

    // POST: api/Pitcher1stInning
    [HttpPost]
    public async Task<IActionResult> CreatePitcher1stInning([FromBody] Pitcher1stInning pitcher1stInning)
    {
        if (pitcher1stInning == null || pitcher1stInning.Year == 0)
        {
            return BadRequest("Invalid data or missing year.");
        }

        _context.Pitcher1stInnings.Add(pitcher1stInning);
        await _context.SaveChangesAsync();

        return Ok(pitcher1stInning);
    }


    // PUT: api/Pitcher1stInning/{bbrefID}
    [HttpPut("{bbrefID}/{year}")]
    public async Task<IActionResult> UpdatePitcher1stInning(string bbrefID, int year, [FromBody] Pitcher1stInning pitcher1stInning)
    {
        if (pitcher1stInning == null || bbrefID != pitcher1stInning.BbrefId || year != pitcher1stInning.Year)
        {
            return BadRequest("Invalid data.");
        }

        var existingPitcher1stInning = await _context.Pitcher1stInnings
            .FirstOrDefaultAsync(p => p.BbrefId == bbrefID && p.Year == year);

        if (existingPitcher1stInning == null)
        {
            return NotFound("Pitcher 1st Inning stats not found.");
        }

        _context.Entry(existingPitcher1stInning).CurrentValues.SetValues(pitcher1stInning);
        await _context.SaveChangesAsync();

        return Ok(existingPitcher1stInning);
    }


    // GET: api/Pitcher1stInning/{bbrefID}
    [HttpGet("{bbrefID}")]
    public async Task<IActionResult> GetPitcher1stInning(string bbrefID)
    {
        var pitcher1stInning = await _context.Pitcher1stInnings.FirstOrDefaultAsync(p => p.BbrefId == bbrefID);

        if (pitcher1stInning == null)
        {
            return NotFound("Pitcher 1st Inning stats not found.");
        }

        return Ok(pitcher1stInning);
    }

    // DELETE: api/Pitcher1stInning/{bbrefID}
    [HttpDelete("{bbrefID}/{year}")]
    public async Task<IActionResult> DeletePitcher1stInning(string bbrefID, int year)
    {
        var pitcher1stInning = await _context.Pitcher1stInnings
            .FirstOrDefaultAsync(p => p.BbrefId == bbrefID && p.Year == year);

        if (pitcher1stInning == null)
        {
            return NotFound("Pitcher 1st Inning stats not found.");
        }

        _context.Pitcher1stInnings.Remove(pitcher1stInning);
        await _context.SaveChangesAsync();

        return NoContent();
    }


    [HttpGet("{bbrefID}/{year}")]
    public async Task<IActionResult> GetPitcher1stInning(string bbrefID, int year)
    {
        var pitcher1stInning = await _context.Pitcher1stInnings
            .FirstOrDefaultAsync(p => p.BbrefId == bbrefID && p.Year == year);

        if (pitcher1stInning == null)
        {
            return NotFound("Pitcher 1st Inning stats not found.");
        }

        return Ok(pitcher1stInning);
    }

}
