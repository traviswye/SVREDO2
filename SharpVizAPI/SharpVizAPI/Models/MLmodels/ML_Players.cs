namespace SharpVizAPI.Models.MLmodels
{
    public class ML_Players
    {
        public int PlayerID { get; set; }
        public string Name { get; set; }
        public int TeamID { get; set; }
        public string Position { get; set; }
        public string SeasonStats { get; set; } // JSON or string representation
        public string CumulativeStats { get; set; } // JSON or string representation

        public ML_Teams Team { get; set; } // Navigation property
    }

}
