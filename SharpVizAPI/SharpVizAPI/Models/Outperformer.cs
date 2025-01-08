namespace SharpVizAPI.Models
{

    public class Outperformer
    {
        public string PlayerName { get; set; }
        public string Team { get; set; }
        public double OutperformanceScore { get; set; }
        public int AtBats { get; set; }
        public double BADifference { get; set; }
        public double OBPDifference { get; set; }
        public double SLGDifference { get; set; }
        public double OPSDifference { get; set; }
        public double? Rostered { get; set; }  // Make rostered nullable if it can be null or a non-integer value
        public string Pos { get; set; }
        public string bbrefId { get; set; }
    }


}
