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
    public class BullpenUsageController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public BullpenUsageController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/BullpenUsage
        [HttpGet]
        public async Task<ActionResult<IEnumerable<BullpenUsage>>> GetBullpenUsage()
        {
            return await _context.BullpenUsage.ToListAsync();
        }

        // GET: api/BullpenUsage/{bbrefid}/{teamGameNumber}
        [HttpGet("{bbrefid}/{teamGameNumber}")]
        public async Task<ActionResult<BullpenUsage>> GetBullpenUsage(string bbrefid, int teamGameNumber)
        {
            var bullpenUsage = await _context.BullpenUsage.FindAsync(bbrefid, teamGameNumber);

            if (bullpenUsage == null)
            {
                return NotFound();
            }

            return bullpenUsage;
        }

        // POST: api/BullpenUsage
        [HttpPost]
        public async Task<ActionResult<BullpenUsage>> PostBullpenUsage(BullpenUsage bullpenUsage)
        {
            _context.BullpenUsage.Add(bullpenUsage);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetBullpenUsage), new { bbrefid = bullpenUsage.Bbrefid, teamGameNumber = bullpenUsage.TeamGameNumber }, bullpenUsage);
        }

        // PUT: api/BullpenUsage/{bbrefid}/{teamGameNumber}
        [HttpPut("{bbrefid}/{teamGameNumber}")]
        public async Task<IActionResult> PutBullpenUsage(string bbrefid, int teamGameNumber, BullpenUsage bullpenUsage)
        {
            if (bbrefid != bullpenUsage.Bbrefid || teamGameNumber != bullpenUsage.TeamGameNumber)
            {
                return BadRequest();
            }

            _context.Entry(bullpenUsage).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!BullpenUsageExists(bbrefid, teamGameNumber))
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

        // DELETE: api/BullpenUsage/{bbrefid}/{teamGameNumber}
        [HttpDelete("{bbrefid}/{teamGameNumber}")]
        public async Task<IActionResult> DeleteBullpenUsage(string bbrefid, int teamGameNumber)
        {
            var bullpenUsage = await _context.BullpenUsage.FindAsync(bbrefid, teamGameNumber);
            if (bullpenUsage == null)
            {
                return NotFound();
            }

            _context.BullpenUsage.Remove(bullpenUsage);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool BullpenUsageExists(string bbrefid, int teamGameNumber)
        {
            return _context.BullpenUsage.Any(e => e.Bbrefid == bbrefid && e.TeamGameNumber == teamGameNumber);
        }
    }
}