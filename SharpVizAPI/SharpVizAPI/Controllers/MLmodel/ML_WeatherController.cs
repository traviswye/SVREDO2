using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using SharpVizAPI.Models.MLmodels;
using SharpVizAPI.Data;
using Microsoft.EntityFrameworkCore;

namespace SharpVizAPI.Controllers.MLmodel
{
    [Route("api/[controller]")]
    [ApiController]
    public class ML_WeatherController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ML_WeatherController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ML_Weather
        [HttpGet]
        public ActionResult<IEnumerable<ML_Weather>> GetWeather()
        {
            return _context.ML_Weather.ToList();
        }

        // GET: api/ML_Weather/5
        [HttpGet("{id}")]
        public ActionResult<ML_Weather> GetWeather(int id)
        {
            var weather = _context.ML_Weather.Find(id);

            if (weather == null)
            {
                return NotFound();
            }

            return weather;
        }

        // POST: api/ML_Weather
        [HttpPost]
        public ActionResult<ML_Weather> PostWeather(ML_Weather weather)
        {
            _context.ML_Weather.Add(weather);
            _context.SaveChanges();

            return CreatedAtAction("GetWeather", new { id = weather.WeatherID }, weather);
        }

        // PUT: api/ML_Weather/5
        [HttpPut("{id}")]
        public IActionResult PutWeather(int id, ML_Weather weather)
        {
            if (id != weather.WeatherID)
            {
                return BadRequest();
            }

            _context.Entry(weather).State = Microsoft.EntityFrameworkCore.EntityState.Modified;

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!_context.ML_Weather.Any(e => e.WeatherID == id))
                {
                    return NotFound();
                }
                else
                {
                    throw;
                }
            }

            return NoContent();
        }

        // DELETE: api/ML_Weather/5
        [HttpDelete("{id}")]
        public ActionResult<ML_Weather> DeleteWeather(int id)
        {
            var weather = _context.ML_Weather.Find(id);
            if (weather == null)
            {
                return NotFound();
            }

            _context.ML_Weather.Remove(weather);
            _context.SaveChanges();

            return weather;
        }
    }
}
