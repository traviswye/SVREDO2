using System;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;

namespace SharpVizAPI.Services
{
    public class WeatherService
    {
        private readonly NrfidbContext _context;
        private readonly HttpClient _httpClient;

        public WeatherService(NrfidbContext context)
        {
            _context = context;
            _httpClient = new HttpClient();
        }

        public async Task UpdateWeatherForGamePreviewsAsync()
        {
            var upcomingGames = await _context.GamePreviews
                .Where(g => g.Date >= DateTime.Today)
                .Include(g => g.Venue)
                .ToListAsync();

            foreach (var game in upcomingGames)
            {
                var parkFactor = await _context.ParkFactors.FirstOrDefaultAsync(p => p.Venue == game.Venue);

                if (parkFactor != null)
                {
                    var weatherData = await FetchWeatherDataAsync(parkFactor.Latitude, parkFactor.Longitude, game.Date, game.Time);

                    if (weatherData != null)
                    {
                        game.Temperature = weatherData.Temperature;
                        game.Humidity = weatherData.Humidity;
                        game.RainProbability = weatherData.RainProbability;
                        game.WindSpeed = weatherData.WindSpeed;
                        game.WindDirection = weatherData.WindDirection;
                        game.WindGusts = weatherData.WindGusts;
                        game.RainProb2hr = weatherData.RainProb2hr;
                        game.totalRain = weatherData.TotalRain;

                        game.RelativeWindDirection = CalculateRelativeWindDirection(parkFactor.Direction, weatherData.WindDirection) ?? 0.0;
                        game.WindDescription = TranslateWindDirection(weatherData.WindDirection, parkFactor.Direction);
                    }
                    else
                    {
                        game.Temperature = 0f;
                        game.Humidity = 0f;
                        game.RainProbability = 0f;
                        game.WindSpeed = 0f;
                        game.WindDirection = 0f;
                        game.WindGusts = 0f;
                        game.RainProb2hr = 0f;
                        game.totalRain = 0f;
                        game.RelativeWindDirection = 0f;
                        game.WindDescription = "Unknown";
                    }

                    _context.GamePreviews.Update(game);
                }
            }

            await _context.SaveChangesAsync();
        }



        public async Task<WeatherData> FetchWeatherDataAsync(double latitude, double longitude, DateTime date, string time)
        {
            if (!DateTime.TryParseExact(time, "h:mmtt", System.Globalization.CultureInfo.InvariantCulture, System.Globalization.DateTimeStyles.None, out DateTime parsedTime))
            {
                return null;
            }

            DateTime datetime = date.Date + parsedTime.TimeOfDay;

            // Set start and end times
            DateTime startTime = datetime.AddHours(-1);
            DateTime endTime = datetime.AddHours(3);

            string startMinutely15 = startTime.ToString("yyyy-MM-ddTHH:mm");
            string endMinutely15 = endTime.ToString("yyyy-MM-ddTHH:mm");

            var url = $"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&minutely_15=temperature_2m,relative_humidity_2m,precipitation,precipitation_probability,wind_speed_10m,wind_direction_10m,wind_gusts_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FNew_York&start_minutely_15={startMinutely15}&end_minutely_15={endMinutely15}";

            var response = await _httpClient.GetAsync(url);

            if (response.IsSuccessStatusCode)
            {
                var jsonString = await response.Content.ReadAsStringAsync();
                var json = JObject.Parse(jsonString);

                if (json["minutely_15"] != null && json["minutely_15"]["time"] != null)
                {
                    var times = json["minutely_15"]["time"].Select(t => DateTime.Parse((string)t)).ToList();

                    // Find the closest time to the game start time
                    var closestTime = times.OrderBy(t => Math.Abs((t - datetime).Ticks)).FirstOrDefault();
                    var index = times.IndexOf(closestTime);

                    var weatherData = new WeatherData
                    {
                        Temperature = (double?)json["minutely_15"]["temperature_2m"]?[index] ?? 0.0,
                        Humidity = (double?)json["minutely_15"]["relative_humidity_2m"]?[index] ?? 0.0,
                        RainProbability = (double?)json["minutely_15"]["precipitation_probability"]?[index] ?? 0.0,
                        WindSpeed = (double?)json["minutely_15"]["wind_speed_10m"]?[index] ?? 0.0,
                        WindDirection = (double?)json["minutely_15"]["wind_direction_10m"]?[index] ?? 0.0,
                        WindGusts = (double?)json["minutely_15"]["wind_gusts_10m"]?[index] ?? 0.0,
                    };

                    // Calculate max precipitation probability within the first 2 hours
                    DateTime twoHoursAfterStart = datetime.AddHours(2);
                    var twoHourWindowIndices = times.Select((t, i) => new { t, i })
                                                     .Where(ti => ti.t >= closestTime && ti.t <= twoHoursAfterStart)
                                                     .Select(ti => ti.i)
                                                     .ToList();

                    if (twoHourWindowIndices.Any())
                    {
                        weatherData.RainProb2hr = twoHourWindowIndices.Max(i => (double?)json["minutely_15"]["precipitation_probability"]?[i] ?? 0.0);
                        weatherData.TotalRain = twoHourWindowIndices.Sum(i => (double?)json["minutely_15"]["precipitation"]?[i] ?? 0.0);
                    }

                    return weatherData;
                }
            }

            return null;
        }




        public double? CalculateRelativeWindDirection(double? stadiumDirection, double? windDirection)
        {
            if (!stadiumDirection.HasValue || !windDirection.HasValue)
            {
                return null; // Return null if either value is null
            }

            // Adjust the wind direction relative to the stadium's orientation.
            // The wind direction tells us where the wind is coming from, so we need to calculate
            // its direction relative to the home plate.

            // Relative wind direction is (windDirection - stadiumDirection)
            var relativeDirection = windDirection.Value - stadiumDirection.Value;

            // Normalize the result between 0 and 360 degrees.
            if (relativeDirection < 0) relativeDirection += 360;
            if (relativeDirection > 360) relativeDirection -= 360;

            return relativeDirection;
        }




        public float? CalculateRelativeWindDirection(float? stadiumDirection, float? windDirection)
        {
            if (!stadiumDirection.HasValue || !windDirection.HasValue)
            {
                return null; // Return null if either value is null
            }

            // Calculate the wind direction relative to home plate
            var relativeDirection = windDirection.Value - stadiumDirection.Value;

            // Normalize the direction to be within 0-360 degrees
            if (relativeDirection < 0) relativeDirection += 360;
            if (relativeDirection > 360) relativeDirection -= 360;

            return relativeDirection;
        }

        public string TranslateWindDirection(double windDirection, double stadiumHeading)
        {
            double relativeDirection = windDirection - stadiumHeading;

            // Normalize to 0-360 degrees
            if (relativeDirection < 0) relativeDirection += 360;
            if (relativeDirection > 360) relativeDirection -= 360;

            // Now interpret relative direction
            if ((relativeDirection >= 0 && relativeDirection <= 15) || (relativeDirection >= 345 && relativeDirection < 360))
                return "Blowing in from center";  // Wind coming from behind
            else if (relativeDirection > 15 && relativeDirection <= 45)
                return "Blowing in from right-center";
            else if (relativeDirection > 45 && relativeDirection <= 75)
                return "Blowing in from right";
            else if (relativeDirection > 75 && relativeDirection <= 105)
                return "Crosswind from right to left";
            else if (relativeDirection > 105 && relativeDirection <= 135)
                return "Blowing out to left";
            else if (relativeDirection > 135 && relativeDirection <= 165)
                return "Blowing out to left-center";
            else if (relativeDirection > 165 && relativeDirection <= 195)
                return "Blowing out to center"; // Fixed: Wind blowing out to center when relative direction is 188
            else if (relativeDirection > 195 && relativeDirection <= 225)
                return "Blowing out to right-center"; // Fixed: Continuing the pattern of outward directions
            else if (relativeDirection > 225 && relativeDirection <= 255)
                return "Blowing out to right";
            else if (relativeDirection > 255 && relativeDirection <= 285)
                return "Crosswind from left to right";
            else if (relativeDirection > 285 && relativeDirection <= 315)
                return "Blowing in from left";
            else if (relativeDirection > 315 && relativeDirection < 345)
                return "Blowing in from left-center";

            return "Calm";
        }




    }

    public class WeatherData
    {
        public double Temperature { get; set; }
        public double Humidity { get; set; }
        public double RainProbability { get; set; }
        public double WindSpeed { get; set; }
        public double WindDirection { get; set; }
        public double WindGusts { get; set; } // New property
        public double RainProb2hr { get; set; } // New property
        public double TotalRain { get; set; } // New property
    }


}
