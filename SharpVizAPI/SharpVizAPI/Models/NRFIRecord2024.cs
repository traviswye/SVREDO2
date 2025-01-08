using Microsoft.EntityFrameworkCore;
namespace SharpVizAPI.Models
{
    public class NRFIRecord2024
    {
        public string Team { get; set; }
        public string? NRFIRecord { get; set; }
        public string? Home { get; set; }
        public string? Away { get; set; }
        public double? RunsPerFirst { get; set; }
        public int? LastGame { get; set; }
        public double RunsAtHome { get; set; }
        public double RunsAtAway { get; set; }
        public int Year { get; set; }
        public DateTime DateModified { get; set; } // Ensure this property is in your model

        // Parameterless constructor for EF
        public NRFIRecord2024() { }

        // Optional constructor
        public NRFIRecord2024(string team)
        {
            Team = team;
        }
    }

}