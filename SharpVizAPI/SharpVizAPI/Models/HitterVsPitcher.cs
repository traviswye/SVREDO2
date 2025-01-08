using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    [Table("HitterVsPitcher")]  // Explicitly map to the correct table name
    public class HitterVsPitcher
    {

        public int ID { get; set; }  // Self-incrementing primary key
        public string Pitcher { get; set; } = string.Empty;  // Pitcher's name
        public string Hitter { get; set; } = string.Empty;   // Hitter's name

        // Foreign key reference to the GamePreview table (just the ID)
        public int GamePreviewID { get; set; }

        public int PA { get; set; }  // Plate appearances
        public int Hits { get; set; }  // Hits
        public int HR { get; set; }  // Home Runs
        public int RBI { get; set; }  // Runs Batted In
        public int BB { get; set; }  // Walks
        public int SO { get; set; }  // Strikeouts
        public double BA { get; set; }  // Batting Average
        public double OBP { get; set; }  // On-Base Percentage
        public double SLG { get; set; }  // Slugging Percentage
        public double OPS { get; set; }  // On-Base Plus Slugging
        public int SH { get; set; }  // Sacrifice Hits
        public int SF { get; set; }  // Sacrifice Flies
        public int IBB { get; set; }  // Intentional Walks
        public int HBP { get; set; }  // Hit by Pitch
        public string MatchupURL { get; set; } = string.Empty;  // URL for the matchup
    }

}
