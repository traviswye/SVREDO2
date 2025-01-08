using System;

namespace SharpVizAPI.Models
{
    public class TeamTemperatureTracking
    {
        public string Team { get; set; }
        public int Year { get; set; }
        public int CurrentTemp { get; set; }
        public int Wins { get; set; }
        public int Loses { get; set; }
        public double WinPerc { get; set; }
        public int RS { get; set; }  // Runs Scored
        public int RA { get; set; }  // Runs Allowed
        public double PythagPerc { get; set; }
        public int Streak { get; set; }
        public string LastResult { get; set; }
        public int PreviousTemp { get; set; }
        public DateTime Date { get; set; }

        public int GameNumber { get; set; }  // Newly added property

        // Updated composite key
        public override bool Equals(object obj)
        {
            return obj is TeamTemperatureTracking tracking &&
                   Team == tracking.Team &&
                   Year == tracking.Year &&
                   Date == tracking.Date &&
                   GameNumber == tracking.GameNumber;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Team, Year, Date, GameNumber);
        }
    }

}
