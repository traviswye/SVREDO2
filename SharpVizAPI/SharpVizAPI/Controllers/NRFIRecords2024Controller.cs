using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using SharpVizAPI.Models; // Directly import the GamePreview class
using SharpVizAPI.Data; // Directly import the GamePreview class

[ApiController]
[Route("api/[controller]")]
public class NRFIRecords2024Controller : ControllerBase
{
    private readonly NrfidbContext _context;

    public NRFIRecords2024Controller(NrfidbContext context)
    {
        _context = context;
    }

    [HttpPost]
    public async Task<IActionResult> CreateNRFIRecord([FromBody] NRFIRecord2024 nrfiRecord)
    {
        if (nrfiRecord == null || nrfiRecord.Year == 0)
        {
            return BadRequest("Invalid data or missing year.");
        }

        _context.NRFIRecords2024.Add(nrfiRecord);
        await _context.SaveChangesAsync();

        return Ok(nrfiRecord);
    }


    [HttpPost("batch")]
    public async Task<IActionResult> CreateNRFIRecords([FromBody] List<NRFIRecord2024> nrfiRecords)
    {
        if (nrfiRecords == null || !nrfiRecords.Any() || nrfiRecords.Any(n => n.Year == 0))
        {
            return BadRequest("Invalid data or missing year.");
        }

        _context.NRFIRecords2024.AddRange(nrfiRecords);
        await _context.SaveChangesAsync();

        return Ok(nrfiRecords);
    }
    [HttpPut("{team}/{year}")]
    public async Task<IActionResult> UpdateNRFIRecord(string team, int year, [FromBody] NRFIRecord2024 updatedNRFIRecord)
    {
        if (updatedNRFIRecord == null || team != updatedNRFIRecord.Team || year != updatedNRFIRecord.Year)
        {
            return BadRequest("Invalid data.");
        }

        try
        {
            var existingNRFIRecord = await _context.NRFIRecords2024
                .FirstOrDefaultAsync(n => n.Team == team && n.Year == year);

            if (existingNRFIRecord == null)
            {
                return NotFound("NRFI record not found.");
            }

            existingNRFIRecord.NRFIRecord = updatedNRFIRecord.NRFIRecord;
            existingNRFIRecord.Home = updatedNRFIRecord.Home;
            existingNRFIRecord.Away = updatedNRFIRecord.Away;
            existingNRFIRecord.RunsPerFirst = updatedNRFIRecord.RunsPerFirst;
            existingNRFIRecord.LastGame = updatedNRFIRecord.LastGame;
            existingNRFIRecord.RunsAtHome = updatedNRFIRecord.RunsAtHome;
            existingNRFIRecord.RunsAtAway = updatedNRFIRecord.RunsAtAway;
            existingNRFIRecord.DateModified = DateTime.Now;

            await _context.SaveChangesAsync();

            return Ok(existingNRFIRecord);
        }
        catch (Exception ex)
        {
            return StatusCode(500, $"Internal server error: {ex.Message}");
        }
    }


    [HttpGet("{year}")]
    public async Task<IActionResult> GetNRFIRecordsByYear(int year)
    {
        var records = await _context.NRFIRecords2024
            .Where(n => n.Year == year)
            .ToListAsync();

        if (records == null || !records.Any())
        {
            return NotFound("No records found for the specified year.");
        }

        return Ok(records);
    }



}
