namespace SharpVizAPI.Models
{
    public class PitchingAverage
    {
        public int Id { get; set; }
        public int Year { get; set; }
        public int Tms { get; set; }
        public int NumP { get; set; }
        public double PAge { get; set; }
        public double R_G { get; set; }
        public double ERA { get; set; }
        public int G { get; set; }
        public double GF { get; set; }
        public double CG { get; set; }
        public double SHO { get; set; }
        public double tSho { get; set; }
        public double SV { get; set; }
        public double IP { get; set; }
        public double H { get; set; }
        public double R { get; set; }
        public double ER { get; set; }
        public double HR { get; set; }
        public double BB { get; set; }
        public double IBB { get; set; }
        public double SO { get; set; }
        public double HBP { get; set; }
        public double BK { get; set; }
        public double WP { get; set; }
        public double BF { get; set; }
        public double WHIP { get; set; }
        public string BAbip { get; set; } // Keep this as string if it's meant to hold non-numeric values
        public double H9 { get; set; }
        public double HR9 { get; set; }
        public double BB9 { get; set; }
        public double SO9 { get; set; }
        public double SOW { get; set; }
        public double E { get; set; }
    }

}
