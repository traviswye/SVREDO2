namespace SharpVizAPI.Models
{
    public class DailyLineupStrengthResponse
    {
        public string Date { get; set; }
        public int GamesAnalyzed { get; set; }
        public double LeagueAverageOPS { get; set; }
        public List<GameLineupAnalysis> Games { get; set; }
        public DailyLineupOverview DailyOverview { get; set; }
    }

    public class GameLineupAnalysis
    {
        public int GameId { get; set; }
        public string Date { get; set; }
        public TeamLineupAnalysis HomeTeam { get; set; }
        public TeamLineupAnalysis AwayTeam { get; set; }
        public HeadToHeadComparison HeadToHead { get; set; }
    }

    public class TeamLineupAnalysis
    {
        public string Team { get; set; }
        public string OpposingPitcher { get; set; }
        public LineupStats LineupStats { get; set; }
        public string ComparedToLeague { get; set; }
    }

    public class LineupStats
    {
        public List<BatterDetail> BatterDetails { get; set; }
        public double SeasonOPS { get; set; }
        public double Last7OPS { get; set; }
        public double BlendedOPS { get; set; }
        public WeightDistribution Weight { get; set; }
        public string[] Warnings { get; set; }
    }

    public class BatterDetail
    {
        public string BatterId { get; set; }
        public int Position { get; set; }
        public BattingStats SeasonStats { get; set; }
        public BattingStats Last7Stats { get; set; }
        public double WeightedOPS { get; set; }
        public bool HasRecentStats { get; set; }
    }

    public class BattingStats
    {
        public double BA { get; set; }
        public double OBP { get; set; }
        public double SLG { get; set; }
        public double OPS { get; set; }
        public int PA { get; set; }
        public int AB { get; set; }
        public int HR { get; set; }
        public int BB { get; set; }
        public int SO { get; set; }
    }

    public class WeightDistribution
    {
        public string Season { get; set; }
        public string Recent { get; set; }
    }

    public class HeadToHeadComparison
    {
        public string StrongerLineup { get; set; }
        public string OpsDifferential { get; set; }
        public OPSComparison SeasonLongComparison { get; set; }
        public OPSComparison Last7DaysComparison { get; set; }
        public OPSComparison BlendedComparison { get; set; }
        public RunsComparison ExpectedRuns { get; set; }
    }

    public class OPSComparison
    {
        public string Differential { get; set; }
        public string StrongerTeam { get; set; }
        public TeamOPSDetail Team1 { get; set; }
        public TeamOPSDetail Team2 { get; set; }
    }

    public class TeamOPSDetail
    {
        public string Team { get; set; }
        public double OPS { get; set; }
    }

    public class RunsComparison
    {
        public TeamRunsDetail Team1 { get; set; }
        public TeamRunsDetail Team2 { get; set; }
        public double Differential { get; set; }
    }

    public class TeamRunsDetail
    {
        public string Team { get; set; }
        public double ExpectedRuns { get; set; }
    }

    public class DailyLineupOverview
    {
        public TeamOPS StrongestLineup { get; set; }
        public TeamOPS WeakestLineup { get; set; }
    }

    public class TeamOPS
    {
        public string Team { get; set; }
        public double OPS { get; set; }
    }
}