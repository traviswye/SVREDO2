using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class TeamTotalBattingTrackingController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public TeamTotalBattingTrackingController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/TeamTotalBattingTracking
        [HttpGet]
        public async Task<IActionResult> GetAll()
        {
            var records = await _context.TeamTotalBattingTracking.ToListAsync();
            return Ok(records);
        }

        // GET: api/TeamTotalBattingTracking/{year}/{teamName}
        [HttpGet("{year}/{teamName}")]
        public async Task<IActionResult> GetByYearAndTeam(int year, string teamName)
        {
            var record = await _context.TeamTotalBattingTracking
                .Where(t => t.Year == year && t.TeamName == teamName)
                .ToListAsync();

            if (record == null || !record.Any())
            {
                return NotFound("No records found for the given year and team.");
            }

            return Ok(record);
        }

        // GET: api/TeamTotalBattingTracking/exists/{year}/{teamName}
        [HttpGet("exists/{year}/{teamName}")]
        public async Task<IActionResult> CheckExists(int year, string teamName)
        {
            var exists = await _context.TeamTotalBattingTracking
                .AnyAsync(t => t.Year == year && t.TeamName == teamName);

            return Ok(new { exists });
        }

        // POST: api/TeamTotalBattingTracking
        [HttpPost]
        public async Task<IActionResult> Add([FromBody] TeamTotalBattingTracking record)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            // Check if record already exists
            var existingRecord = await _context.TeamTotalBattingTracking
                .FirstOrDefaultAsync(t => t.Year == record.Year && t.TeamName == record.TeamName);

            if (existingRecord != null)
            {
                // If record exists, update it
                _context.Entry(existingRecord).CurrentValues.SetValues(record);
            }
            else
            {
                // If record doesn't exist, add it
                _context.TeamTotalBattingTracking.Add(record);
            }

            await _context.SaveChangesAsync();
            return CreatedAtAction(nameof(GetByYearAndTeam), new { year = record.Year, teamName = record.TeamName }, record);
        }

        // PUT: api/TeamTotalBattingTracking/{year}/{teamName}
        [HttpPut("{year}/{teamName}")]
        public async Task<IActionResult> Update(int year, string teamName, [FromBody] TeamTotalBattingTracking record)
        {
            if (year != record.Year || teamName != record.TeamName)
            {
                return BadRequest("Year and team name in URL must match the record data.");
            }

            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            var existingRecord = await _context.TeamTotalBattingTracking
                .FirstOrDefaultAsync(t => t.Year == year && t.TeamName == teamName);

            if (existingRecord == null)
            {
                return NotFound("Record not found.");
            }

            // Update record with new values
            _context.Entry(existingRecord).CurrentValues.SetValues(record);

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!RecordExists(year, teamName))
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

        // DELETE: api/TeamTotalBattingTracking/{year}/{teamName}/{dateAdded}
        [HttpDelete("{year}/{teamName}/{dateAdded}")]
        public async Task<IActionResult> Delete(int year, string teamName, DateTime dateAdded)
        {
            var record = await _context.TeamTotalBattingTracking
                .FirstOrDefaultAsync(t => t.Year == year && t.TeamName == teamName && t.DateAdded == dateAdded);

            if (record == null)
            {
                return NotFound("Record not found.");
            }

            _context.TeamTotalBattingTracking.Remove(record);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool RecordExists(int year, string teamName)
        {
            return _context.TeamTotalBattingTracking.Any(t => t.Year == year && t.TeamName == teamName);
        }
    }
}