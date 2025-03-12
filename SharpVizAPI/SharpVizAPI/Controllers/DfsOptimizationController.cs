using Microsoft.AspNetCore.Mvc;
using SharpVizApi.Models;
using SharpVizApi.Services.Optimization;
using SharpVizAPI.Services;

namespace SharpVizApi.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class DfsOptimizationController : ControllerBase
    {
        private readonly IDfsOptimizationService _optimizationService;
        private readonly ILogger<DfsOptimizationController> _logger;

        public DfsOptimizationController(
            IDfsOptimizationService optimizationService,
            ILogger<DfsOptimizationController> logger)
        {
            _optimizationService = optimizationService;
            _logger = logger;
        }

        // POST: api/DfsOptimization/optimize
        [HttpPost("optimize")]
        public async Task<ActionResult<DfsOptimizationResponse>> OptimizeLineup([FromBody] DfsOptimizationRequest request)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            try
            {
                var result = await _optimizationService.OptimizeLineup(request);

                if (!result.IsSuccessful)
                {
                    return BadRequest(result);
                }

                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing optimization request");
                return StatusCode(500, "An error occurred while processing the request");
            }
        }
    }
}