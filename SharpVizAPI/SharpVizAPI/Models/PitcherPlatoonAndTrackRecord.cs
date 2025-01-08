using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{

    public class PitcherPlatoonAndTrackRecord
    {
        public string BbrefID { get; set; }  // Player's Baseball-Reference ID
        public int Year { get; set; }  // Year of the data
        public string Split { get; set; }  // Split type (e.g., Home/Away, vs. LHP/RHP)
        public int G { get; set; }  // Games
        public int PA { get; set; }  // Plate Appearances
        public int AB { get; set; }  // At Bats
        public int R { get; set; }  // Runs
        public int H { get; set; }  // Hits
        [Column("2B")]
        public int TwoB { get; set; }  // Doubles
        [Column("3B")]
        public int ThreeB { get; set; }  // Triples
        public int HR { get; set; }  // Home Runs
        public int SB { get; set; }  // Stolen Bases
        public int CS { get; set; }  // Caught Stealing
        public int BB { get; set; }  // Walks
        public int SO { get; set; }  // Strikeouts
        public double SOW { get; set; }  // Strikeouts per Walk
        public double BA { get; set; }  // Batting Average
        public double OBP { get; set; }  // On-Base Percentage
        public double SLG { get; set; }  // Slugging Percentage
        public double OPS { get; set; }  // On-base Plus Slugging
        public int TB { get; set; }  // Total Bases
        public int GDP { get; set; }  // Grounded into Double Plays
        public int HBP { get; set; }  // Hit by Pitch
        public int SH { get; set; }  // Sacrifice Hits
        public int SF { get; set; }  // Sacrifice Flies
        public int IBB { get; set; }  // Intentional Walks
        public int ROE { get; set; }  // Reached on Error
        public double BAbip { get; set; }  // Batting Average on Balls in Play
        public int tOPSPlus { get; set; }  // OPS+ relative to split
        public int sOPSPlus { get; set; }  // OPS+ relative to league

        public DateTime DateModified { get; set; }  // Date the record was last modified
    }

}