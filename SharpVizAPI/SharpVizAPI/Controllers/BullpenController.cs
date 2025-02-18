using Microsoft.AspNetCore.Mvc;
using SharpVizAPI.Services;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class BullpenController : ControllerBase
    {
        private readonly BullpenAnalysisService _bullpenService;

        public BullpenController(BullpenAnalysisService bullpenService)
        {
            _bullpenService = bullpenService;
        }

        [HttpGet]
        public async Task<ActionResult<BullpenStats>> GetBullpenAnalysis(
            [FromQuery] int year,
            [FromQuery] string team,
            [FromQuery] string date)
        {
            DateTime parsedDate = DateTime.Parse(date);
            var result = await _bullpenService.GetBullpenAnalysis(year, team, parsedDate);
            return Ok(result);
        }
    }
}
