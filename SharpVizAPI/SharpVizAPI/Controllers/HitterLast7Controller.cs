using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using SharpVizAPI.Services;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class HitterLast7Controller : ControllerBase
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<HitterLast7Controller> _logger;
        private readonly BlendingService _blendingService;

        public HitterLast7Controller(NrfidbContext context, ILogger<HitterLast7Controller> logger, BlendingService blendingService)
        {
            _context = context;
            _logger = logger;
            _blendingService = blendingService;
        }

        // GET: api/HitterLast7/{bbrefId}
        [HttpGet("{bbrefId}")]
        public async Task<ActionResult<HitterLast7>> GetHitterLast7(string bbrefId)
        {
            _logger.LogInformation($"Received GET request for HitterLast7 with bbrefId: {bbrefId}");
            var hitterLast7 = await _context.HitterLast7.FirstOrDefaultAsync(h => h.BbrefId == bbrefId);

            if (hitterLast7 == null)
            {
                _logger.LogWarning($"HitterLast7 with bbrefId: {bbrefId} not found.");
                return NotFound();
            }

            return hitterLast7;
        }

        // GET: api/HitterLast7/outperformers/{date}
        [HttpGet("outperformers/{date}")]
        public async Task<ActionResult<List<object>>> GetOutperformingHitters(string date)
        {
            _logger.LogInformation($"Received GET request for top outperforming hitters for date: {date}");

            var outperformingHitters = await _blendingService.GetOutperformingHittersAsync(date);

            if (outperformingHitters == null || !outperformingHitters.Any())
            {
                _logger.LogWarning("No outperforming hitters found.");
                return NotFound("No outperforming hitters found.");
            }

            return Ok(outperformingHitters);
        }


        // POST: api/HitterLast7
        [HttpPost]
        public async Task<ActionResult<HitterLast7>> PostHitterLast7(HitterLast7 hitterLast7)
        {
            _logger.LogInformation($"Received POST request for HitterLast7 with data: {JsonConvert.SerializeObject(hitterLast7)}");

            if (!ModelState.IsValid)
            {
                _logger.LogError("Model state is invalid.");
                return BadRequest(ModelState);
            }

            _context.HitterLast7.Add(hitterLast7);
            try
            {
                await _context.SaveChangesAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving HitterLast7: {ex.Message}");
                return StatusCode(500, "Internal server error");
            }

            return CreatedAtAction(nameof(GetHitterLast7), new { bbrefId = hitterLast7.BbrefId }, hitterLast7);
        }

        // PUT: api/HitterLast7/{bbrefId}
        [HttpPut("{bbrefId}")]
        public async Task<IActionResult> PutHitterLast7(string bbrefId, HitterLast7 hitterLast7)
        {
            _logger.LogInformation($"Received PUT request for HitterLast7 with bbrefId: {bbrefId} and data: {JsonConvert.SerializeObject(hitterLast7)}");

            if (bbrefId != hitterLast7.BbrefId)
            {
                _logger.LogError("bbrefId does not match hitterLast7.BbrefId");
                return BadRequest("bbrefId does not match hitterLast7.BbrefId");
            }

            _context.Entry(hitterLast7).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException ex)
            {
                _logger.LogError($"Concurrency error: {ex.Message}");

                if (!HitterLast7Exists(bbrefId))
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
                _logger.LogError($"Error saving HitterLast7: {ex.Message}");
                return StatusCode(500, "Internal server error");
            }

            return NoContent();
        }

        // DELETE: api/HitterLast7/{bbrefId}
        [HttpDelete("{bbrefId}")]
        public async Task<IActionResult> DeleteHitterLast7(string bbrefId)
        {
            _logger.LogInformation($"Received DELETE request for HitterLast7 with bbrefId: {bbrefId}");

            var hitterLast7 = await _context.HitterLast7.FirstOrDefaultAsync(h => h.BbrefId == bbrefId);

            if (hitterLast7 == null)
            {
                _logger.LogWarning($"HitterLast7 with bbrefId: {bbrefId} not found.");
                return NotFound();
            }

            _context.HitterLast7.Remove(hitterLast7);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool HitterLast7Exists(string bbrefId)
        {
            return _context.HitterLast7.Any(e => e.BbrefId == bbrefId);
        }
    }
}
