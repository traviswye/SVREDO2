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
                .OrderByDescending(i => i.Date)
                .ToListAsync();

            if (injuries == null || !injuries.Any())
            {
                return NotFound();
            }

            return injuries;
        }

        // GET: api/Injury/{bbrefId}/{year}
        [HttpGet("{bbrefId}/{year}")]
        public async Task<ActionResult<IEnumerable<Injury>>> GetInjuryByPlayerAndYear(string bbrefId, int year)
        {
            var injuries = await _context.Injuries
                .Where(i => i.bbrefId == bbrefId && i.Year == year)
                .OrderByDescending(i => i.Date)
                .ToListAsync();

            if (injuries == null || !injuries.Any())
            {
                return NotFound();
            }

            return injuries;
        }

        // GET: api/Injury/summary
        [HttpGet("summary")]
        public async Task<ActionResult<IEnumerable<object>>> GetInjurySummary(
            [FromQuery] string date = null,
            [FromQuery] int? year = null)
        {
            DateTime? filterDate = null;

            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out DateTime parsedDate))
            {
                filterDate = parsedDate.Date;
            }

            // Start with base query
            var query = _context.Injuries.AsQueryable();

            // Apply date filter if provided
            if (filterDate.HasValue)
            {
                query = query.Where(i => i.Date.Date == filterDate);
            }

            // Apply year filter if provided (otherwise default to current year)
            if (year.HasValue)
            {
                query = query.Where(i => i.Year == year.Value);
            }
            else
            {
                // Default to current year if no year is specified
                int currentYear = DateTime.Now.Year;
                query = query.Where(i => i.Year == currentYear);
            }

            var injurySummary = await query
                .Select(i => new { i.bbrefId, i.CurrentTeam, i.Year })
                .ToListAsync();

            return Ok(injurySummary);
        }

        // POST: api/Injury
        [HttpPost]
        public async Task<ActionResult<Injury>> PostInjury(Injury injury)
        {
            // If year is not provided, use current year
            if (injury.Year == 0)
            {
                injury.Year = DateTime.Now.Year;
            }

            // Check if an injury record already exists for this player and year
            var existingInjury = await _context.Injuries
                .FirstOrDefaultAsync(i => i.bbrefId == injury.bbrefId && i.Year == injury.Year);

            if (existingInjury != null)
            {
                // Update the existing record
                existingInjury.InjuryDescription = injury.InjuryDescription;
                existingInjury.CurrentTeam = injury.CurrentTeam;
                existingInjury.Date = injury.Date;

                await _context.SaveChangesAsync();

                return CreatedAtAction(
                    nameof(GetInjuryByPlayerAndYear),
                    new { bbrefId = existingInjury.bbrefId, year = existingInjury.Year },
                    existingInjury);
            }

            // Create a new record
            _context.Injuries.Add(injury);
            await _context.SaveChangesAsync();

            return CreatedAtAction(
                nameof(GetInjuryByPlayerAndYear),
                new { bbrefId = injury.bbrefId, year = injury.Year },
                injury);
        }

        // PUT: api/Injury/{bbrefId}/{year}
        [HttpPut("{bbrefId}/{year}")]
        public async Task<IActionResult> PutInjury(string bbrefId, int year, Injury injury)
        {
            if (bbrefId != injury.bbrefId || year != injury.Year)
            {
                return BadRequest("bbrefId or year in URL does not match the injury data");
            }

            _context.Entry(injury).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!InjuryExists(bbrefId, year))
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

        // DELETE: api/Injury/{bbrefId}/{year}
        [HttpDelete("{bbrefId}/{year}")]
        public async Task<IActionResult> DeleteInjury(string bbrefId, int year)
        {
            var injury = await _context.Injuries
                .FirstOrDefaultAsync(i => i.bbrefId == bbrefId && i.Year == year);

            if (injury == null)
            {
                return NotFound();
            }

            _context.Injuries.Remove(injury);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool InjuryExists(string bbrefId, int year)
        {
            return _context.Injuries.Any(i => i.bbrefId == bbrefId && i.Year == year);
        }

        // GET: api/Injury/date/{date}
        [HttpGet("date/{date}")]
        public async Task<ActionResult<IEnumerable<Injury>>> GetInjuriesByDate(
            string date,
            [FromQuery] int? year = null)
        {
            // Try to parse the date
            if (!DateTime.TryParse(date, out DateTime parsedDate))
            {
                return BadRequest("Invalid date format. Please provide a valid date.");
            }

            // Start query
            var query = _context.Injuries.AsQueryable();

            // Filter by date
            query = query.Where(i => i.Date.Date == parsedDate.Date);

            // Filter by year if provided
            if (year.HasValue)
            {
                query = query.Where(i => i.Year == year.Value);
            }
            else
            {
                // Default to current year
                int currentYear = DateTime.Now.Year;
                query = query.Where(i => i.Year == currentYear);
            }

            var injuries = await query.ToListAsync();

            if (injuries == null || !injuries.Any())
            {
                return NotFound();
            }

            return Ok(injuries);
        }

        // GET: api/Injury/year/{year}
        [HttpGet("year/{year}")]
        public async Task<ActionResult<IEnumerable<Injury>>> GetInjuriesByYear(int year)
        {
            var injuries = await _context.Injuries
                .Where(i => i.Year == year)
                .OrderByDescending(i => i.Date)
                .ToListAsync();

            if (injuries == null || !injuries.Any())
            {
                return NotFound($"No injuries found for year {year}");
            }

            return Ok(injuries);
        }
    }
}