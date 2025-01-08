namespace SharpVizAPI.Models
{
    public class Pitcher
    {
        public string BbrefId { get; set; }
        public int Year { get; set; }
        public int Age { get; set; }
        public string Team { get; set; }
        public string Lg { get; set; }
        public string WL { get; set; }  // Win-Loss record as a string
        public double WLPercentage { get; set; }  // Win-Loss percentage
        public double ERA { get; set; }  // Earned Run Average
        public int G { get; set; }  // Games played
        public int GS { get; set; }  // Games started
        public int GF { get; set; }  // Games finished
        public int CG { get; set; }  // Complete games
        public int SHO { get; set; }  // Shutouts
        public int SV { get; set; }  // Saves
        public double IP { get; set; }  // Innings pitched
        public int H { get; set; }  // Hits allowed
        public int R { get; set; }  // Runs allowed
        public int ER { get; set; }  // Earned runs
        public int HR { get; set; }  // Home runs allowed
        public int BB { get; set; }  // Walks allowed
        public int IBB { get; set; }  // Intentional walks allowed
        public int SO { get; set; }  // Strikeouts
        public int HBP { get; set; }  // Hit by pitches
        public int BK { get; set; }  // Balks
        public int WP { get; set; }  // Wild pitches
        public int BF { get; set; }  // Batters faced
        public int ERAPlus { get; set; }  // Adjusted ERA
        public double FIP { get; set; }  // Fielding Independent Pitching
        public double WHIP { get; set; }  // Walks and Hits per Inning Pitched
        public double H9 { get; set; }  // Hits per 9 innings
        public double HR9 { get; set; }  // Home runs per 9 innings
        public double BB9 { get; set; }  // Walks per 9 innings
        public double SO9 { get; set; }  // Strikeouts per 9 innings
        public double SOW { get; set; }  // Strikeouts per walk
        public DateTime DateModified { get; set; }  // Automatically set to the current date and time
        public string? Throws { get; set; }


    }
}