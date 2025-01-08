namespace SharpVizAPI.Models
{
    public class GameDetails
    {
        public string HomeTeam { get; set; }
        public string AwayTeam { get; set; }
        public string HomeSP { get; set; }
        public string AwaySP { get; set; }
        public string HomeSPThrows { get; set; }
        public string AwaySPThrows { get; set; }
        public string HomeSPTrend { get; set; }
        public string AwaySPTrend { get; set; }
        public decimal HomeLineupScoreAvg { get; set; }
        public decimal AwayLineupScoreAvg { get; set; }
        public string HomeRecordVsOpposingSPThrows { get; set; }
        public string AwayRecordVsOpposingSPThrows { get; set; }
        public string HomeRecordHome { get; set; }
        public string AwayRecordAway { get; set; }
    }

}
