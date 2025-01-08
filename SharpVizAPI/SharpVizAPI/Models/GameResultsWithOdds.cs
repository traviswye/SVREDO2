namespace SharpVizAPI.Models
{
    public class GameResultsWithOdds
    {
        public int Id { get; set; } // Assuming an Id for primary key
        public string Team { get; set; }
        public string Date { get; set; }
        public string Opponent { get; set; }
        public string Score { get; set; }
        public string Result { get; set; }
        public string Odds { get; set; }
        public string OverUnder { get; set; }
        public string OverUnderRes { get; set; }
        public string Pitcher { get; set; }
        public string OpposingPitcher { get; set; }
        public string RecordAsFav { get; set; }
        public string RecordAsDog { get; set; }
        public string OverallRecord { get; set; }
        public double OverallBetter { get; set; }
        public double DogBetter { get; set; }
        public double FavBetter { get; set; }
    }

}
