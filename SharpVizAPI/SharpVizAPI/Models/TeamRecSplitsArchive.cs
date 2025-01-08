using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class TeamRecSplitsArchive
    {
        [Key]
        public string Team { get; set; }  // Team name

        public int Wins { get; set; }
        public int Losses { get; set; }
        public string WinPercentage { get; set; } // Use string to match the main model
        public string L10 { get; set; }
        public string? L20 { get; set; }
        public string? L30 { get; set; }
        public int RunsScored { get; set; }
        public int RunsAgainst { get; set; }
        public int Diff { get; set; }
        public string ExpectedRecord { get; set; }
        public string HomeRec { get; set; }
        public string AwayRec { get; set; }
        public string Xtra { get; set; }
        [Column("1Run")]
        public string OneRun { get; set; }
        public string Day { get; set; }
        public string Night { get; set; }
        public string Grass { get; set; }
        public string Turf { get; set; }
        public string East { get; set; }
        public string Central { get; set; }
        public string West { get; set; }
        public string Inter { get; set; }
        [Column("vs500+")]
        public string Vs500Plus { get; set; }
        public string VsRHP { get; set; }
        public string VsLHP { get; set; }
        public DateTime DateLastModified { get; set; }
        public string GB { get; set; } // Use string to match the main model
        public string WCGB { get; set; } // Use string to match the main model
        public string Streak { get; set; }

        // Additional field for year
        public int Year { get; set; }
    }
}
