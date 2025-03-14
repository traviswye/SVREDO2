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
    public class TrailingGameLogSplitsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public TrailingGameLogSplitsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/TrailingGameLogSplits
        [HttpGet]
        public async Task<IActionResult> GetTrailingGameLogSplits([FromQuery] string bbrefid, [FromQuery] string split)
        {
            if (string.IsNullOrEmpty(bbrefid) || string.IsNullOrEmpty(split))
            {
                return BadRequest("bbrefid and split are required.");
            }

            var splits = await _context.TrailingGameLogSplits
                .Where(t => t.BbrefId == bbrefid && t.Split == split)
                .ToListAsync();

            if (splits == null || !splits.Any())
            {
                return NotFound("No trailing game log splits found for the given bbrefid and split.");
            }

            return Ok(splits);
        }

        // GET: api/TrailingGameLogSplits/mostRecent
        [HttpGet("mostRecent")]
        public async Task<IActionResult> GetMostRecentTrailingGameLogSplit([FromQuery] string bbrefid, [FromQuery] string split)
        {
            if (string.IsNullOrEmpty(bbrefid) || string.IsNullOrEmpty(split))
            {
                return BadRequest("bbrefid and split are required.");
            }

            var mostRecentSplit = await _context.TrailingGameLogSplits
                .Where(t => t.BbrefId == bbrefid && t.Split == split)
                .OrderByDescending(t => t.DateUpdated)
                .FirstOrDefaultAsync();

            if (mostRecentSplit == null)
            {
                return NotFound("No trailing game log split found for the given bbrefid and split.");
            }

            return Ok(mostRecentSplit);
        }

        // POST: api/TrailingGameLogSplits/batch
        [HttpPost("batch")]
        public async Task<IActionResult> GetBatchTrailingGameLogSplits([FromBody] BatchSplitRequest request)
        {
            if (request == null || request.BbrefIds == null || !request.BbrefIds.Any())
            {
                return BadRequest("BBRef IDs and split type are required.");
            }

            // Validate the split type
            if (string.IsNullOrEmpty(request.Split) ||
                (request.Split != "Last7G" && request.Split != "Season"))
            {
                return BadRequest("Split must be either 'Last7G' or 'Season'.");
            }

            try
            {
                var splits = await _context.TrailingGameLogSplits
                    .Where(t => request.BbrefIds.Contains(t.BbrefId) && t.Split == request.Split)
                    .ToListAsync();

                // Create a dictionary with BBRef ID as the key for easier lookup on the frontend
                var resultDict = splits.GroupBy(s => s.BbrefId)
                    .ToDictionary(
                        g => g.Key,
                        g => g.OrderByDescending(s => s.DateUpdated).FirstOrDefault()
                    );

                return Ok(resultDict);
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { message = "An error occurred while fetching batch records.", error = ex.Message });
            }
        }

        public class BatchSplitRequest
        {
            public List<string> BbrefIds { get; set; }
            public string Split { get; set; }
        }

        // POST: api/TrailingGameLogSplits
        [HttpPost]
        public async Task<IActionResult> AddTrailingGameLogSplit([FromBody] TrailingGameLogSplit split)
        {
            if (split == null)
            {
                return BadRequest("Invalid split data.");
            }

            // Check if a record with the same composite key already exists
            var existingSplit = await _context.TrailingGameLogSplits
                .FirstOrDefaultAsync(t => t.BbrefId == split.BbrefId && t.Split == split.Split && t.DateUpdated == split.DateUpdated);

            if (existingSplit != null)
            {
                return Conflict("A trailing game log split with the same bbrefid, split, and date already exists.");
            }

            await _context.TrailingGameLogSplits.AddAsync(split);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetTrailingGameLogSplits), new { bbrefid = split.BbrefId, split = split.Split }, split);
        }

        // PUT: api/TrailingGameLogSplits/{bbrefid}/{split}/{dateUpdated}
        [HttpPut("{bbrefid}/{split}/{dateUpdated}")]
        public async Task<IActionResult> UpdateTrailingGameLogSplit(string bbrefid, string split, string dateUpdated, [FromBody] TrailingGameLogSplit updatedSplit)
        {
            if (string.IsNullOrEmpty(bbrefid) || string.IsNullOrEmpty(split) || string.IsNullOrEmpty(dateUpdated))
            {
                return BadRequest("bbrefid, split, and dateUpdated are required.");
            }

            var existingSplit = await _context.TrailingGameLogSplits
                .FirstOrDefaultAsync(t => t.BbrefId == bbrefid && t.Split == split && t.DateUpdated.ToString("yyyy-MM-dd") == dateUpdated);

            if (existingSplit == null)
            {
                return NotFound("No trailing game log split found for the given bbrefid, split, and date.");
            }

            // Update the fields with the provided data
            existingSplit.Team = updatedSplit.Team;
            existingSplit.SplitParkFactor = updatedSplit.SplitParkFactor;
            existingSplit.G = updatedSplit.G;
            existingSplit.PA = updatedSplit.PA;
            existingSplit.AB = updatedSplit.AB;
            existingSplit.R = updatedSplit.R;
            existingSplit.H = updatedSplit.H;
            existingSplit.Doubles = updatedSplit.Doubles;
            existingSplit.Triples = updatedSplit.Triples;
            existingSplit.HR = updatedSplit.HR;
            existingSplit.RBI = updatedSplit.RBI;
            existingSplit.BB = updatedSplit.BB;
            existingSplit.IBB = updatedSplit.IBB;
            existingSplit.SO = updatedSplit.SO;
            existingSplit.HBP = updatedSplit.HBP;
            existingSplit.SH = updatedSplit.SH;
            existingSplit.SF = updatedSplit.SF;
            existingSplit.ROE = updatedSplit.ROE;
            existingSplit.GDP = updatedSplit.GDP;
            existingSplit.SB = updatedSplit.SB;
            existingSplit.CS = updatedSplit.CS;
            existingSplit.BA = updatedSplit.BA;
            existingSplit.OBP = updatedSplit.OBP;
            existingSplit.SLG = updatedSplit.SLG;
            existingSplit.OPS = updatedSplit.OPS;
            existingSplit.BOP = updatedSplit.BOP;
            existingSplit.ALI = updatedSplit.ALI;
            existingSplit.WPA = updatedSplit.WPA;
            existingSplit.AcLI = updatedSplit.AcLI;
            existingSplit.CWPA = updatedSplit.CWPA;
            existingSplit.RE24 = updatedSplit.RE24;
            existingSplit.DFSDk = updatedSplit.DFSDk;
            existingSplit.DFSFd = updatedSplit.DFSFd;

            await _context.SaveChangesAsync();

            return NoContent();
        }

        // DELETE: api/TrailingGameLogSplits/{bbrefid}/{split}/{dateUpdated}
        [HttpDelete("{bbrefid}/{split}/{dateUpdated}")]
        public async Task<IActionResult> DeleteTrailingGameLogSplit(string bbrefid, string split, string dateUpdated)
        {
            if (string.IsNullOrEmpty(bbrefid) || string.IsNullOrEmpty(split) || string.IsNullOrEmpty(dateUpdated))
            {
                return BadRequest("bbrefid, split, and dateUpdated are required.");
            }

            var existingSplit = await _context.TrailingGameLogSplits
                .FirstOrDefaultAsync(t => t.BbrefId == bbrefid && t.Split == split && t.DateUpdated.ToString("yyyy-MM-dd") == dateUpdated);

            if (existingSplit == null)
            {
                return NotFound("No trailing game log split found for the given bbrefid, split, and date.");
            }

            _context.TrailingGameLogSplits.Remove(existingSplit);
            await _context.SaveChangesAsync();

            return NoContent();
        }
        // GET: api/TrailingGameLogSplits/last7G
        [HttpGet("last7G")]
        public async Task<IActionResult> GetLast7GRecords()
        {
            try
            {
                var records = await _context.TrailingGameLogSplits
                    .Where(t => t.Split == "Last7G")
                    .ToListAsync();

                if (records == null || !records.Any())
                {
                    return NotFound("No records found with the Split column set to 'Last7G'.");
                }

                return Ok(records);
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { message = "An error occurred while fetching records.", error = ex.Message });
            }
        }


    }
}
