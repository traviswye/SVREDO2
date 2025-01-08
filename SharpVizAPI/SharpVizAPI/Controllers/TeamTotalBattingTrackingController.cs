using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore; // <-- Added this
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

        // POST: api/TeamTotalBattingTracking
        [HttpPost]
        public async Task<IActionResult> Add([FromBody] TeamTotalBattingTracking record)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            _context.TeamTotalBattingTracking.Add(record);
            await _context.SaveChangesAsync();
            return CreatedAtAction(nameof(GetByYearAndTeam), new { year = record.Year, teamName = record.TeamName }, record);
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


    }
}
