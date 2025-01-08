using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using SharpVizAPI.Services;

[ApiController]
[Route("api/[controller]")]
public class HitterTempTrackingController : ControllerBase
{
    private readonly NrfidbContext _context;
    private readonly BJmodelingService _bjModelingService;

    public HitterTempTrackingController(NrfidbContext context, BJmodelingService bjmodel)
    {
        _context = context;
        _bjModelingService = bjmodel;
    }

    // GET: api/HitterTempTracking/updateTemps
    [HttpGet("updateTemps")]
    public async Task<IActionResult> UpdateTemps([FromQuery] DateTime? targetDate)
    {
        try
        {
            if (!targetDate.HasValue)
            {
                return BadRequest(new { message = "Please provide a valid target date." });
            }

            await _bjModelingService.UpdateHitterTemperatureAsync(targetDate.Value);
            return Ok(new { message = "Hitter temperatures updated successfully for the given date." });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { message = "An error occurred while updating hitter temperatures.", error = ex.Message });
        }
    }


    [HttpGet("{bbrefid}/{year}")]
    public async Task<ActionResult<HitterTempTracking>> GetHitterTemperature(string bbrefid, int year)
    {
        var hitterTemp = await _context.HitterTempTracking
            .Where(h => h.BbrefId == bbrefid && h.Year == year)
            .OrderByDescending(h => h.Date)
            .FirstOrDefaultAsync();

        if (hitterTemp == null)
        {
            return NotFound();
        }

        return Ok(hitterTemp);
    }

    [HttpPost]
    public async Task<IActionResult> PostHitterTemperature(HitterTempTracking hitterTempDto)
    {
        var hitterTemp = new HitterTempTracking
        {
            BbrefId = hitterTempDto.BbrefId,
            Year = hitterTempDto.Year,
            Date = hitterTempDto.Date,
            CurrentTemp = hitterTempDto.CurrentTemp,
            TrailingTemp1 = hitterTempDto.TrailingTemp1,
            TrailingTemp2 = hitterTempDto.TrailingTemp2,
            TrailingTemp3 = hitterTempDto.TrailingTemp3,
            TrailingTemp4 = hitterTempDto.TrailingTemp4,
            TrailingTemp5 = hitterTempDto.TrailingTemp5,
            TrailingTemp6 = hitterTempDto.TrailingTemp6
        };

        _context.HitterTempTracking.Add(hitterTemp);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetHitterTemperature), new { bbrefid = hitterTemp.BbrefId, year = hitterTemp.Year }, hitterTemp);
    }
}
