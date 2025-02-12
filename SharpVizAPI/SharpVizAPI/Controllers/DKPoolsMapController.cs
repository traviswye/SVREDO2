using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizApi.Models;
using SharpVizAPI.Data;

namespace SharpVizApi.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class DKPoolsMapController : ControllerBase
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<DKPoolsMapController> _logger;

        public DKPoolsMapController(NrfidbContext context, ILogger<DKPoolsMapController> logger)
        {
            _context = context;
            _logger = logger;
        }

        // GET: api/DKPoolsMap/date/{date}
        [HttpGet("date/{date}")]
        public async Task<ActionResult<IEnumerable<DKPoolsMap>>> GetPoolsByDate(DateTime date)
        {
            var pools = await _context.DKPoolsMaps
                .Where(p => p.Date == date.Date)
                .ToListAsync();

            if (!pools.Any())
            {
                return NotFound($"No pools found for date {date:yyyy-MM-dd}");
            }

            return Ok(pools);
        }

        // GET: api/DKPoolsMap/sport/{sport}
        [HttpGet("sport/{sport}")]
        public async Task<ActionResult<IEnumerable<DKPoolsMap>>> GetPoolsBySport(string sport)
        {
            var pools = await _context.DKPoolsMaps
                .Where(p => p.Sport == sport)
                .OrderByDescending(p => p.Date)
                .ToListAsync();

            if (!pools.Any())
            {
                return NotFound($"No pools found for sport {sport}");
            }

            return Ok(pools);
        }
        // GET: api/DKPoolsMap/sport/{sport}/date/{date}
        [HttpGet("sport/{sport}/date/{date}")]
        public async Task<ActionResult<IEnumerable<DKPoolsMap>>> GetPoolsBySportAndDate(string sport, DateTime date)
        {
            var pools = await _context.DKPoolsMaps
                .Where(p => p.Sport == sport && p.Date == date.Date)
                .OrderBy(p => p.StartTime)
                .ToListAsync();

            if (!pools.Any())
            {
                return NotFound($"No pools found for sport {sport} on date {date:yyyy-MM-dd}");
            }

            return Ok(pools);
        }

        // POST: api/DKPoolsMap
        [HttpPost]
        public async Task<ActionResult<DKPoolsMap>> PostPool(DKPoolsMapInput input)
        {
            try
            {
                // Check if pool already exists
                var existingPool = await _context.DKPoolsMaps
                    .FirstOrDefaultAsync(p => p.DraftGroupId == input.DraftGroupId);

                if (existingPool != null)
                {
                    // Return success if pool already exists
                    return Ok(existingPool);
                }

                var pool = new DKPoolsMap
                {
                    Sport = input.Sport,
                    DraftGroupId = input.DraftGroupId,
                    Date = input.Date.Date,
                    StartTime = input.StartTime,
                    GameType = input.GameType,
                    DateAdded = DateTime.UtcNow
                };

                _context.DKPoolsMaps.Add(pool);
                await _context.SaveChangesAsync();

                _logger.LogInformation($"Added new pool map entry for draft group {input.DraftGroupId}");

                return CreatedAtAction(nameof(GetPoolsByDate), new { date = pool.Date }, pool);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error adding pool map entry for draft group {input.DraftGroupId}");
                return StatusCode(500, "An error occurred while processing the request");
            }
        }
        // POST: api/DKPoolsMap/batch
        [HttpPost("batch")]
        public async Task<ActionResult<IEnumerable<DKPoolsMap>>> PostPoolBatch(List<DKPoolsMapInput> inputs)
        {
            try
            {
                var addedPools = new List<DKPoolsMap>();

                foreach (var input in inputs)
                {
                    // Check if pool already exists
                    var existingPool = await _context.DKPoolsMaps
                        .FirstOrDefaultAsync(p => p.DraftGroupId == input.DraftGroupId);

                    if (existingPool != null)
                    {
                        // Update existing pool with new values
                        existingPool.Sport = input.Sport;
                        existingPool.Date = input.Date.Date;
                        existingPool.StartTime = input.StartTime;
                        existingPool.GameType = input.GameType;
                        existingPool.TotalGames = input.TotalGames;  // Update TotalGames
                        continue;
                    }

                    var pool = new DKPoolsMap
                    {
                        Sport = input.Sport,
                        DraftGroupId = input.DraftGroupId,
                        Date = input.Date.Date,
                        StartTime = input.StartTime,
                        GameType = input.GameType,
                        TotalGames = input.TotalGames,  // Set TotalGames from input
                        DateAdded = DateTime.UtcNow
                    };

                    _context.DKPoolsMaps.Add(pool);
                    addedPools.Add(pool);
                }

                if (addedPools.Any())
                {
                    await _context.SaveChangesAsync();
                    _logger.LogInformation($"Added {addedPools.Count} new pool map entries");
                }

                return Ok(new
                {
                    message = $"Successfully processed {inputs.Count} pools, added {addedPools.Count} new entries",
                    addedPools = addedPools
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error adding pool map entries in batch");
                return StatusCode(500, "An error occurred while processing the request");
            }
        }
    }
}