using System.ComponentModel.DataAnnotations;
namespace SharpVizAPI.Models
{
    public class TeamSplits
    {
        [Key]
        public string Team { get; set; } // Using Team name as the primary key

        public int Wins { get; set; }

        public int Losses { get; set; }

        public string L10 { get; set; } // Format example: "7-3"

        public string L20 { get; set; } // Format example: "14-6"

        public string L30 { get; set; } // Format example: "20-10"

        public string HomeRec { get; set; } // Format example: "30-15"

        public string AwayRec { get; set; } // Format example: "20-25"

        public string ExtRec { get; set; } // Format example: "10-5"

        public string VsRHP { get; set; } // Format example: "25-15"

        public string VsLHP { get; set; } // Format example: "15-10"

        public string VsInterLeague { get; set; } // Format example: "10-8"
    }
}