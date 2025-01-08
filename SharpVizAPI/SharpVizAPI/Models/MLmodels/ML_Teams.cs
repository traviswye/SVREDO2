namespace SharpVizAPI.Models.MLmodels
{
    public class ML_Teams
    {
        public int TeamID { get; set; }
        public string TeamName { get; set; }
        public string Abbreviation { get; set; }
        public int Wins { get; set; }
        public int Losses { get; set; }
        public int Ties { get; set; } // Default is 0, can be ignored if not applicable
    }

}
