using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    [Table("TeamTotalBattingTracking")]
    public class TeamTotalBattingTracking
    {
        [Key]
        //[Column(Order = 0)]
        [Column("team_name", Order =0)]
        public string TeamName { get; set; }

        [Key]
        [Column(Order = 1)]
        public int Year { get; set; }

        [Key]
        [Column(Order = 2)]
        public DateTime DateAdded { get; set; }

        [Column("batters_used")]
        public int? batters_used { get; set; }
        [Column("age_bat")]
        public decimal? age_bat { get; set; }
        [Column("runs_per_game")]
        public decimal? runs_per_game { get; set; }
        public int? G { get; set; }
        public int? PA { get; set; }
        public int? AB { get; set; }
        public int? R { get; set; }
        public int? H { get; set; }
        [Column("2B")]
        public int? Doubles { get; set; }
        [Column("3B")]
        public int? Triples { get; set; }
        public int? HR { get; set; }
        public int? RBI { get; set; }
        public int? SB { get; set; }
        public int? CS { get; set; }
        public int? BB { get; set; }
        public int? SO { get; set; }
        [Column("batting_avg")]
        public decimal? batting_avg { get; set; }
        [Column("onbase_perc")]

        public decimal? onbase_perc { get; set; }
        [Column("slugging_perc")]

        public decimal? slugging_perc { get; set; }
        [Column("onbase_plus_slugging")]

        public decimal? onbase_plus_slugging { get; set; }
        [Column("onbase_plus_slugging_plus")]

        public int? onbase_plus_slugging_plus { get; set; }
        public int? TB { get; set; }
        public int? GIDP { get; set; }
        public int? HBP { get; set; }
        public int? SH { get; set; }
        public int? SF { get; set; }
        public int? IBB { get; set; }
        public int? LOB { get; set; }
    }
}
