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
    public class PitcherHomeAwaySplitsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public PitcherHomeAwaySplitsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/PitcherHomeAwaySplits
        [HttpGet]
        public async Task<ActionResult<IEnumerable<PitcherHomeAwaySplits>>> GetPitcherHomeAwaySplits()
        {
            return await _context.PitcherHomeAwaySplits.ToListAsync();
        }

        // GET: api/PitcherHomeAwaySplits/{bbrefID}/{year}/{split}
        [HttpGet("{bbrefID}/{year}/{split}")]
        public async Task<ActionResult<PitcherHomeAwaySplits>> GetPitcherHomeAwaySplit(string bbrefID, int year, string split)
        {
            var pitcherSplit = await _context.PitcherHomeAwaySplits.FindAsync(bbrefID, year, split);

            if (pitcherSplit == null)
            {
                return NotFound();
            }

            return pitcherSplit;
        }

        // PUT: api/PitcherHomeAwaySplits/{bbrefID}/{year}/{split}
        [HttpPut("{bbrefID}/{year}/{split}")]
        public async Task<IActionResult> PutPitcherHomeAwaySplit(string bbrefID, int year, string split, PitcherHomeAwaySplits pitcherSplit)
        {
            if (bbrefID != pitcherSplit.bbrefID || year != pitcherSplit.Year || split != pitcherSplit.Split)
            {
                return BadRequest();
            }

            _context.Entry(pitcherSplit).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!PitcherHomeAwaySplitExists(bbrefID, year, split))
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

        // POST: api/PitcherHomeAwaySplits
        [HttpPost]
        public async Task<ActionResult<PitcherHomeAwaySplits>> PostPitcherHomeAwaySplit(PitcherHomeAwaySplits pitcherSplit)
        {
            _context.PitcherHomeAwaySplits.Add(pitcherSplit);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetPitcherHomeAwaySplit), new { bbrefID = pitcherSplit.bbrefID, year = pitcherSplit.Year, split = pitcherSplit.Split }, pitcherSplit);
        }

        // DELETE: api/PitcherHomeAwaySplits/{bbrefID}/{year}/{split}
        [HttpDelete("{bbrefID}/{year}/{split}")]
        public async Task<IActionResult> DeletePitcherHomeAwaySplit(string bbrefID, int year, string split)
        {
            var pitcherSplit = await _context.PitcherHomeAwaySplits.FindAsync(bbrefID, year, split);
            if (pitcherSplit == null)
            {
                return NotFound();
            }

            _context.PitcherHomeAwaySplits.Remove(pitcherSplit);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool PitcherHomeAwaySplitExists(string bbrefID, int year, string split)
        {
            return _context.PitcherHomeAwaySplits.Any(e => e.bbrefID == bbrefID && e.Year == year && e.Split == split);
        }
    }
}
