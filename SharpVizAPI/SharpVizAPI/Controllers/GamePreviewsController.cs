using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System;
using System.Linq;
using System.Threading.Tasks;
using SharpVizAPI.Services;
using SharpVizAPI.Data;
using SharpVizAPI.Models;


[ApiController]
[Route("api/[controller]")]
public class GamePreviewsController : ControllerBase
{
    private readonly NrfidbContext _context;
    private readonly WeatherService _weatherService;
    private readonly LineupService _lineupService;

    public GamePreviewsController(NrfidbContext context, WeatherService weatherService, LineupService lineupService)
    {
        _context = context;
        _weatherService = weatherService;
        _lineupService = lineupService;
    }
    [HttpPost]
    public async Task<IActionResult> CreateGamePreview([FromBody] GamePreviewDto gamePreviewDto)
    {
        if (gamePreviewDto == null)
        {
            return BadRequest("Invalid data.");
        }

        var venue = await _context.ParkFactors
                                  .Where(p => p.Team == gamePreviewDto.HomeTeam)
                                  .Select(p => p.Venue)
                                  .FirstOrDefaultAsync();

        if (venue == null)
        {
            return NotFound("Venue not found for the specified home team.");
        }

        var gamePreview = new GamePreview
        {
            Date = gamePreviewDto.Date,
            Time = gamePreviewDto.Time,
            HomeTeam = gamePreviewDto.HomeTeam,
            AwayTeam = gamePreviewDto.AwayTeam,
            Venue = venue,
            HomePitcher = !string.IsNullOrEmpty(gamePreviewDto.HomePitcher) && gamePreviewDto.HomePitcher != "Unannounced" ? gamePreviewDto.HomePitcher : "Unannounced",
            AwayPitcher = !string.IsNullOrEmpty(gamePreviewDto.AwayPitcher) && gamePreviewDto.AwayPitcher != "Unannounced" ? gamePreviewDto.AwayPitcher : "Unannounced",
            PreviewLink = gamePreviewDto.PreviewLink,
            DateModified = DateTime.UtcNow
        };

        // Add weather data if available
        var parkFactor = await _context.ParkFactors.FirstOrDefaultAsync(p => p.Venue == venue);
        if (parkFactor != null)
        {
            var weatherData = await _weatherService.FetchWeatherDataAsync(parkFactor.Latitude, parkFactor.Longitude, gamePreview.Date, gamePreview.Time);
            if (weatherData != null)
            {
                gamePreview.Temperature = weatherData.Temperature;
                gamePreview.Humidity = weatherData.Humidity;
                gamePreview.RainProbability = weatherData.RainProbability;
                gamePreview.WindSpeed = weatherData.WindSpeed;
                gamePreview.WindDirection = weatherData.WindDirection;
                gamePreview.RainProb2hr = weatherData.RainProb2hr;
                gamePreview.totalRain = weatherData.TotalRain;
                gamePreview.WindGusts = weatherData.WindGusts;

                double relativeWindDirection = _weatherService.CalculateRelativeWindDirection(parkFactor.Direction, weatherData.WindDirection) ?? 0.0;
                gamePreview.RelativeWindDirection = relativeWindDirection;
                gamePreview.WindDescription = _weatherService.TranslateWindDirection(weatherData.WindDirection, parkFactor.Direction);
            }
        }

        _context.GamePreviews.Add(gamePreview);
        await _context.SaveChangesAsync();

        // After saving, get the generated gamePreviewId
        var gamePreviewId = gamePreview.Id;

        // Fetch and post the lineups for both teams, passing the gamePreviewId
        await _lineupService.FetchAndPostLineupsAndPredictionsAsync(gamePreviewDto.HomeTeam, gamePreviewDto.AwayTeam, gamePreviewId);

        return Ok(gamePreview);
    }


    // GET method to retrieve all game previews by date
    [HttpGet("{date}")]
    public async Task<IActionResult> GetGamePreviewsByDate(string date)
    {
        if (!DateTime.TryParseExact(date, "yy-MM-dd", null, System.Globalization.DateTimeStyles.None, out var parsedDate))
        {
            return BadRequest("Invalid date format. Please use 'yy-MM-dd'.");
        }

        var gamePreviews = await _context.GamePreviews
                                         .Where(gp => gp.Date == parsedDate)
                                         .ToListAsync();

        if (gamePreviews == null || gamePreviews.Count == 0)
        {
            return NotFound("No game previews found for the specified date.");
        }

        return Ok(gamePreviews);
    }


    // New GET method to retrieve home and away pitchers from the last 7 days
    [HttpGet("startingL7Pitchers")]
    public async Task<IActionResult> GetStartingPitchers()
    {
        var last7Days = DateTime.UtcNow.AddDays(-7);

        var pitchers = await _context.GamePreviews
                                     .Where(gp => gp.Date >= last7Days)
                                     .Select(gp => new
                                     {
                                         gp.HomePitcher,
                                         gp.AwayPitcher
                                     })
                                     .ToListAsync();

        if (pitchers == null || pitchers.Count == 0)
        {
            return NotFound("No pitchers found in the last 7 days.");
        }

        return Ok(pitchers);
    }
}

