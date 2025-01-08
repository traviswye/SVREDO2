using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class InjuryController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public InjuryController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/Injury/{bbrefId}
        [HttpGet("{bbrefId}")]
        public async Task<ActionResult<IEnumerable<Injury>>> GetInjuryByPlayer(string bbrefId)
        {
            var injuries = await _context.Injuries
                .Where(i => i.bbrefId == bbrefId)
                .OrderByDescending(i => i.Date)  // Changed to Date
                .ToListAsync();

            if (injuries == null || injuries.Count == 0)
            {
                return NotFound();
            }

            return injuries;
        }

        // GET: api/Injury/summary
        [HttpGet("summary")]
        public async Task<ActionResult<IEnumerable<object>>> GetInjurySummary([FromQuery] string date = null)
        {
            DateTime? filterDate = null;

            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out DateTime parsedDate))
            {
                filterDate = parsedDate.Date;
            }

            var injurySummary = await _context.Injuries
                .Where(i => !filterDate.HasValue || i.Date.Date == filterDate)
                .Select(i => new { i.bbrefId, i.CurrentTeam })
                .ToListAsync();

            return Ok(injurySummary);
        }

        // POST: api/Injury
        [HttpPost]
        public async Task<ActionResult<Injury>> PostInjury(Injury injury)
        {
            _context.Injuries.Add(injury);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetInjuryByPlayer), new { bbrefId = injury.bbrefId }, injury);
        }

        // PUT: api/Injury/{bbrefId}
        [HttpPut("{bbrefId}")]
        public async Task<IActionResult> PutInjury(string bbrefId, Injury injury)
        {
            if (bbrefId != injury.bbrefId)
            {
                return BadRequest();
            }

            _context.Entry(injury).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!InjuryExists(bbrefId))
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

        // DELETE: api/Injury/{bbrefId}
        [HttpDelete("{bbrefId}")]
        public async Task<IActionResult> DeleteInjury(string bbrefId)
        {
            var injury = await _context.Injuries.FirstOrDefaultAsync(i => i.bbrefId == bbrefId);
            if (injury == null)
            {
                return NotFound();
            }

            _context.Injuries.Remove(injury);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool InjuryExists(string bbrefId)
        {
            return _context.Injuries.Any(i => i.bbrefId == bbrefId);
        }


        // Add a new endpoint for querying injuries by date
        [HttpGet("date/{date}")]
        public async Task<ActionResult<IEnumerable<Injury>>> GetInjuriesByDate(string date)
        {
            // Try to parse the date
            if (!DateTime.TryParse(date, out DateTime parsedDate))
            {
                return BadRequest("Invalid date format. Please provide a valid date.");
            }

            // Query injuries for the given date
            var injuries = await _context.Injuries
                .Where(i => i.Date.Date == parsedDate.Date)
                .ToListAsync();

            if (injuries == null || injuries.Count == 0)
            {
                return NotFound();
            }

            return Ok(injuries);
        }

    }
}
