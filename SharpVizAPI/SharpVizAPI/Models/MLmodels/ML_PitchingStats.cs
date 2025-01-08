namespace SharpVizAPI.Models.MLmodels
{
    public class ML_PitchingStats
    {
        public int PitchingID { get; set; }
        public int GameID { get; set; }
        public int PlayerID { get; set; }
        public int TeamID { get; set; }
        public float InningsPitched { get; set; }
        public int EarnedRuns { get; set; }
        public int Strikeouts { get; set; }
        public int Walks { get; set; }
        public int HitsAllowed { get; set; }
        public int HomeRunsAllowed { get; set; }
        public string PitchingRole { get; set; } // 'Starting' or 'Relief'

        public ML_Games Game { get; set; } // Navigation property
        public ML_Teams Team { get; set; } // Navigation property
        public ML_Players Player { get; set; } // Navigation property
    }

}
