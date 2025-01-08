using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class HittersTrailingGamelog
    {
        public string BbrefId { get; set; }
        public string Name { get; set; }
        public int? Age { get; set; }
        public int Year { get; set; }
        public string Team { get; set; }
        public string Lg { get; set; }
        public int G { get; set; }

        // Advanced statistics fields
        public int PA { get; set; }
        public int AB { get; set; }
        public int R { get; set; }
        public int H { get; set; }
        [Column("2B")]
        public int Doubles { get; set; }
        [Column("3B")]
        public int Triples { get; set; }
        public int HR { get; set; }
        public int RBI { get; set; }
        public int BB { get; set; }
        public int IBB { get; set; }
        public int SO { get; set; }
        public int HBP { get; set; }
        public int SH { get; set; }
        public int SF { get; set; }
        public int ROE { get; set; }
        public int GDP { get; set; }
        public int SB { get; set; }
        public int CS { get; set; }
        public double BA { get; set; }
        public double OBP { get; set; }
        public double SLG { get; set; }
        public double OPS { get; set; }
        public double BOP { get; set; }
        public double aLI { get; set; }
        public double WPA { get; set; }
        public double acLI { get; set; }
        public double cWPA { get; set; }
        public double RE24 { get; set; }
        public double DFS_DK { get; set; }
        public double DFS_FD { get; set; }
        public string Pos { get; set; }
        public DateTime Date { get; set; }
    }
}
