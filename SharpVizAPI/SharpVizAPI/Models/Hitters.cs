using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class Hitter
    {
        [Key]
        [Column(Order = 0)]
        public string bbrefId { get; set; }

        [Key]
        [Column(Order = 1)]
        public int Year { get; set; }

        [Key]
        [Column(Order = 2)]
        public string Team { get; set; }

        public string Name { get; set; }
        public int Age { get; set; }
        public string Lg { get; set; }
        public double WAR { get; set; }
        public int G { get; set; }
        public int PA { get; set; }
        public int AB { get; set; }
        public int R { get; set; }
        public int H { get; set; }
        public int Doubles { get; set; }
        public int Triples { get; set; }
        public int HR { get; set; }
        public int RBI { get; set; }
        public int SB { get; set; }
        public int CS { get; set; }
        public int BB { get; set; }
        public int SO { get; set; }
        public double BA { get; set; }
        public double OBP { get; set; }
        public double SLG { get; set; }
        public double OPS { get; set; }
        public int OPSplus { get; set; }
        public double rOBA { get; set; }
        public int Rbatplus { get; set; }
        public int TB { get; set; }
        public int GIDP { get; set; }
        public int HBP { get; set; }
        public int SH { get; set; }
        public int SF { get; set; }
        public int IBB { get; set; }
        public string Pos { get; set; }
        public string Bats { get; set; }

        public DateTime Date { get; set; }
    }
}
