using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Linq;
using System.Threading.Tasks;
using System.Collections.Generic;
using SharpVizAPI.Models; // Directly import the GamePreview class
using SharpVizAPI.Data; // Directly import the GamePreview class
using SharpVizAPI.Services; // Directly import the GamePreview class


[ApiController]
[Route("api/[controller]")]
public class EvaluationController : ControllerBase
{
    private readonly NrfidbContext _context;
    private readonly EvaluationService _evaluationService;
    private readonly ILogger<EvaluationService> _logger;

    public EvaluationController(NrfidbContext context, EvaluationService evaluationService, ILogger<EvaluationService> logger)
    {
        _context = context;
        _evaluationService = evaluationService;
        _logger = logger;
    }

    [HttpGet("evaluateNRFI/{date}")]
    public async Task<IActionResult> EvaluateNRFI(string date)
    {
        if (!DateTime.TryParse(date, out DateTime parsedDate))
        {
            return BadRequest("Invalid date format. Please use 'yyyy-MM-dd'.");
        }

        var gamePreviews = await _context.GamePreviews
            .Where(g => g.Date.Date == parsedDate.Date)
            .ToListAsync();

        if (gamePreviews == null || gamePreviews.Count == 0)
        {
            return NotFound($"No game previews found for date: {date}");
        }

        var results = new List<object>();

        foreach (var game in gamePreviews)
        {
            var homeTeamNRFI = await _context.NRFIRecords2024
                .Where(n => n.Team == game.HomeTeam)
                .Select(n => new
                {
                    n.NRFIRecord,
                    n.Home,
                    n.RunsPerFirst,
                    n.RunsAtHome
                })
                .FirstOrDefaultAsync();

            var awayTeamNRFI = await _context.NRFIRecords2024
                .Where(n => n.Team == game.AwayTeam)
                .Select(n => new
                {
                    n.NRFIRecord,
                    n.Away,
                    n.RunsPerFirst,
                    n.RunsAtAway
                })
                .FirstOrDefaultAsync();

            var venueDetails = await _context.ParkFactors
                .Where(p => p.Venue == game.Venue)
                .Select(p => new
                {
                    p.ParkFactorRating,
                    p.zipcode,
                    p.RoofType,
                    p.HR,

                    game.Temperature,
                    game.Humidity,
                    game.RainProbability,
                    game.RainProb2hr,
                    game.totalRain,
                    game.WindSpeed,
                    game.WindDirection,
                    game.WindGusts,
                    game.WindDescription
                })
                .FirstOrDefaultAsync();

            var homePitcherStats = await _context.Pitchers
                .Where(p => p.BbrefId == game.HomePitcher)
                .FirstOrDefaultAsync();

            var awayPitcherStats = await _context.Pitchers
                .Where(p => p.BbrefId == game.AwayPitcher)
                .FirstOrDefaultAsync();

            var homePitcherFirstInningStats = await _context.Pitcher1stInnings
                .Where(p => p.BbrefId == game.HomePitcher)
                .FirstOrDefaultAsync();

            var awayPitcherFirstInningStats = await _context.Pitcher1stInnings
                .Where(p => p.BbrefId == game.AwayPitcher)
                .FirstOrDefaultAsync();

            var gameData = new
            {
                game.Time,
                game.HomeTeam,
                game.AwayTeam,
                game.Venue,
                homeTeamNRFI,
                awayTeamNRFI,
                VenueDetails = venueDetails,
                HomePitcher = new { Stats = homePitcherStats, FirstInningStats = homePitcherFirstInningStats },
                AwayPitcher = new { Stats = awayPitcherStats, FirstInningStats = awayPitcherFirstInningStats }
            };

            results.Add(gameData);
        }

        return Ok(results);
    }
    [HttpGet("evaluateNRFI1st/{date}")]
    public async Task<IActionResult> EvaluateNRFI1st(string date)
    {
        var result = await _evaluationService.Calculate1stInningRunExpectancy(date);

        if (result == null)
        {
            return NotFound($"No data available for date: {date}");
        }

        return Ok(result);
    }


    [HttpGet("evaluateWithBaseState/{date}")]
    public async Task<IActionResult> EvaluateWithBaseState(string date)
    {
        _logger.LogInformation($"Received request to evaluate with base state for date: {date}");

        var result = await _evaluationService.CalculateInningWithBaseState(date);

        if (result == null)
        {
            _logger.LogWarning($"No data available for date: {date}");
            return NotFound($"No data available for date: {date}");
        }

        _logger.LogInformation("Evaluation with base state completed successfully.");

        return Ok(result);
    }

    //[HttpGet("simulateGames/{date}")]
    //public async Task<IActionResult> SimulateGames(string date)
    //{
    //    _logger.LogInformation("Received request to simulate games for date: {date}");

    //    var result = await _evaluationService.SimulateGames(date);

    //    if (result == null)
    //    {
    //        _logger.LogWarning($"No data available for date: {date}");
    //        return NotFound($"No data available for date: {date}");
    //    }

    //    _logger.LogInformation("Simulation completed successfully.");

    //    return Ok(result);
    //}





}
