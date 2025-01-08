namespace SharpVizAPI.Models.MLmodels
{
    public class ML_Lineups
    {
        public int LineupID { get; set; }
        public int GameID { get; set; }
        public int TeamID { get; set; }
        public int PlayerID { get; set; }
        public int BattingOrder { get; set; }
        public string Position { get; set; }

        public ML_Games Game { get; set; } // Navigation property
        public ML_Teams Team { get; set; } // Navigation property
        public ML_Players Player { get; set; } // Navigation property
    }

}
