using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class TeamRecSplitsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public TeamRecSplitsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/TeamRecSplits
        [HttpGet]
        public async Task<IActionResult> GetTeamRecSplits()
        {
            var teamRecSplits = await _context.TeamRecSplits.ToListAsync();
            return Ok(teamRecSplits);
        }

        // GET: api/TeamRecSplits/{team}
        [HttpGet("{team}")]
        public async Task<IActionResult> GetTeamRecSplit(string team)
        {
            var teamRecSplit = await _context.TeamRecSplits.FindAsync(team);

            if (teamRecSplit == null)
            {
                return NotFound();
            }

            return Ok(teamRecSplit);
        }

        // POST: api/TeamRecSplits
        [HttpPost]
        public async Task<IActionResult> PostTeamRecSplit([FromBody] TeamRecSplits teamRecSplits)
        {
            if (teamRecSplits == null)
            {
                return BadRequest("TeamRecSplits data is null.");
            }

            // Ensure L20 and L30 can be null
            if (teamRecSplits.L20 == null)
            {
                teamRecSplits.L20 = null;
            }

            if (teamRecSplits.L30 == null)
            {
                teamRecSplits.L30 = null;
            }

            _context.TeamRecSplits.Add(teamRecSplits);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetTeamRecSplit), new { team = teamRecSplits.Team }, teamRecSplits);
        }

        // PUT: api/TeamRecSplits/{team}
        [HttpPut("{team}")]
        public async Task<IActionResult> PutTeamRecSplit(string team, [FromBody] TeamRecSplits teamRecSplits)
        {
            if (team != teamRecSplits.Team)
            {
                return BadRequest("Team name in the URL and body must match.");
            }

            // Ensure L20 and L30 can be null
            if (teamRecSplits.L20 == null)
            {
                teamRecSplits.L20 = null;
            }

            if (teamRecSplits.L30 == null)
            {
                teamRecSplits.L30 = null;
            }

            _context.Entry(teamRecSplits).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!TeamRecSplitsExists(team))
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

        // DELETE: api/TeamRecSplits/{team}
        [HttpDelete("{team}")]
        public async Task<IActionResult> DeleteTeamRecSplit(string team)
        {
            var teamRecSplits = await _context.TeamRecSplits.FindAsync(team);

            if (teamRecSplits == null)
            {
                return NotFound();
            }

            _context.TeamRecSplits.Remove(teamRecSplits);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool TeamRecSplitsExists(string team)
        {
            return _context.TeamRecSplits.Any(e => e.Team == team);
        }


    [HttpPut("updatePrimaryStats/{team}")]
    public async Task<IActionResult> UpdatePrimaryStats(string team, TeamRecSplits updatedData)
    {
        var teamRecSplit = await _context.TeamRecSplits.FirstOrDefaultAsync(t => t.Team == team);
        if (teamRecSplit == null)
        {
            return NotFound($"Team with name {team} not found.");
        }

        // Update the columns related to the first data source
        teamRecSplit.Wins = updatedData.Wins;
        teamRecSplit.Losses = updatedData.Losses;
        teamRecSplit.WinPercentage = updatedData.WinPercentage;
        teamRecSplit.GB = updatedData.GB;
        teamRecSplit.WCGB = updatedData.WCGB;
        teamRecSplit.L10 = updatedData.L10;
        teamRecSplit.Streak = updatedData.Streak;
        teamRecSplit.RunsScored = updatedData.RunsScored;
        teamRecSplit.RunsAgainst = updatedData.RunsAgainst;
        teamRecSplit.Diff = updatedData.Diff;
        teamRecSplit.ExpectedRecord = updatedData.ExpectedRecord;
        teamRecSplit.HomeRec = updatedData.HomeRec;
        teamRecSplit.AwayRec = updatedData.AwayRec;
        teamRecSplit.Vs500Plus  = updatedData.Vs500Plus;

        await _context.SaveChangesAsync();

        return Ok(teamRecSplit);
    }

    // PUT method to update columns from the second data source
    [HttpPut("updateSecondaryStats/{team}")]
    public async Task<IActionResult> UpdateSecondaryStats(string team, TeamRecSplits updatedData)
    {
        var teamRecSplit = await _context.TeamRecSplits.FirstOrDefaultAsync(t => t.Team == team);
        if (teamRecSplit == null)
        {
            return NotFound($"Team with name {team} not found.");
        }

        // Update the columns related to the second data source
        teamRecSplit.Xtra = updatedData.Xtra;
        teamRecSplit.OneRun = updatedData.OneRun;
        teamRecSplit.Day = updatedData.Day;
        teamRecSplit.Night = updatedData.Night;
        teamRecSplit.Grass = updatedData.Grass;
        teamRecSplit.Turf = updatedData.Turf;
        teamRecSplit.East = updatedData.East;
        teamRecSplit.Central = updatedData.Central;
        teamRecSplit.West = updatedData.West;
        teamRecSplit.Inter = updatedData.Inter;
        teamRecSplit.VsLHP = updatedData.VsLHP;
        teamRecSplit.VsRHP = updatedData.VsRHP;

        await _context.SaveChangesAsync();

        return Ok(teamRecSplit);
    }
}
}
