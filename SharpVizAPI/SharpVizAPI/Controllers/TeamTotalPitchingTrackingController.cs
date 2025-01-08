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
    public class TeamTotalPitchingTrackingController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public TeamTotalPitchingTrackingController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/TeamTotalPitchingTracking
        [HttpGet]
        public async Task<IActionResult> GetAll()
        {
            var records = await _context.TeamTotalPitchingTracking.ToListAsync();
            return Ok(records);
        }

        // GET: api/TeamTotalPitchingTracking/{year}/{teamName}
        [HttpGet("{year}/{teamName}")]
        public async Task<IActionResult> GetByYearAndTeam(int year, string teamName)
        {
            var record = await _context.TeamTotalPitchingTracking
                .Where(t => t.Year == year && t.TeamName == teamName)
                .ToListAsync();

            if (record == null || !record.Any())
            {
                return NotFound("No records found for the given year and team.");
            }

            return Ok(record);
        }

        // POST: api/TeamTotalPitchingTracking
        [HttpPost]
        public async Task<IActionResult> Add([FromBody] TeamTotalPitchingTracking record)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            _context.TeamTotalPitchingTracking.Add(record);
            await _context.SaveChangesAsync();
            return CreatedAtAction(nameof(GetByYearAndTeam), new { year = record.Year, teamName = record.TeamName }, record);
        }

        // DELETE: api/TeamTotalPitchingTracking/{year}/{teamName}/{dateAdded}
        [HttpDelete("{year}/{teamName}/{dateAdded}")]
        public async Task<IActionResult> Delete(int year, string teamName, DateTime dateAdded)
        {
            var record = await _context.TeamTotalPitchingTracking
                .FirstOrDefaultAsync(t => t.Year == year && t.TeamName == teamName && t.DateAdded == dateAdded);

            if (record == null)
            {
                return NotFound("Record not found.");
            }

            _context.TeamTotalPitchingTracking.Remove(record);
            await _context.SaveChangesAsync();
            return NoContent();
        }
    }
}
