using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class TeamRecSplits
    {
        [Key]
        public string Team { get; set; } // Using Team name as the primary key

        public int Wins { get; set; }

        public int Losses { get; set; }

        public double WinPercentage { get; set; }
        public string GB {  get; set; }
        public string WCGB { get; set; }
        public string Streak { get; set; }

        public string L10 { get; set; } // Format example: "7-3"

        public string? L20 { get; set; } // Format example: "14-6", can be null

        public string? L30 { get; set; } // Format example: "20-10", can be null

        public int RunsScored { get; set; }

        public int RunsAgainst { get; set; }

        public int Diff { get; set; } // Difference between RunsScored and RunsAgainst

        public string ExpectedRecord { get; set; } // Format example: "85-77"

        public string HomeRec { get; set; } // Format example: "30-15"

        public string AwayRec { get; set; } // Format example: "20-25"

        public string Xtra { get; set; } // Format example: "5-3"
        [Column("1Run")]
        public string OneRun { get; set; } // Format example: "10-9"

        public string Day { get; set; } // Format example: "15-10"

        public string Night { get; set; } // Format example: "25-20"

        public string Grass { get; set; } // Format example: "20-15"

        public string Turf { get; set; } // Format example: "10-5"

        public string East { get; set; } // Format example: "12-8"

        public string Central { get; set; } // Format example: "14-6"

        public string West { get; set; } // Format example: "8-12"

        public string Inter { get; set; } // Format example: "10-8"
        [Column("vs500+")]
        public string Vs500Plus { get; set; } // Format example: "12-10"

        public string VsRHP { get; set; } // Format example: "25-15"

        public string VsLHP { get; set; } // Format example: "15-10"

        public DateTime DateLastModified { get; set; } // To track the last modification date
    }
}
