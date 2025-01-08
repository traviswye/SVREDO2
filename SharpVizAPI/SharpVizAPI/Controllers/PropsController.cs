using Microsoft.AspNetCore.Mvc;
using SharpVizAPI.Services;
using System;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class PropsController : ControllerBase
    {
        private readonly PropsService _propsService;

        public PropsController(PropsService propsService)
        {
            _propsService = propsService;
        }

        // GET: api/Props/SBProps?date=2024-09-01
        [HttpGet("SBProps")]
        public async Task<IActionResult> GetSBProps([FromQuery] DateTime date)
        {
            try
            {
                var pitchersWithHitters = await _propsService.GetTopPitchersAndLineupStealers(date);

                // Return the nested response with pitchers and their associated hitters
                return Ok(new { Pitchers = pitchersWithHitters });
            }
            catch (Exception ex)
            {
                // Handle any exceptions that may occur
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }


        [HttpGet("StrikeoutProjections")]
        public async Task<IActionResult> GetStrikeoutProjections([FromQuery] DateTime date)
        {
            try
            {
                var projections = await _propsService.GetStrikeoutProjections(date);
                return Ok(projections);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }



    }
}
