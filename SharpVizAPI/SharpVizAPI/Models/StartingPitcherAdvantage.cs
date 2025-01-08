namespace SharpVizAPI.Models
{
    public class StartingPitcherAdvantage
    {
        public string Game { get; set; }
        public string HomePitcher { get; set; }
        public string AwayPitcher { get; set; }
        public Dictionary<string, double> ComparisonMetrics { get; set; }
        public string Advantage { get; set; }
        public string HomeWarnings { get; set; }
        public string AwayWarnings { get; set; }
    }

}
