using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using SharpVizAPI.Models;
using SharpVizAPI.Data;
using SharpVizAPI.Services;
using System;

[ApiController]
[Route("api/[controller]")]
public class ParkFactorsController : ControllerBase
{
    private readonly NrfidbContext _context;

    public ParkFactorsController(NrfidbContext context)
    {
        _context = context;
    }

    private static readonly Dictionary<string, string> TeamAbbreviationMap = new Dictionary<string, string>
    {
        { "Brewers", "MIL" },
        { "Angels", "LAA" },
        { "Cardinals", "STL" },
        { "Diamondbacks", "ARI" },
        { "Mets", "NYM" },
        { "Phillies", "PHI" },
        { "Tigers", "DET" },
        { "Rockies", "COL" },
        { "Dodgers", "LAD" },
        { "Red Sox", "BOS" },
        { "Rangers", "TEX" },
        { "Reds", "CIN" },
        { "White Sox", "CWS" },
        { "Royals", "KC" },
        { "Marlins", "MIA" },
        { "Astros", "HOU" },
        { "Nationals", "WSH" },
        { "Athletics", "OAK" },
        { "Giants", "SF" },
        { "Orioles", "BAL" },
        { "Padres", "SD" },
        { "Pirates", "PIT" },
        { "Guardians", "CLE" },
        { "Blue Jays", "TOR" },
        { "Mariners", "SEA" },
        { "Twins", "MIN" },
        { "Rays", "TB" },
        { "Braves", "ATL" },
        { "Cubs", "CHC" },
        { "Yankees", "NYY" }
    };

    private string TeamMap(string abbreviation)
    {
        return TeamAbbreviationMap.FirstOrDefault(x => x.Value == abbreviation).Key;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<ParkFactor>>> GetAllParkFactors()
    {
        return await _context.ParkFactors.ToListAsync();
    }

    [HttpGet("{venue}")]
    public async Task<ActionResult<ParkFactor>> GetParkFactorByVenue(string venue)
    {
        var parkFactor = await _context.ParkFactors.FirstOrDefaultAsync(p => p.Venue == venue);

        if (parkFactor == null)
        {
            return NotFound("Park factor not found for the specified venue.");
        }

        return Ok(parkFactor);
    }

    [HttpPost]
    public async Task<IActionResult> CreateParkFactor([FromBody] ParkFactor parkFactor)
    {
        if (parkFactor == null)
        {
            return BadRequest("Invalid data.");
        }

        _context.ParkFactors.Add(parkFactor);
        await _context.SaveChangesAsync();

        return Ok(parkFactor);
    }

    [HttpPost("batch")]
    public async Task<IActionResult> CreateParkFactors([FromBody] List<ParkFactor> parkFactors)
    {
        if (parkFactors == null || !parkFactors.Any())
        {
            return BadRequest("Invalid data.");
        }

        _context.ParkFactors.AddRange(parkFactors);
        await _context.SaveChangesAsync();

        return Ok(parkFactors);
    }

    [HttpPut("{team}")]
    public async Task<IActionResult> UpdateParkFactor(string team, [FromBody] ParkFactor updatedParkFactor)
    {
        if (updatedParkFactor == null || team != updatedParkFactor.Team)
        {
            return BadRequest("Invalid data.");
        }

        var existingParkFactor = await _context.ParkFactors.FirstOrDefaultAsync(p => p.Team == team);

        if (existingParkFactor == null)
        {
            return NotFound("Park factor not found.");
        }

        // Update the existing park factor with new data
        existingParkFactor.Venue = updatedParkFactor.Venue;
        existingParkFactor.Year = updatedParkFactor.Year;
        existingParkFactor.ParkFactorRating = updatedParkFactor.ParkFactorRating;
        existingParkFactor.wOBACon = updatedParkFactor.wOBACon;
        existingParkFactor.BACON = updatedParkFactor.BACON;
        existingParkFactor.R = updatedParkFactor.R;
        existingParkFactor.OBP = updatedParkFactor.OBP;
        existingParkFactor.H = updatedParkFactor.H;
        existingParkFactor.OneB = updatedParkFactor.OneB;
        existingParkFactor.TwoB = updatedParkFactor.TwoB;
        existingParkFactor.ThreeB = updatedParkFactor.ThreeB;
        existingParkFactor.HR = updatedParkFactor.HR;
        existingParkFactor.BB = updatedParkFactor.BB;
        existingParkFactor.SO = updatedParkFactor.SO;
        existingParkFactor.zipcode = updatedParkFactor.zipcode;
        existingParkFactor.RoofType = updatedParkFactor.RoofType;
        existingParkFactor.Latitude = updatedParkFactor.Latitude;
        existingParkFactor.Longitude = updatedParkFactor.Longitude;
        existingParkFactor.Direction = updatedParkFactor.Direction; // Added direction update

        await _context.SaveChangesAsync();

        return Ok(existingParkFactor);
    }

    [HttpPost("normalize")]
    public async Task<IActionResult> NormalizeParkFactors(
        [FromBody] NormalizeRequest request,
        [FromServices] NormalizationService normalizationService)
    {
        if (request == null || string.IsNullOrWhiteSpace(request.BbrefId))
        {
            return BadRequest("Invalid input data.");
        }

        try
        {
            var result = await normalizationService.NormalizeParkFactors(
                request.BbrefId,
                request.OppIds ?? new List<string>(), // Ensure a non-null list
                request.HomeGames
            );
            return Ok(result);
        }
        catch (Exception ex)
        {
            return StatusCode(500, $"An error occurred: {ex.Message}");
        }
    }

    [HttpGet("normToNextPark")]
    public async Task<IActionResult> AdjustValueByParkFactor([FromQuery] double value, [FromQuery] string teamAbbreviation,
        [FromServices] NormalizationService normalizationService)
    {
        try
        {
            // Call the service method to adjust the value
            double adjustedValue = await normalizationService.AdjustValueByParkFactor(value, teamAbbreviation);

            return Ok(new
            {
                OriginalValue = value,
                AdjustedValue = adjustedValue,
                TeamAbbreviation = teamAbbreviation
            });
        }
        catch (Exception ex)
        {
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpGet("getParkFactor")]
    public async Task<IActionResult> GetParkFactor([FromQuery] string teamAbbreviation)
    {
        var teamName = TeamMap(teamAbbreviation);
        if (string.IsNullOrEmpty(teamName))
        {
            return BadRequest("Invalid team abbreviation.");
        }

        var parkFactor = await _context.ParkFactors.FirstOrDefaultAsync(p => p.Team == teamName);

        if (parkFactor == null)
        {
            return NotFound("Park factor not found for the specified team.");
        }

        return Ok(parkFactor);
    }

    public class NormalizeRequest
    {
        public string BbrefId { get; set; }
        public List<string> OppIds { get; set; }
        public int HomeGames { get; set; }
    }
}
