using Microsoft.AspNetCore.Mvc;
using SharpVizAPI.Models;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore; // Assuming you are using Entity Framework
using SharpVizAPI.Models;
using SharpVizAPI.Data;
using Newtonsoft.Json;


namespace SharpVizAPI.Controllers
{


        [Route("api/[controller]")]
        [ApiController]
        public class HitterVsPitcherController : ControllerBase
        {
            private readonly NrfidbContext _context;

            public HitterVsPitcherController(NrfidbContext context)
            {
                _context = context;
            }

            // GET: api/HitterVsPitcher
            [HttpGet]
            public async Task<ActionResult<IEnumerable<HitterVsPitcher>>> GetAllHitterVsPitchers()
            {
                return await _context.HitterVsPitchers.ToListAsync();
            }

            // GET: api/HitterVsPitcher/5
            [HttpGet("{id}")]
            public async Task<ActionResult<HitterVsPitcher>> GetHitterVsPitcher(int id)
            {
                var hitterVsPitcher = await _context.HitterVsPitchers.FindAsync(id);

                if (hitterVsPitcher == null)
                {
                    return NotFound();
                }

                return hitterVsPitcher;
            }

            // GET: api/HitterVsPitcher/pitcher/{pitcher}
            [HttpGet("pitcher/{pitcher}")]
            public async Task<ActionResult<IEnumerable<HitterVsPitcher>>> GetHitterVsPitchersByPitcher(string pitcher)
            {
                var results = await _context.HitterVsPitchers
                    .Where(hvp => hvp.Pitcher.ToLower() == pitcher.ToLower())
                    .ToListAsync();

                if (results == null || !results.Any())
                {
                    return NotFound();
                }

                return results;
            }

            // GET: api/HitterVsPitcher/game/{gamePreviewId}
            [HttpGet("game/{gamePreviewId}")]
            public async Task<ActionResult<IEnumerable<HitterVsPitcher>>> GetHitterVsPitchersByGamePreviewID(int gamePreviewId)
            {
                var results = await _context.HitterVsPitchers
                    .Where(hvp => hvp.GamePreviewID == gamePreviewId)
                    .ToListAsync();

                if (results == null || !results.Any())
                {
                    return NotFound();
                }

                return results;
            }

            // PUT: api/HitterVsPitcher/5
            [HttpPut("{id}")]
            public async Task<IActionResult> UpdateHitterVsPitcher(int id, HitterVsPitcher hitterVsPitcher)
            {
                if (id != hitterVsPitcher.ID)
                {
                    return BadRequest();
                }

                _context.Entry(hitterVsPitcher).State = EntityState.Modified;

                try
                {
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!HitterVsPitcherExists(id))
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

            // POST: api/HitterVsPitcher
            [HttpPost]
            public async Task<ActionResult<HitterVsPitcher>> CreateHitterVsPitcher(HitterVsPitcher hitterVsPitcher)
            {
                _context.HitterVsPitchers.Add(hitterVsPitcher);
                await _context.SaveChangesAsync();

                return CreatedAtAction("GetHitterVsPitcher", new { id = hitterVsPitcher.ID }, hitterVsPitcher);
            }

            // DELETE: api/HitterVsPitcher/5
            [HttpDelete("{id}")]
            public async Task<IActionResult> DeleteHitterVsPitcher(int id)
            {
                var hitterVsPitcher = await _context.HitterVsPitchers.FindAsync(id);
                if (hitterVsPitcher == null)
                {
                    return NotFound();
                }

                _context.HitterVsPitchers.Remove(hitterVsPitcher);
                await _context.SaveChangesAsync();

                return NoContent();
            }

            private bool HitterVsPitcherExists(int id)
            {
                return _context.HitterVsPitchers.Any(e => e.ID == id);
            }


        [HttpGet("LineupView/{date}")]
        public async Task<ActionResult<IEnumerable<object>>> GetHitterVsPitchersByDate(string date)
        {
            // Step 1: Fetch game previews for the given date
            var gamePreviews = await GetGamePreviewsByDate(date);

            if (gamePreviews == null || !gamePreviews.Any())
            {
                return NotFound("No game previews found for the given date.");
            }

            // Step 2: For each gamePreviewID, pull rows from HitterVsPitcher
            var response = new List<object>();

            foreach (var game in gamePreviews)
            {
                var gameId = game.Id;
                var gamePitcher = game.HomePitcher ?? game.AwayPitcher;

                var hitterVsPitcherStats = await _context.HitterVsPitchers
                    .Where(hvp => hvp.GamePreviewID == gameId)
                    .ToListAsync();

                if (!hitterVsPitcherStats.Any())
                {
                    continue;  // Skip if no HitterVsPitcher records found for this game
                }

                // Structure the hitters and their stats
                var hitters = hitterVsPitcherStats.Select(hvp => new
                {
                    hitter = hvp.Hitter,
                    stats = new
                    {
                        PA = hvp.PA,
                        H = hvp.Hits,
                        HR = hvp.HR,
                        RBI = hvp.RBI,
                        BB = hvp.BB,
                        SO = hvp.SO,
                        BA = hvp.BA,
                        OBP = hvp.OBP,
                        SLG = hvp.SLG,
                        OPS = hvp.OPS,
                        SH = hvp.SH,
                        SF = hvp.SF,
                        IBB = hvp.IBB,
                        HBP = hvp.HBP
                    }
                });

                // Structure the response for this game
                response.Add(new
                {
                    game = new
                    {
                        id = gameId,
                        pitcher = gamePitcher,
                        hitters = hitters
                    }
                });
            }

            return Ok(response);
        }

        // Helper method to fetch game previews for a given date
        // Helper method to fetch game previews for a given date
        private async Task<IEnumerable<GamePreview>> GetGamePreviewsByDate(string date)
        {
            // Step 1: Parse the incoming date string to DateTime
            if (!DateTime.TryParseExact(date, "yy-MM-dd", null, System.Globalization.DateTimeStyles.None, out DateTime parsedDate))
            {
                return null;  // Return null if the date format is invalid
            }

            // Step 2: Query the database with the parsed DateTime
            var localGamePreviews = await _context.GamePreviews
                .Where(gp => gp.Date.Date == parsedDate.Date)  // Ensure the Date component matches
                .ToListAsync();

            if (localGamePreviews.Any())
            {
                return localGamePreviews;
            }

            //// Step 3: If not found locally, fetch from external GamePreview API
            //var apiUrl = $"https://localhost:44346/api/GamePreviews/{date}";
            //var client = _clientFactory.CreateClient();
            //var response = await client.GetAsync(apiUrl);

            //if (!response.IsSuccessStatusCode)
            //{
            //    return null;
            //}

            //var content = await response.Content.ReadAsStringAsync();
            //var gamePreviews = JsonConvert.DeserializeObject<IEnumerable<GamePreview>>(content);

            //return gamePreviews;
            return null;
        }


        // New GET: api/HitterVsPitcher/allRecordsByDate/{date}
        [HttpGet("allRecordsByDate/{date}")]
        public async Task<ActionResult<IEnumerable<HitterVsPitcher>>> GetAllRecordsByDate(string date)
        {
            // Step 1: Fetch game previews for the given date
            var gamePreviews = await GetGamePreviewsByDate(date);

            if (gamePreviews == null || !gamePreviews.Any())
            {
                return NotFound("No game previews found for the given date.");
            }

            // Step 2: Extract all gamePreviewIDs for the given date
            var gamePreviewIds = gamePreviews.Select(gp => gp.Id).ToList();

            // Step 3: Fetch all HitterVsPitcher records where gamePreviewID matches one of the IDs
            var allRecords = await _context.HitterVsPitchers
                .Where(hvp => gamePreviewIds.Contains(hvp.GamePreviewID))
                .ToListAsync();

            if (!allRecords.Any())
            {
                return NotFound("No HitterVsPitcher records found for the given date.");
            }

            // Return the records as-is, with all fields from the HitterVsPitcher model
            return Ok(allRecords);
        }



    }
}

