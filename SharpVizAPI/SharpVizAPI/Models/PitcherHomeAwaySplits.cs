using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class PitcherHomeAwaySplits
    {
        public string bbrefID { get; set; }  // Part of the composite primary key
        public int Year { get; set; }  // Part of the composite primary key
        public string Split { get; set; }  // 'Home' or 'Away', part of the composite primary key

        public int G { get; set; }
        public float IP { get; set; }
        public int PA { get; set; }
        public int AB { get; set; }
        public int R { get; set; }
        public int H { get; set; }
        public int TwoB { get; set; }
        public int ThreeB { get; set; }
        public int HR { get; set; }
        public int SB { get; set; }
        public int CS { get; set; }
        public int BB { get; set; }
        public int SO { get; set; }
        public float SO_W { get; set; }
        public float BA { get; set; }
        public float OBP { get; set; }
        public float SLG { get; set; }
        public float OPS { get; set; }
        public int TB { get; set; }
        public int GDP { get; set; }
        public int HBP { get; set; }
        public int SH { get; set; }
        public int SF { get; set; }
        public int IBB { get; set; }
        public int ROE { get; set; }
        public float BAbip { get; set; }
        public int tOPSPlus { get; set; }
        public int sOPSPlus { get; set; }
    }
}
