namespace SharpVizAPI.Models.MLmodels
{
    public class ML_BoxScores
    {
        public int BoxScoreID { get; set; }
        public int GameID { get; set; }
        public int PlayerID { get; set; }
        public string EventType { get; set; } // e.g., 'Single', 'Double', 'Home Run', etc.
        public string Outcome { get; set; } // JSON or detailed outcome
        public int Inning { get; set; }
        public int PitchCount { get; set; }
        public int ScoreBeforeEvent { get; set; }
        public int ScoreAfterEvent { get; set; }

        public ML_Games Game { get; set; } // Navigation property
        public ML_Players Player { get; set; } // Navigation property
    }

}
