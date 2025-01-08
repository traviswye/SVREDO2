using Microsoft.AspNetCore.Mvc;
using System;
using System.Threading.Tasks;
using SharpVizAPI.Services;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ClassificationController : ControllerBase
    {
        private readonly IClassificationService _classificationService;

        public ClassificationController(IClassificationService classificationService)
        {
            _classificationService = classificationService;
        }

        // Endpoint to classify by Pitching Advantage
        [HttpGet("classificationByPitchingAdv")]
        public async Task<IActionResult> ClassificationByPitchingAdv([FromQuery] string date)
        {
            try
            {
                var result = await _classificationService.ClassificationByPitchingAdvAsync(date);
                return Ok(result);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // Endpoint to classify by all factors
        [HttpGet("classificationByAllFactors")]
        public async Task<IActionResult> ClassificationByAllFactors([FromQuery] string date)
        {
            try
            {
                var result = await _classificationService.ClassificationByAllFactorsAsync(date);
                return Ok(result);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }
    }
}
