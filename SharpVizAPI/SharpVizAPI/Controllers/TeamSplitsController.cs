using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Models; // Directly import the GamePreview class
using SharpVizAPI.Data; // Directly import the GamePreview class

[Route("api/[controller]")]
[ApiController]
public class TeamSplitsController : ControllerBase
{
    private readonly NrfidbContext _context;

    public TeamSplitsController(NrfidbContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<TeamSplits>>> GetTeamSplits()
    {
        return await _context.TeamSplits.ToListAsync();
    }

    [HttpGet("{team}")]
    public async Task<ActionResult<TeamSplits>> GetTeamSplit(string team)
    {
        var teamSplit = await _context.TeamSplits.FindAsync(team);

        if (teamSplit == null)
        {
            return NotFound();
        }

        return teamSplit;
    }

    [HttpPost]
    public async Task<ActionResult<TeamSplits>> CreateTeamSplit(TeamSplits teamSplits)
    {
        _context.TeamSplits.Add(teamSplits);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetTeamSplit), new { team = teamSplits.Team }, teamSplits);
    }

    [HttpPut("{team}")]
    public async Task<IActionResult> UpdateTeamSplit(string team, TeamSplits teamSplits)
    {
        if (team != teamSplits.Team)
        {
            return BadRequest();
        }

        _context.Entry(teamSplits).State = EntityState.Modified;

        try
        {
            await _context.SaveChangesAsync();
        }
        catch (DbUpdateConcurrencyException)
        {
            if (!_context.TeamSplits.Any(e => e.Team == team))
            {
                return NotFound();
            }
            else
            {
                throw;
            }
        }

        return NoContent();
    }

    [HttpDelete("{team}")]
    public async Task<IActionResult> DeleteTeamSplit(string team)
    {
        var teamSplit = await _context.TeamSplits.FindAsync(team);
        if (teamSplit == null)
        {
            return NotFound();
        }

        _context.TeamSplits.Remove(teamSplit);
        await _context.SaveChangesAsync();

        return NoContent();
    }
}
