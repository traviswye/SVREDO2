using Microsoft.AspNetCore.Mvc;
using SharpVizAPI.Models;
using SharpVizAPI.Data;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;


namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class TeamProjectionsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public TeamProjectionsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/TeamProjections/lineups
        [HttpGet("lineups")]
        public async Task<ActionResult<IEnumerable<OpeningDayProjectedLineupModel>>> GetLineups()
        {
            return await _context.OpeningDayProjectedLineup.ToListAsync();
        }

        // GET: api/TeamProjections/lineups/year/2025
        [HttpGet("lineups/year/{year}")]
        public async Task<ActionResult<IEnumerable<OpeningDayProjectedLineupModel>>> GetLineupsByYear(int year)
        {
            return await _context.OpeningDayProjectedLineup
                .Where(l => l.Year == year)
                .ToListAsync();
        }

        // GET: api/TeamProjections/lineups/team/NYY/year/2025
        [HttpGet("lineups/team/{team}/year/{year}")]
        public async Task<ActionResult<OpeningDayProjectedLineupModel>> GetLineupByTeamAndYear(string team, int year)
        {
            var lineup = await _context.OpeningDayProjectedLineup
                .Where(l => l.Team == team && l.Year == year)
                .FirstOrDefaultAsync();

            if (lineup == null)
            {
                return NotFound();
            }

            return lineup;
        }

        // POST: api/TeamProjections/lineups
        [HttpPost("lineups")]
        public async Task<ActionResult<OpeningDayProjectedLineupModel>> PostLineup(OpeningDayProjectedLineupModel lineup)
        {
            // Check if lineup already exists for this team and year
            var existingLineup = await _context.OpeningDayProjectedLineup
                .Where(l => l.Team == lineup.Team && l.Year == lineup.Year)
                .FirstOrDefaultAsync();

            if (existingLineup != null)
            {
                // Update existing
                _context.Entry(existingLineup).CurrentValues.SetValues(lineup);
            }
            else
            {
                // Add new
                _context.OpeningDayProjectedLineup.Add(lineup);
            }

            await _context.SaveChangesAsync();

            return CreatedAtAction("GetLineupByTeamAndYear",
                new { team = lineup.Team, year = lineup.Year }, lineup);
        }

        // GET: api/TeamProjections/rotations
        [HttpGet("rotations")]
        public async Task<ActionResult<IEnumerable<OpeningDayProjectedRotationModel>>> GetRotations()
        {
            return await _context.OpeningDayProjectedRotation.ToListAsync();
        }

        // GET: api/TeamProjections/rotations/year/2025
        [HttpGet("rotations/year/{year}")]
        public async Task<ActionResult<IEnumerable<OpeningDayProjectedRotationModel>>> GetRotationsByYear(int year)
        {
            return await _context.OpeningDayProjectedRotation
                .Where(r => r.Year == year)
                .ToListAsync();
        }

        // GET: api/TeamProjections/rotations/team/NYY/year/2025
        [HttpGet("rotations/team/{team}/year/{year}")]
        public async Task<ActionResult<OpeningDayProjectedRotationModel>> GetRotationByTeamAndYear(string team, int year)
        {
            var rotation = await _context.OpeningDayProjectedRotation
                .Where(r => r.Team == team && r.Year == year)
                .FirstOrDefaultAsync();

            if (rotation == null)
            {
                return NotFound();
            }

            return rotation;
        }

        // POST: api/TeamProjections/rotations
        [HttpPost("rotations")]
        public async Task<ActionResult<OpeningDayProjectedRotationModel>> PostRotation(OpeningDayProjectedRotationModel rotation)
        {
            // Check if rotation already exists for this team and year
            var existingRotation = await _context.OpeningDayProjectedRotation
                .Where(r => r.Team == rotation.Team && r.Year == rotation.Year)
                .FirstOrDefaultAsync();

            if (existingRotation != null)
            {
                // Update existing
                _context.Entry(existingRotation).CurrentValues.SetValues(rotation);
            }
            else
            {
                // Add new
                _context.OpeningDayProjectedRotation.Add(rotation);
            }

            await _context.SaveChangesAsync();

            return CreatedAtAction("GetRotationByTeamAndYear",
                new { team = rotation.Team, year = rotation.Year }, rotation);
        }

        // DELETE: api/TeamProjections/lineups/team/NYY/year/2025
        [HttpDelete("lineups/team/{team}/year/{year}")]
        public async Task<IActionResult> DeleteLineup(string team, int year)
        {
            var lineup = await _context.OpeningDayProjectedLineup
                .Where(l => l.Team == team && l.Year == year)
                .FirstOrDefaultAsync();

            if (lineup == null)
            {
                return NotFound();
            }

            _context.OpeningDayProjectedLineup.Remove(lineup);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        // DELETE: api/TeamProjections/rotations/team/NYY/year/2025
        [HttpDelete("rotations/team/{team}/year/{year}")]
        public async Task<IActionResult> DeleteRotation(string team, int year)
        {
            var rotation = await _context.OpeningDayProjectedRotation
                .Where(r => r.Team == team && r.Year == year)
                .FirstOrDefaultAsync();

            if (rotation == null)
            {
                return NotFound();
            }

            _context.OpeningDayProjectedRotation.Remove(rotation);
            await _context.SaveChangesAsync();

            return NoContent();
        }
    }
}
