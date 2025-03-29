using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class HittersController : ControllerBase
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<HittersController> _logger;

        public HittersController(NrfidbContext context, ILogger<HittersController> logger)
        {
            _context = context;
            _logger = logger;
        }

        // GET: api/Hitters/{bbrefId}/{year}/{team}
        [HttpGet("{bbrefId}/{year}/{team}")]
        public async Task<ActionResult<Hitter>> GetHitter(string bbrefId, int year, string team)
        {
            _logger.LogInformation($"Received GET request for bbrefId: {bbrefId}, year: {year}, team: {team}");
            var hitter = await _context.Hitters.FindAsync(bbrefId, year, team);

            if (hitter == null)
            {
                _logger.LogWarning($"Hitter with bbrefId: {bbrefId}, year: {year}, team: {team} not found.");
                return NotFound();
            }

            return hitter;
        }

        // GET: api/Hitters/{bbrefId} - Backward compatibility for HitterLast7 foreign key
        [HttpGet("{bbrefId}")]
        public async Task<ActionResult<Hitter>> GetHitterByBbrefId(string bbrefId)
        {
            _logger.LogInformation($"Received GET request for bbrefId: {bbrefId}");
            // Get the most recent hitter entry for this bbrefId
            var hitter = await _context.Hitters
                .Where(h => h.bbrefId == bbrefId)
                .OrderByDescending(h => h.Year)
                .FirstOrDefaultAsync();

            if (hitter == null)
            {
                _logger.LogWarning($"Hitter with bbrefId: {bbrefId} not found.");
                return NotFound();
            }

            return hitter;
        }

        // POST: api/Hitters
        [HttpPost]
        public async Task<ActionResult<Hitter>> PostHitter(Hitter hitter)
        {
            _logger.LogInformation($"Received POST request with data: {JsonConvert.SerializeObject(hitter)}");

            if (!ModelState.IsValid)
            {
                _logger.LogError("Model state is invalid.");
                foreach (var error in ModelState)
                {
                    _logger.LogError($"Key: {error.Key}, Error: {string.Join(", ", error.Value.Errors.Select(e => e.ErrorMessage))}");
                }
                return BadRequest(ModelState);
            }

            // Check if the hitter already exists
            var existingHitter = await _context.Hitters.FindAsync(hitter.bbrefId, hitter.Year, hitter.Team);
            if (existingHitter != null)
            {
                _logger.LogInformation($"Hitter already exists. Updating instead: {hitter.bbrefId}, {hitter.Year}, {hitter.Team}");
                // Update the existing hitter
                _context.Entry(existingHitter).CurrentValues.SetValues(hitter);
            }
            else
            {
                // Add the new hitter
                _context.Hitters.Add(hitter);
            }

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving Hitter: {ex.Message}");
                return StatusCode(500, "Internal server error");
            }

            return CreatedAtAction(nameof(GetHitter), new { bbrefId = hitter.bbrefId, year = hitter.Year, team = hitter.Team }, hitter);
        }

        // PUT: api/Hitters/{bbrefId}/{year}/{team}
        [HttpPut("{bbrefId}/{year}/{team}")]
        public async Task<IActionResult> PutHitter(string bbrefId, int year, string team, Hitter hitter)
        {
            _logger.LogInformation($"Received PUT request for bbrefId: {bbrefId}, year: {year}, team: {team}");

            if (bbrefId != hitter.bbrefId || year != hitter.Year || team != hitter.Team)
            {
                _logger.LogError("Path parameters do not match hitter entity values");
                return BadRequest("Path parameters do not match hitter entity values");
            }

            _context.Entry(hitter).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException ex)
            {
                _logger.LogError($"Concurrency error: {ex.Message}");

                if (!HitterExists(bbrefId, year, team))
                {
                    return NotFound();
                }
                else
                {
                    return StatusCode(500, "Internal server error");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving Hitter: {ex.Message}");
                return StatusCode(500, "Internal server error");
            }

            return NoContent();
        }

        private bool HitterExists(string bbrefId, int year, string team)
        {
            return _context.Hitters.Any(e => e.bbrefId == bbrefId && e.Year == year && e.Team == team);
        }
    }
}