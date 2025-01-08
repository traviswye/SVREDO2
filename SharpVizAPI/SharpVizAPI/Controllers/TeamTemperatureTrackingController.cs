using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class TeamTemperatureTrackingController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public TeamTemperatureTrackingController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/TeamTemperatureTracking
        [HttpGet]
        public async Task<ActionResult<IEnumerable<TeamTemperatureTracking>>> GetTeamTemperatureTrackings()
        {
            return await _context.TeamTemperatureTrackings.ToListAsync();
        }

        // GET: api/TeamTemperatureTracking/Team/Year/Date
        [HttpGet("{team}/{year}/{date}")]
        public async Task<ActionResult<TeamTemperatureTracking>> GetTeamTemperatureTracking(string team, int year, string date)
        {
            var trackingDate = DateTime.Parse(date);
            var teamTemperatureTracking = await _context.TeamTemperatureTrackings
                .FindAsync(team, year, trackingDate);

            if (teamTemperatureTracking == null)
            {
                return NotFound();
            }

            return teamTemperatureTracking;
        }

        // GET: api/TeamTemperatureTracking/latest/{team}/{year}
        [HttpGet("latest/{team}/{year}")]
        public async Task<ActionResult<TeamTemperatureTracking>> GetLatestTeamTemperatureTracking(string team, int year)
        {
            var latestRecord = await _context.TeamTemperatureTrackings
                .Where(t => t.Team == team && t.Year == year)
                .OrderByDescending(t => t.Date)
                .FirstOrDefaultAsync();

            if (latestRecord == null)
            {
                return NotFound();
            }

            return latestRecord;
        }


        // POST: api/TeamTemperatureTracking
        [HttpPost]
        public async Task<ActionResult<TeamTemperatureTracking>> PostTeamTemperatureTracking(TeamTemperatureTracking tracking)
        {
            _context.TeamTemperatureTrackings.Add(tracking);
            await _context.SaveChangesAsync();

            return CreatedAtAction("GetTeamTemperatureTracking", new { team = tracking.Team, year = tracking.Year, date = tracking.Date }, tracking);
        }

        // PUT: api/TeamTemperatureTracking/Team/Year/Date
        [HttpPut("{team}/{year}/{date}")]
        public async Task<IActionResult> PutTeamTemperatureTracking(string team, int year, string date, TeamTemperatureTracking tracking)
        {
            var trackingDate = DateTime.Parse(date);

            if (team != tracking.Team || year != tracking.Year || trackingDate != tracking.Date)
            {
                return BadRequest();
            }

            _context.Entry(tracking).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!TeamTemperatureTrackingExists(team, year, trackingDate))
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

        // DELETE: api/TeamTemperatureTracking/Team/Year/Date
        [HttpDelete("{team}/{year}/{date}")]
        public async Task<IActionResult> DeleteTeamTemperatureTracking(string team, int year, string date)
        {
            var trackingDate = DateTime.Parse(date);
            var teamTemperatureTracking = await _context.TeamTemperatureTrackings
                .FindAsync(team, year, trackingDate);

            if (teamTemperatureTracking == null)
            {
                return NotFound();
            }

            _context.TeamTemperatureTrackings.Remove(teamTemperatureTracking);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        // GET: api/TeamTemperatureTracking/latest-teams/{year}/{useGameNumber}
        [HttpGet("latest-teams/{year}/{useGameNumber}")]
        public async Task<ActionResult<IEnumerable<TeamTemperatureTracking>>> GetLatestEntriesForEachTeam(int year, bool useGameNumber)
        {
            var latestRecords = await _context.TeamTemperatureTrackings
                .Where(t => t.Year == year)
                .GroupBy(t => t.Team)
                .Select(g => useGameNumber
                    ? g.OrderByDescending(t => t.GameNumber).FirstOrDefault()
                    : g.OrderByDescending(t => t.Date).FirstOrDefault())
                .ToListAsync();

            if (!latestRecords.Any())
            {
                return NotFound();
            }

            return latestRecords;
        }

        // GET: api/TeamTemperatureTracking/{team}/{year}
        [HttpGet("{team}/{year}")]
        public async Task<ActionResult<IEnumerable<TeamTemperatureTracking>>> GetTeamTemperatureTrackingByTeamAndYear(string team, int year)
        {
            var records = await _context.TeamTemperatureTrackings
                .Where(t => t.Team == team && t.Year == year)
                .OrderBy(t => t.Date) // Order by date for proper time-series graphing
                .ToListAsync();

            if (!records.Any())
            {
                return NotFound(new { message = $"No data found for team: {team} in year: {year}" });
            }

            return records;
        }



        private bool TeamTemperatureTrackingExists(string team, int year, DateTime date)
        {
            return _context.TeamTemperatureTrackings.Any(e => e.Team == team && e.Year == year && e.Date == date);
        }
    }
}
