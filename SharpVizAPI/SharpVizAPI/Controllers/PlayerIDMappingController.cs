    using global::SharpVizAPI.Data;
    using global::SharpVizAPI.Models;
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
        public class PlayerIDMappingController : ControllerBase
        {
            private readonly NrfidbContext _context;

            public PlayerIDMappingController(NrfidbContext context)
            {
                _context = context;
            }

            // GET: api/PlayerIDMapping
            [HttpGet]
            public async Task<ActionResult<IEnumerable<PlayerIDMapping>>> GetPlayerIDMappings()
            {
                return await _context.PlayerIDMappings.ToListAsync();
            }

            // GET: api/PlayerIDMapping/5
            [HttpGet("{id}")]
            public async Task<ActionResult<PlayerIDMapping>> GetPlayerIDMapping(int id)
            {
                var playerIDMapping = await _context.PlayerIDMappings.FindAsync(id);

                if (playerIDMapping == null)
                {
                    return NotFound();
                }

                return playerIDMapping;
            }

            // GET: api/PlayerIDMapping/bbref/verlaju01
            [HttpGet("bbref/{bbrefId}")]
            public async Task<ActionResult<PlayerIDMapping>> GetByBbrefId(string bbrefId)
            {
                var mapping = await _context.PlayerIDMappings
                    .Where(m => m.BbrefId == bbrefId)
                    .OrderByDescending(m => m.LastUpdated) // Get the most recently updated one
                    .FirstOrDefaultAsync();

                if (mapping == null)
                {
                    return NotFound($"No mapping found for BBRef ID: {bbrefId}");
                }

                return mapping;
            }

            // POST: api/PlayerIDMapping/bbrefToDkIds
            [HttpPost("bbrefToDkIds")]
            public async Task<ActionResult<Dictionary<string, int>>> GetDkIdsByBbrefIds([FromBody] List<string> bbrefIds)
            {
                if (bbrefIds == null || !bbrefIds.Any())
                {
                    return BadRequest("No BBRef IDs provided");
                }

                var mappings = await _context.PlayerIDMappings
                    .Where(m => bbrefIds.Contains(m.BbrefId))
                    .OrderByDescending(m => m.LastUpdated)
                    .ToListAsync();

                // Create a dictionary with BBRef ID as key and DraftKings ID as value
                var result = new Dictionary<string, int>();

                // Group by BBRef ID and take the most recently updated for each
                var latestMappings = mappings
                    .GroupBy(m => m.BbrefId)
                    .Select(g => g.OrderByDescending(m => m.LastUpdated).First());

                foreach (var mapping in latestMappings)
                {
                    result[mapping.BbrefId] = mapping.PlayerDkId;
                }

                // Report any BBRef IDs that weren't found
                var missingBbrefIds = bbrefIds.Except(result.Keys).ToList();
                if (missingBbrefIds.Any())
                {
                    // Log this information but still return what we found
                    Console.WriteLine($"Missing mappings for BBRef IDs: {string.Join(", ", missingBbrefIds)}");
                }

                return Ok(result);
            }

            // PUT: api/PlayerIDMapping/5
            [HttpPut("{id}")]
            public async Task<IActionResult> PutPlayerIDMapping(int id, PlayerIDMapping playerIDMapping)
            {
                if (id != playerIDMapping.Id)
                {
                    return BadRequest();
                }

                _context.Entry(playerIDMapping).State = EntityState.Modified;
                playerIDMapping.LastUpdated = DateTime.Now;

                try
                {
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!PlayerIDMappingExists(id))
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

            // POST: api/PlayerIDMapping
            [HttpPost]
            public async Task<ActionResult<PlayerIDMapping>> PostPlayerIDMapping(PlayerIDMapping playerIDMapping)
            {
                playerIDMapping.DateAdded = DateTime.Now;
                playerIDMapping.LastUpdated = DateTime.Now;

                _context.PlayerIDMappings.Add(playerIDMapping);
                await _context.SaveChangesAsync();

                return CreatedAtAction("GetPlayerIDMapping", new { id = playerIDMapping.Id }, playerIDMapping);
            }

            // DELETE: api/PlayerIDMapping/5
            [HttpDelete("{id}")]
            public async Task<IActionResult> DeletePlayerIDMapping(int id)
            {
                var playerIDMapping = await _context.PlayerIDMappings.FindAsync(id);
                if (playerIDMapping == null)
                {
                    return NotFound();
                }

                _context.PlayerIDMappings.Remove(playerIDMapping);
                await _context.SaveChangesAsync();

                return NoContent();
            }

            private bool PlayerIDMappingExists(int id)
            {
                return _context.PlayerIDMappings.Any(e => e.Id == id);
            }
        }
    }
