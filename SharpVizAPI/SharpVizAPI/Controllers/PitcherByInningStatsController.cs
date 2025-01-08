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
    public class PitcherByInningStatsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public PitcherByInningStatsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/PitcherByInningStats/{bbrefId}/{inning}/year
        [HttpGet("{bbrefId}/{inning}/{year}")]
        public async Task<ActionResult<PitcherByInningStats>> GetPitcherByInningStats(string bbrefId, int inning, int year)
        {
            var stats = await _context.PitcherByInningStats
                                      .Where(p => p.BbrefId == bbrefId && p.Inning == inning && p.Year == year)
                                      .FirstOrDefaultAsync();

            if (stats == null)
            {
                return NotFound();
            }

            return stats;
        }


        // GET: api/PitcherByInningStats/{bbrefId}
        [HttpGet("{bbrefId}")]
        public async Task<ActionResult<IEnumerable<PitcherByInningStats>>> GetPitcherStatsByBbrefId(string bbrefId)
        {
            var stats = await _context.PitcherByInningStats
                                      .Where(p => p.BbrefId == bbrefId)
                                      .ToListAsync();

            if (stats == null || stats.Count == 0)
            {
                return NotFound();
            }

            return stats;
        }

        // POST: api/PitcherByInningStats
        [HttpPost]
        public async Task<ActionResult<PitcherByInningStats>> PostPitcherByInningStats(PitcherByInningStats stats)
        {
            _context.PitcherByInningStats.Add(stats);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetPitcherByInningStats), new { bbrefId = stats.BbrefId, inning = stats.Inning }, stats);
        }

        // PUT: api/PitcherByInningStats/{bbrefId}/{inning}
        [HttpPut("{bbrefId}/{inning}/{year}")]
        public async Task<IActionResult> PutPitcherByInningStats(string bbrefId, int inning, int year, PitcherByInningStats stats)
        {
            if (bbrefId != stats.BbrefId || inning != stats.Inning || year != stats.Year)
            {
                return BadRequest();
            }

            _context.Entry(stats).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!PitcherByInningStatsExists(bbrefId, inning, year))
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


        private bool PitcherByInningStatsExists(string bbrefId, int inning, int year)
        {
            return _context.PitcherByInningStats.Any(e => e.BbrefId == bbrefId && e.Inning == inning && e.Year == year);
        }
    }
}
