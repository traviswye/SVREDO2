namespace SharpVizAPI.Models.MLmodels
{
    public class ML_Games
    {
        public int GameID { get; set; }
        public DateTime Date { get; set; }
        public string StartTime { get; set; }
        public int HomeTeamID { get; set; }
        public int AwayTeamID { get; set; }
        public int BallparkID { get; set; }
        public int HomeTeamScore { get; set; }
        public int AwayTeamScore { get; set; }
        public int WeatherID { get; set; }
        public string Result { get; set; } // 'HomeWin' or 'AwayWin'
        public bool ExtraInnings { get; set; }

        public ML_Teams HomeTeam { get; set; } // Navigation property
        public ML_Teams AwayTeam { get; set; } // Navigation property
        public ML_Ballparks Ballpark { get; set; } // Navigation property
        public ML_Weather Weather { get; set; } // Navigation property
    }

}
