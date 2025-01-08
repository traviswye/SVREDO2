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

        // GET: api/Hitters/{bbrefId}
        [HttpGet("{bbrefId}")]
        public async Task<ActionResult<Hitter>> GetHitter(string bbrefId)
        {
            _logger.LogInformation($"Received GET request for bbrefId: {bbrefId}");
            var hitter = await _context.Hitters.FindAsync(bbrefId);

            if (hitter == null)
            {
                _logger.LogWarning($"Hitter with bbrefId: {bbrefId} not found.");
                return NotFound();
            }

            return hitter;
        }
// POST HITTER
        [HttpPost]
        public async Task<ActionResult<Hitter>> PostHitter(Hitter hitter)
        {
            _logger.LogInformation($"Received POST request with data: {JsonConvert.SerializeObject(hitter)}");
            Console.WriteLine($"Received POST request with data: {JsonConvert.SerializeObject(hitter)}");


            if (!ModelState.IsValid)
            {
                _logger.LogError("Model state is invalid.");

                // Log specific model validation errors
                foreach (var error in ModelState)
                {
                    _logger.LogError($"Key: {error.Key}, Error: {string.Join(", ", error.Value.Errors.Select(e => e.ErrorMessage))}");
                }

                return BadRequest(ModelState);
            }

            _context.Hitters.Add(hitter);
            try
            {
                await _context.SaveChangesAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving Hitter: {ex.Message}");
                return StatusCode(500, "Internal server error");
            }

            return CreatedAtAction(nameof(GetHitter), new { bbrefId = hitter.bbrefId }, hitter);
        }


        // PUT: api/Hitters/{bbrefId}
        [HttpPut("{bbrefId}")]
        public async Task<IActionResult> PutHitter(string bbrefId, Hitter hitter)
        {
            _logger.LogInformation($"Received PUT request for bbrefId: {bbrefId} with data: {JsonConvert.SerializeObject(hitter)}");

            if (bbrefId != hitter.bbrefId)
            {
                _logger.LogError("bbrefId does not match hitter.bbrefId");
                return BadRequest("bbrefId does not match hitter.bbrefId");
            }

            _context.Entry(hitter).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException ex)
            {
                _logger.LogError($"Concurrency error: {ex.Message}");

                if (!HitterExists(bbrefId))
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

        private bool HitterExists(string bbrefId)
        {
            return _context.Hitters.Any(e => e.bbrefId == bbrefId);
        }
    }
}
