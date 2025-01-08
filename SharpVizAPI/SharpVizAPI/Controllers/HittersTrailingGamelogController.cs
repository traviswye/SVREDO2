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
    public class HittersTrailingGamelogController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public HittersTrailingGamelogController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/HittersTrailingGamelog
        [HttpGet]
        public async Task<IActionResult> GetTrailingGamelogs([FromQuery] string bbrefid, [FromQuery] int year)
        {
            if (string.IsNullOrEmpty(bbrefid))
            {
                return BadRequest("bbrefid is required.");
            }

            var gamelogs = await _context.HittersTrailingGamelogs
                .Where(h => h.BbrefId == bbrefid && h.Year == year)
                .ToListAsync();

            if (gamelogs == null || !gamelogs.Any())
            {
                return NotFound("No trailing game logs found for the given bbrefid and year.");
            }

            return Ok(gamelogs);
        }

        // GET: api/HittersTrailingGamelog/mostRecent
        [HttpGet("mostRecent")]
        public async Task<IActionResult> GetMostRecentTrailingGamelog([FromQuery] string bbrefid, [FromQuery] int year)
        {
            if (string.IsNullOrEmpty(bbrefid))
            {
                return BadRequest("bbrefid is required.");
            }

            var mostRecentGamelog = await _context.HittersTrailingGamelogs
                .Where(h => h.BbrefId == bbrefid && h.Year == year)
                .OrderByDescending(h => h.Date)
                .FirstOrDefaultAsync();

            if (mostRecentGamelog == null)
            {
                return NotFound("No trailing game log found for the given bbrefid and year.");
            }

            return Ok(mostRecentGamelog);
        }

        // POST: api/HittersTrailingGamelog
        [HttpPost]
        public async Task<IActionResult> AddTrailingGamelog([FromBody] HittersTrailingGamelog gamelog)
        {
            if (gamelog == null)
            {
                return BadRequest("Invalid game log data.");
            }

            // Check if a record with the same bbrefid and date already exists to avoid duplicates
            var existingGamelog = await _context.HittersTrailingGamelogs
                .FirstOrDefaultAsync(h => h.BbrefId == gamelog.BbrefId && h.Date == gamelog.Date);

            if (existingGamelog != null)
            {
                return Conflict("A trailing game log with the same bbrefid and date already exists.");
            }

            await _context.HittersTrailingGamelogs.AddAsync(gamelog);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetTrailingGamelogs), new { bbrefid = gamelog.BbrefId, year = gamelog.Year }, gamelog);
        }

        // PUT: api/HittersTrailingGamelog/{bbrefid}/{date}
        [HttpPut("{bbrefid}/{date}")]
        public async Task<IActionResult> UpdateTrailingGamelog(string bbrefid, string date, [FromBody] HittersTrailingGamelog updatedGamelog)
        {
            if (string.IsNullOrEmpty(bbrefid) || string.IsNullOrEmpty(date))
            {
                return BadRequest("bbrefid and date are required.");
            }

            var existingGamelog = await _context.HittersTrailingGamelogs
                .FirstOrDefaultAsync(h => h.BbrefId == bbrefid && h.Date.ToString("yyyy-MM-dd") == date);

            if (existingGamelog == null)
            {
                return NotFound("No trailing game log found for the given bbrefid and date.");
            }

            // Update the fields with the provided data
            existingGamelog.PA = updatedGamelog.PA;
            existingGamelog.AB = updatedGamelog.AB;
            existingGamelog.R = updatedGamelog.R;
            existingGamelog.H = updatedGamelog.H;
            existingGamelog.Doubles = updatedGamelog.Doubles;
            existingGamelog.Triples = updatedGamelog.Triples;
            existingGamelog.HR = updatedGamelog.HR;
            existingGamelog.RBI = updatedGamelog.RBI;
            existingGamelog.BB = updatedGamelog.BB;
            existingGamelog.IBB = updatedGamelog.IBB;
            existingGamelog.SO = updatedGamelog.SO;
            existingGamelog.HBP = updatedGamelog.HBP;
            existingGamelog.SH = updatedGamelog.SH;
            existingGamelog.SF = updatedGamelog.SF;
            existingGamelog.ROE = updatedGamelog.ROE;
            existingGamelog.GDP = updatedGamelog.GDP;
            existingGamelog.SB = updatedGamelog.SB;
            existingGamelog.CS = updatedGamelog.CS;
            existingGamelog.BA = updatedGamelog.BA;
            existingGamelog.OBP = updatedGamelog.OBP;
            existingGamelog.SLG = updatedGamelog.SLG;
            existingGamelog.OPS = updatedGamelog.OPS;
            existingGamelog.BOP = updatedGamelog.BOP;
            existingGamelog.aLI = updatedGamelog.aLI;
            existingGamelog.WPA = updatedGamelog.WPA;
            existingGamelog.acLI = updatedGamelog.acLI;
            existingGamelog.cWPA = updatedGamelog.cWPA;
            existingGamelog.RE24 = updatedGamelog.RE24;
            existingGamelog.DFS_DK = updatedGamelog.DFS_DK;
            existingGamelog.DFS_FD = updatedGamelog.DFS_FD;
            existingGamelog.Pos = updatedGamelog.Pos;

            await _context.SaveChangesAsync();

            return NoContent();
        }

        // DELETE: api/HittersTrailingGamelog/{bbrefid}/{date}
        [HttpDelete("{bbrefid}/{date}")]
        public async Task<IActionResult> DeleteTrailingGamelog(string bbrefid, string date)
        {
            if (string.IsNullOrEmpty(bbrefid) || string.IsNullOrEmpty(date))
            {
                return BadRequest("bbrefid and date are required.");
            }

            var existingGamelog = await _context.HittersTrailingGamelogs
                .FirstOrDefaultAsync(h => h.BbrefId == bbrefid && h.Date.ToString("yyyy-MM-dd") == date);

            if (existingGamelog == null)
            {
                return NotFound("No trailing game log found for the given bbrefid and date.");
            }

            _context.HittersTrailingGamelogs.Remove(existingGamelog);
            await _context.SaveChangesAsync();

            return NoContent();
        }
    }
}
