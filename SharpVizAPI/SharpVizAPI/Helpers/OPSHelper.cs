using SharpVizAPI.Models;

namespace SharpVizAPI.Helpers
{
    public static class OPSHelper
    {
        //public static double ConvertOPSToRunsPerGame(double ops)
        //{
        //    // Formula based on 2024 MLB team data correlation
        //    return (ops * 7) - 0.3;
        //}
        public static double ConvertOPSToRunsPerGame(double oops)
        {
            // New formula based on 2024 MLB team oOPS correlation
            return (oops * 5.2) + 0.1;
        }

        public static double CalculateOPSDifferential(double ops1, double ops2)
        {

            // Convert to points (e.g., 0.800 - 0.700 = 100 points)
            return Math.Round((ops1 - ops2) * 1000, 1);
        }

        public static HeadToHeadComparison CompareLineups(double team1BlendedOPS, string team1Name,
            double team2BlendedOPS, string team2Name,
            LineupStats team1Stats, LineupStats team2Stats)
        {
            // Calculate all differentials (convert to points by multiplying by 1000)
            var seasonDiff = (team1Stats.SeasonOPS - team2Stats.SeasonOPS) * 1000;
            var last7Diff = (team1Stats.Last7OPS - team2Stats.Last7OPS) * 1000;
            var blendedDiff = (team1BlendedOPS - team2BlendedOPS) * 1000;

            // Calculate expected runs based on blended OPS
            var team1ExpectedRuns = ConvertOPSToRunsPerGame(team1BlendedOPS);
            var team2ExpectedRuns = ConvertOPSToRunsPerGame(team2BlendedOPS);
            var runDifferential = Math.Abs(team1ExpectedRuns - team2ExpectedRuns);

            var strongerTeam = team1BlendedOPS > team2BlendedOPS ? team1Name : team2Name;

            return new HeadToHeadComparison
            {
                StrongerLineup = strongerTeam,
                OpsDifferential = $"{Math.Abs(blendedDiff):F1} points",
                SeasonLongComparison = new OPSComparison
                {
                    Differential = $"{Math.Abs(seasonDiff):F1} points",
                    StrongerTeam = seasonDiff > 0 ? team1Name : team2Name,
                    Team1 = new TeamOPSDetail { Team = team1Name, OPS = team1Stats.SeasonOPS },
                    Team2 = new TeamOPSDetail { Team = team2Name, OPS = team2Stats.SeasonOPS }
                },
                Last7DaysComparison = new OPSComparison
                {
                    Differential = $"{Math.Abs(last7Diff):F1} points",
                    StrongerTeam = last7Diff > 0 ? team1Name : team2Name,
                    Team1 = new TeamOPSDetail { Team = team1Name, OPS = team1Stats.Last7OPS },
                    Team2 = new TeamOPSDetail { Team = team2Name, OPS = team2Stats.Last7OPS }
                },
                BlendedComparison = new OPSComparison
                {
                    Differential = $"{Math.Abs(blendedDiff):F1} points",
                    StrongerTeam = blendedDiff > 0 ? team1Name : team2Name,
                    Team1 = new TeamOPSDetail { Team = team1Name, OPS = team1BlendedOPS },
                    Team2 = new TeamOPSDetail { Team = team2Name, OPS = team2BlendedOPS }
                },
                ExpectedRuns = new RunsComparison
                {
                    Team1 = new TeamRunsDetail
                    {
                        Team = team1Name,
                        ExpectedRuns = team1ExpectedRuns
                    },
                    Team2 = new TeamRunsDetail
                    {
                        Team = team2Name,
                        ExpectedRuns = team2ExpectedRuns
                    },
                    Differential = runDifferential
                }
            };
        }
    }
}