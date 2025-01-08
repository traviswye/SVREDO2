namespace SharpVizAPI.Models
{
    public class HitterTempTracking
    {
        public string BbrefId { get; set; } // Maps to bbrefid
        public int Year { get; set; }       // Maps to year
        public string Team { get; set; }
        public DateTime Date { get; set; } // Maps to date
        public double CurrentTemp { get; set; } // Maps to currentTemp
        public double? TrailingTemp1 { get; set; } // Maps to trailingTemp1
        public double? TrailingTemp2 { get; set; } // Maps to trailingTemp2
        public double? TrailingTemp3 { get; set; } // Maps to trailingTemp3
        public double? TrailingTemp4 { get; set; } // Maps to trailingTemp4
        public double? TrailingTemp5 { get; set; } // Maps to trailingTemp5
        public double? TrailingTemp6 { get; set; } // Maps to trailingTemp6
    }

}
