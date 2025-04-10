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
    public class PitcherPlatoonAndTrackRecordController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public PitcherPlatoonAndTrackRecordController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/PitcherPlatoonAndTrackRecord
        [HttpGet]
        public async Task<ActionResult<IEnumerable<PitcherPlatoonAndTrackRecord>>> GetPitcherPlatoonAndTrackRecords()
        {
            return await _context.PitcherPlatoonAndTrackRecord.ToListAsync();
        }

        // GET: api/PitcherPlatoonAndTrackRecord/bbrefID/year/split
        [HttpGet("{bbrefID}/{year}/{split}")]
        public async Task<ActionResult<PitcherPlatoonAndTrackRecord>> GetPitcherPlatoonAndTrackRecord(string bbrefID, int year, string split)
        {
            var record = await _context.PitcherPlatoonAndTrackRecord.FindAsync(bbrefID, year, split);

            if (record == null)
            {
                return NotFound();
            }

            return record;
        }
        // GET: api/PitcherPlatoonAndTrackRecord/year/{year}/{split}
        [HttpGet("year/{year}/{split}")]
        public async Task<ActionResult<IEnumerable<PitcherPlatoonAndTrackRecord>>> GetPitcherPlatoonAndTrackRecordsByYearAndSplit(int year, string split)
        {
            var records = await _context.PitcherPlatoonAndTrackRecord
                .Where(r => r.Year == year && r.Split == split)
                .ToListAsync();

            if (!records.Any())
            {
                return NotFound($"No records found for year {year} and split '{split}'.");
            }

            return records;
        }

        // GET: api/PitcherPlatoonAndTrackRecord/bbrefID/year
        [HttpGet("{bbrefID}/{year}")]
        public async Task<ActionResult<IEnumerable<PitcherPlatoonAndTrackRecord>>> GetPitcherPlatoonAndTrackRecordsByBbrefIDAndYear(string bbrefID, int year)
        {
            var records = await _context.PitcherPlatoonAndTrackRecord
                .Where(r => r.BbrefID == bbrefID && r.Year == year)
                .ToListAsync();

            if (!records.Any())
            {
                return NotFound();
            }

            return records;
        }

        // PUT: api/PitcherPlatoonAndTrackRecord/bbrefID/year/split
        [HttpPut("{bbrefID}/{year}/{split}")]
        public async Task<IActionResult> PutPitcherPlatoonAndTrackRecord(string bbrefID, int year, string split, PitcherPlatoonAndTrackRecord record)
        {
            if (bbrefID != record.BbrefID || year != record.Year || split != record.Split)
            {
                return BadRequest();
            }

            _context.Entry(record).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!PitcherPlatoonAndTrackRecordExists(bbrefID, year, split))
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

        // POST: api/PitcherPlatoonAndTrackRecord
        [HttpPost]
        public async Task<ActionResult<PitcherPlatoonAndTrackRecord>> PostPitcherPlatoonAndTrackRecord(PitcherPlatoonAndTrackRecord record)
        {
            _context.PitcherPlatoonAndTrackRecord.Add(record);
            await _context.SaveChangesAsync();

            return CreatedAtAction("GetPitcherPlatoonAndTrackRecord", new { bbrefID = record.BbrefID, year = record.Year, split = record.Split }, record);
        }

        // DELETE: api/PitcherPlatoonAndTrackRecord/bbrefID/year/split
        [HttpDelete("{bbrefID}/{year}/{split}")]
        public async Task<IActionResult> DeletePitcherPlatoonAndTrackRecord(string bbrefID, int year, string split)
        {
            var record = await _context.PitcherPlatoonAndTrackRecord.FindAsync(bbrefID, year, split);
            if (record == null)
            {
                return NotFound();
            }

            _context.PitcherPlatoonAndTrackRecord.Remove(record);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool PitcherPlatoonAndTrackRecordExists(string bbrefID, int year, string split)
        {
            return _context.PitcherPlatoonAndTrackRecord.Any(e => e.BbrefID == bbrefID && e.Year == year && e.Split == split);
        }
    }
}
