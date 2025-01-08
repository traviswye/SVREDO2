using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    [Table("Pitcher1stInning")]
    public class Pitcher1stInning
    {
        [Key]
        public string BbrefId { get; set; }  // Player identifier, primary key

        public int G { get; set; }  // Games played
        public float IP { get; set; }  // Innings pitched
        public int ER { get; set; }  // Earned runs
        public float ERA { get; set; }  // Earned Run Average
        public int PA { get; set; }  // Plate appearances
        public int AB { get; set; }  // At-bats
        public int R { get; set; }  // Runs
        public int H { get; set; }  // Hits

        [Column("2B")]
        public int TwoB { get; set; }  // Doubles (2B)

        [Column("3B")]
        public int ThreeB { get; set; }  // Triples (3B)

        public int HR { get; set; }  // Home runs
        public int SB { get; set; }  // Stolen bases
        public int CS { get; set; }  // Caught stealing
        public int BB { get; set; }  // Walks
        public int SO { get; set; }  // Strikeouts
        public float SO_W { get; set; }  // Strikeouts per walk
        public float BA { get; set; }  // Batting average
        public float OBP { get; set; }  // On-base percentage
        public float SLG { get; set; }  // Slugging percentage
        public float OPS { get; set; }  // On-base Plus Slugging
        public int TB { get; set; }  // Total bases
        public int GDP { get; set; }  // Grounded into double play
        public int HBP { get; set; }  // Hit by pitch
        public int SH { get; set; }  // Sacrifice hits
        public int SF { get; set; }  // Sacrifice flies
        public int IBB { get; set; }  // Intentional walks
        public int ROE { get; set; }  // Reached on error
        public float BAbip { get; set; }  // Batting Average on Balls In Play
        public int tOPSPlus { get; set; }  // OPS+ in this split relative to the total OPS+
        public int sOPSPlus { get; set; }  // OPS+ relative to the split
        public DateTime DateModified { get; set; }  // Automatically set to the current date and time

        public int Year { get; set; }  // New column for year
    }
}