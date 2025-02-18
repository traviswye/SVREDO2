using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using SharpVizAPI.Data;
using SharpVizAPI.Models;

namespace SharpVizAPI.Services
{
    public class BlendingService
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<EvaluationService> _logger;

        public BlendingService(NrfidbContext context, ILogger<EvaluationService> logger)
        {
            _context = context;
            _logger = logger;
        }



        private Dictionary<string, string> CreateTeamDictionary()
        {
            return new Dictionary<string, string>
            {
    { "ARI", "Diamondbacks" },
    { "ATL", "Braves" },
    { "BAL", "Orioles" },
    { "BOS", "Red Sox" },
    { "CHW", "White Sox" },
    { "CHC", "Cubs" },
    { "CIN", "Reds" },
    { "CLE", "Guardians" },
    { "COL", "Rockies" },
    { "DET", "Tigers" },
    { "HOU", "Astros" },
    { "KCR", "Royals" },
    { "LAA", "Angels" },
    { "LAD", "Dodgers" },
    { "MIA", "Marlins" },
    { "MIL", "Brewers" },
    { "MIN", "Twins" },
    { "NYY", "Yankees" },
    { "NYM", "Mets" },
    { "OAK", "Athletics" },
    { "PHI", "Phillies" },
    { "PIT", "Pirates" },
    { "SDP", "Padres" },
    { "SFG", "Giants" },
    { "SEA", "Mariners" },
    { "STL", "Cardinals" },
    { "TBR", "Rays" },
    { "TEX", "Rangers" },
    { "TOR", "Blue Jays" },
    { "WSN", "Nationals" }
            };
        }


        private async Task<HashSet<string>> GetTeamsPlayingOnDateAsync(DateTime date)
        {
            var gamesOnDate = await _context.GamePreviews
                                            .Where(gp => gp.Date.Date == date.Date)
                                            .ToListAsync();

            var teamsPlaying = new HashSet<string>();

            foreach (var game in gamesOnDate)
            {
                teamsPlaying.Add(game.HomeTeam);
                teamsPlaying.Add(game.AwayTeam);
            }

            return teamsPlaying;
        }

        private void AddSampleSizeWarnings(Dictionary<string, double> pitcherStats, string pitcherType, Dictionary<string, object> comparisonMetrics)
        {
            if (pitcherStats.ContainsKey("G") && pitcherStats["G"] < 10)
            {
                comparisonMetrics[$"{pitcherType}PitcherSampleSizeWarning"] = "Sample size is significantly low.";
            }
            if (pitcherStats.ContainsKey("PA") && pitcherStats["PA"] < 40)
            {
                comparisonMetrics[$"{pitcherType}PitcherPASampleSizeWarning"] = "PA sample size is significantly low.";
            }
        }

        private async Task<Dictionary<string, double>> GetTotalStatsForPitcher(string pitcherId, int year)
        {
            // Retrieve the pitcher's Total stats for the specified year
            var totalStats = await _context.PitcherPlatoonAndTrackRecord
                                           .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "Totals" && p.Year == year);

            // Check if the record exists
            if (totalStats == null)
            {
                //_logger.LogWarning($"Total stats not found for pitcher {pitcherId} in year {year}");
                return null; // or return an empty dictionary if that's preferred
            }

            // Return the stats as a dictionary
            return new Dictionary<string, double>
    {
        { "G", totalStats.G },
        { "PA", totalStats.PA },
        { "AB", totalStats.AB },
        { "R", totalStats.R },
        { "H", totalStats.H },
        { "HR", totalStats.HR },
        { "SB", totalStats.SB },
        { "CS", totalStats.CS },
        { "BB", totalStats.BB },
        { "SO", totalStats.SO },
        { "SOW", totalStats.SOW },
        { "BA", totalStats.BA },
        { "OBP", totalStats.OBP },
        { "SLG", totalStats.SLG },
        { "OPS", totalStats.OPS },
        { "TB", totalStats.TB },
        { "GDP", totalStats.GDP },
        { "BAbip", totalStats.BAbip },
        { "tOPSPlus", totalStats.tOPSPlus },
        { "sOPSPlus", totalStats.sOPSPlus }
    };
        }

        private async Task<Dictionary<string, double>> GetLast28StatsForPitcher(string pitcherId, int year)
        {
            // Retrieve the pitcher's last 28 days stats for the specified year
            var last28Stats = await _context.PitcherPlatoonAndTrackRecord
                                            .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "last28" && p.Year == year);

            // Check if the record exists
            if (last28Stats == null)
            {
                _logger.LogWarning($"Last 28 days stats not found for pitcher {pitcherId} in year {year}");
                return null; // or return an empty dictionary if that's preferred
            }

            // Return the stats as a dictionary
            return new Dictionary<string, double>
    {
        { "G", last28Stats.G },
        { "PA", last28Stats.PA },
        { "AB", last28Stats.AB },
        { "R", last28Stats.R },
        { "H", last28Stats.H },
        { "HR", last28Stats.HR },
        { "SB", last28Stats.SB },
        { "CS", last28Stats.CS },
        { "BB", last28Stats.BB },
        { "SO", last28Stats.SO },
        { "SOW", last28Stats.SOW },
        { "BA", last28Stats.BA },
        { "OBP", last28Stats.OBP },
        { "SLG", last28Stats.SLG },
        { "OPS", last28Stats.OPS },
        { "TB", last28Stats.TB },
        { "GDP", last28Stats.GDP },
        { "BAbip", last28Stats.BAbip },
        { "tOPSPlus", last28Stats.tOPSPlus },
        { "sOPSPlus", last28Stats.sOPSPlus }
    };
        }



        // Blending logic for combining total and last28 statistics with 60%/40% weight
        // Blending logic for combining total and last28 statistics with customizable weights
        private (Dictionary<string, double> BlendedStats, List<string> Warnings) BlendStats(
            Dictionary<string, double> totalStats,
            Dictionary<string, double> last28Stats,
            string bbrefID,
            double totalWeight,
            double last28Weight)
        {
            var blendedStats = new Dictionary<string, double>();
            var warnings = new List<string>();

            if (last28Stats == null || last28Stats.Count == 0)
            {
                // Add warning if last28 stats are missing
                warnings.Add($"{bbrefID} has no last28 stats available. Using season totals only.");
                last28Stats = new Dictionary<string, double>(); // Set to empty dictionary to avoid null reference

                // If totalStats are also null or empty, add another warning and skip blending
                if (totalStats == null || totalStats.Count == 0)
                {
                    warnings.Add($"{bbrefID} has no season totals or last28 stats. Might be a season debut.");
                    return (null, warnings); // Return null blendedStats with warnings
                }

                // Use total stats only
                return (totalStats, warnings);
            }

            // Blending logic with customizable weights for total and last28 stats
            foreach (var stat in totalStats.Keys)
            {
                if (last28Stats.ContainsKey(stat))
                {
                    blendedStats[stat] = (totalStats[stat] * totalWeight) + (last28Stats[stat] * last28Weight);
                }
                else
                {
                    blendedStats[stat] = totalStats[stat]; // Use only totalStats if last28 is missing for a specific stat
                }
            }

            return (blendedStats, warnings);
        }





        public double CalculatePercentageDifference(double recentStat, double seasonStat)
        {
            return (recentStat - seasonStat) / seasonStat * 100;
        }

        public Dictionary<string, double> CalculateStatWeights(PitcherPlatoonAndTrackRecord recentSplit, PitcherPlatoonAndTrackRecord seasonTotals)
        {
            if (recentSplit == null || seasonTotals == null)
            {
                _logger.LogWarning("One or both of the split records are null.");
                return new Dictionary<string, double>(); // return empty dictionary or handle as needed
            }

            var weights = new Dictionary<string, double>
    {
        { "BA", CalculatePercentageDifference(recentSplit.BA, seasonTotals.BA) },
        { "OBP", CalculatePercentageDifference(recentSplit.OBP, seasonTotals.OBP) },
        { "SLG", CalculatePercentageDifference(recentSplit.SLG, seasonTotals.SLG) },
        { "OPS", CalculatePercentageDifference(recentSplit.OPS, seasonTotals.OPS) },
        { "BAbip", CalculatePercentageDifference(recentSplit.BAbip, seasonTotals.BAbip) }
    };

            return weights;
        }


        public Dictionary<string, double> BlendWeightsAcrossTimeSpans(List<PitcherPlatoonAndTrackRecord> splits, PitcherPlatoonAndTrackRecord seasonTotals)
        {
            // Get the relevant splits (last7, last14, last28)
            var last7 = splits.FirstOrDefault(s => s.Split == "last7");
            var last14 = splits.FirstOrDefault(s => s.Split == "last14");
            var last28 = splits.FirstOrDefault(s => s.Split == "last28");

            // Calculate weights for each split
            var last7Weights = CalculateStatWeights(last7, seasonTotals);
            var last14Weights = CalculateStatWeights(last14, seasonTotals);
            var last28Weights = CalculateStatWeights(last28, seasonTotals);

            // Blend the weights (using a simple average for this example)
            var blendedWeights = new Dictionary<string, double>();
            foreach (var stat in last7Weights.Keys)
            {
                blendedWeights[stat] = (last7Weights[stat] * 0.2) + (last14Weights[stat] * 0.3) + (last28Weights[stat] * 0.5);
            }

            return blendedWeights;
        }

        public PitcherPlatoonAndTrackRecord ApplyBlendedWeights(PitcherPlatoonAndTrackRecord seasonTotals, Dictionary<string, double> blendedWeights)
        {
            // Adjust the season totals using the blended weights
            seasonTotals.BA *= (1 + blendedWeights["BA"] / 100);
            seasonTotals.OBP *= (1 + blendedWeights["OBP"] / 100);
            seasonTotals.SLG *= (1 + blendedWeights["SLG"] / 100);
            seasonTotals.OPS *= (1 + blendedWeights["OPS"] / 100);
            seasonTotals.BAbip *= (1 + blendedWeights["BAbip"] / 100);
            // Add adjustments for more stats as needed

            return seasonTotals;
        }

        // Example usage of the blending process
        public PitcherPlatoonAndTrackRecord BlendRecentAndSeasonPerformance(List<PitcherPlatoonAndTrackRecord> splits)
        {
            // Get the season totals
            var totals = splits.FirstOrDefault(s => s.Split == "Totals");

            if (totals == null)
            {
                _logger.LogWarning("Season totals not found.");
                return null; // or throw an appropriate exception
            }

            // Get the relevant splits (last7, last14, last28)
            var last7 = splits.FirstOrDefault(s => s.Split == "last7");
            var last14 = splits.FirstOrDefault(s => s.Split == "last14");
            var last28 = splits.FirstOrDefault(s => s.Split == "last28");

            // Ensure we have at least last28, since it's essential for blending
            if (last28 == null)
            {
                _logger.LogWarning("Last 28 days split not found.");
                return null; // or handle this case as needed
            }

            // Calculate weights for each split if they exist
            var last7Weights = last7 != null ? CalculateStatWeights(last7, totals) : new Dictionary<string, double>();
            var last14Weights = last14 != null ? CalculateStatWeights(last14, totals) : new Dictionary<string, double>();
            var last28Weights = CalculateStatWeights(last28, totals); // last28 should not be null here

            // Blend the weights (using a simple average for this example)
            var blendedWeights = new Dictionary<string, double>();
            foreach (var stat in last28Weights.Keys)
            {
                blendedWeights[stat] = ((last7Weights.ContainsKey(stat) ? last7Weights[stat] * 0.2 : 0) +
                                        (last14Weights.ContainsKey(stat) ? last14Weights[stat] * 0.3 : 0) +
                                        last28Weights[stat] * 0.5);
            }

            // Apply the blended weights to the season totals
            var blendedModel = ApplyBlendedWeights(totals, blendedWeights);

            return blendedModel;
        }


        public async Task<Dictionary<string, double>> GetBlendingResultsForPitcher(string pitcherId)
        {
            var pitcherTotals = await _context.PitcherPlatoonAndTrackRecord
                                              .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "Totals");

            var last7 = await _context.PitcherPlatoonAndTrackRecord
                                      .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "last7");

            var last14 = await _context.PitcherPlatoonAndTrackRecord
                                       .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "last14");

            var last28 = await _context.PitcherPlatoonAndTrackRecord
                                       .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "last28");

            if (pitcherTotals == null || last28 == null)
            {
                _logger.LogWarning($"No season totals found for pitcher {pitcherId}");
                return null;
            }

            // Calculate trends
            var trends = new Dictionary<string, double>
    {
        { "bA_Trend", CalculateTrend(last28?.BA ?? pitcherTotals.BA, pitcherTotals.BA) },
        { "obP_Trend", CalculateTrend(last28?.OBP ?? pitcherTotals.OBP, pitcherTotals.OBP) },
        { "slG_Trend", CalculateTrend(last28?.SLG ?? pitcherTotals.SLG, pitcherTotals.SLG) },
        { "BAbip_Trend", CalculateTrend(last28?.BAbip ?? pitcherTotals.BAbip, pitcherTotals.BAbip) }

        // Add other trend calculations if needed

    };

            var comparison = CompareLast28WithTotals(last28, pitcherTotals);

            return trends;
        }


        private object CalculateBlendingResults(PitcherPlatoonAndTrackRecord totals, PitcherPlatoonAndTrackRecord last7, PitcherPlatoonAndTrackRecord last14, PitcherPlatoonAndTrackRecord last28)
        {
            // Implement the logic to calculate how the pitcher is trending
            // Compare the last 7, 14, and 28 days with the season totals and return a summary of results

            // You can use the blending logic we discussed earlier here
            var results = new
            {
                BA_Trend = CalculateTrend(last28?.BA ?? totals.BA, totals.BA),
                OBP_Trend = CalculateTrend(last28?.OBP ?? totals.OBP, totals.OBP),
                SLG_Trend = CalculateTrend(last28?.SLG ?? totals.SLG, totals.SLG),
                BAbip_Trend = CalculateTrend(last28?.BAbip ?? totals.BAbip, totals.BAbip),

                // Add more stats as needed
            };

            return results;
        }

        private double CalculateTrend(double recentStat, double seasonStat)
        {
            if (seasonStat == 0) return 0;
            return (recentStat - seasonStat) / seasonStat;
        }

        public Dictionary<string, object> AnalyzeTrends(string pitcherId, Dictionary<string, double> trends)
        {
            // Calculate the average trend
            double avgTrend = (trends["bA_Trend"] + trends["obP_Trend"] + trends["slG_Trend"] + trends["BAbip_Trend"]) / 4;
            string performanceStatus;

            // Determine performance status
            if (avgTrend < -0.10) // More than 10% better than season average
            {
                performanceStatus = "HOT";
            }
            else if (avgTrend > 0.10) // More than 10% worse than season average
            {
                performanceStatus = "COLD";
            }
            else // Within 10% of season averages
            {
                performanceStatus = "CONSISTENT";
            }

            // Generate the plain English message
            string message = $"{pitcherId} is {performanceStatus} right now, pitching {Math.Abs(avgTrend * 100):0.0}% {(avgTrend < 0 ? "better" : "worse")} than his season averages.";

            // Return the dictionary with results and message
            return new Dictionary<string, object>
    {
        { "pitcher", pitcherId },
        { "bA_Trend", trends["bA_Trend"] },
        { "obP_Trend", trends["obP_Trend"] },
        { "slG_Trend", trends["slG_Trend"] },
        { "BAbip_Trend", trends["BAbip_Trend"] },

        { "performanceStatus", performanceStatus },
        { "message", message }
    };
        }



        public async Task<Dictionary<string, object>> Blend1stInningWithPlatoonStats(string pitcherId)
        {
            // Retrieve 1st Inning stats
            var firstInningStats = await _context.Pitcher1stInnings
                                                 .FirstOrDefaultAsync(p => p.BbrefId == pitcherId);
            if (firstInningStats == null)
            {
                _logger.LogWarning($"No 1st inning stats found for pitcher {pitcherId}");
                return new Dictionary<string, object> { { "message", "No 1st inning stats available" } };
            }

            // Retrieve vsLHB and vsRHB splits
            var vsLHB = await _context.PitcherPlatoonAndTrackRecord
                                      .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "vsLHB");
            var vsRHB = await _context.PitcherPlatoonAndTrackRecord
                                      .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "vsRHB");

            if (vsLHB == null || vsRHB == null)
            {
                _logger.LogWarning($"No platoon splits found for pitcher {pitcherId}");
                return new Dictionary<string, object> { { "message", "No platoon splits available" } };
            }

            var blendedLHBStats = new
            {
                BA = (firstInningStats.BA + vsLHB.BA) / 2,
                OBP = (firstInningStats.OBP + vsLHB.OBP) / 2,
                SLG = (firstInningStats.SLG + vsLHB.SLG) / 2,
                OPS = (firstInningStats.OPS + vsLHB.OPS) / 2,
                K_Percentage = ((firstInningStats.SO / firstInningStats.PA) + (vsLHB.SO / vsLHB.PA)) / 2,
                BB_Percentage = ((firstInningStats.BB / firstInningStats.PA) + (vsLHB.BB / vsLHB.PA)) / 2,
                BAbip = ((firstInningStats.H - firstInningStats.HR) / (firstInningStats.AB - firstInningStats.HR - firstInningStats.SO + firstInningStats.SF) +
                         (vsLHB.H - vsLHB.HR) / (vsLHB.AB - vsLHB.HR - vsLHB.SO + vsLHB.SF)) / 2
            };

            var blendedRHBStats = new
            {
                BA = (firstInningStats.BA + vsRHB.BA) / 2,
                OBP = (firstInningStats.OBP + vsRHB.OBP) / 2,
                SLG = (firstInningStats.SLG + vsRHB.SLG) / 2,
                OPS = (firstInningStats.OPS + vsRHB.OPS) / 2,
                K_Percentage = ((firstInningStats.SO / firstInningStats.PA) + (vsRHB.SO / vsRHB.PA)) / 2,
                BB_Percentage = ((firstInningStats.BB / firstInningStats.PA) + (vsRHB.BB / vsRHB.PA)) / 2,
                BAbip = ((firstInningStats.H - firstInningStats.HR) / (firstInningStats.AB - firstInningStats.HR - firstInningStats.SO + firstInningStats.SF) +
                         (vsRHB.H - vsRHB.HR) / (vsRHB.AB - vsRHB.HR - vsRHB.SO + vsRHB.SF)) / 2
            };

            return new Dictionary<string, object>
    {
        { "pitcher", pitcherId },
        { "blendedLHBStats", blendedLHBStats },
        { "blendedRHBStats", blendedRHBStats }
    };
        }

        public async Task<(Hitter hitterSeasonStats, HitterLast7 hitterLast7Stats)> GetHitterStatsAsync(string bbrefId, string date)
        {
            DateTime dateParsed;
            if (!DateTime.TryParse(date, out dateParsed))
            {
                _logger.LogWarning($"Invalid date format: {date}");
                return (null, null);
            }

            var hitterSeasonStats = await _context.Hitters.FirstOrDefaultAsync(h => h.bbrefId == bbrefId);
            var hitterLast7Stats = await _context.HitterLast7.FirstOrDefaultAsync(h => h.BbrefId == bbrefId && h.DateUpdated == dateParsed);

            if (hitterSeasonStats == null || hitterLast7Stats == null)
            {
                _logger.LogWarning($"No stats found for hitter {bbrefId} on {date}");
                return (null, null);
            }

            return (hitterSeasonStats, hitterLast7Stats);
        }



        public Dictionary<string, double> CalculateHitterStatDifferences(Hitter hitterSeasonStats, HitterLast7 hitterLast7Stats)
        {
            return new Dictionary<string, double>
    {
        { "BA", CalculatePercentageDifferenceHitters(hitterLast7Stats.AVG, hitterSeasonStats.BA) },
        { "OBP", CalculatePercentageDifferenceHitters(hitterLast7Stats.OBP, hitterSeasonStats.OBP) },
        { "SLG", CalculatePercentageDifferenceHitters(hitterLast7Stats.SLG, hitterSeasonStats.SLG) },
        { "OPS", CalculatePercentageDifferenceHitters(hitterLast7Stats.OPS, hitterSeasonStats.OPS) }
    };
        }

        public async Task<List<object>> GetOutperformingHittersAsync(string date)
        {
            DateTime dateParsed;
            if (!DateTime.TryParse(date, out dateParsed))
            {
                _logger.LogWarning($"Invalid date format: {date}");
                return null;
            }

            var hitters = await _context.Hitters.ToListAsync();
            var outperformingHitters = new List<object>();

            // Create the team dictionary
            var teamDictionary = CreateTeamDictionary();

            // Get the list of teams playing on the parsed date
            var teamsPlayingToday = await GetTeamsPlayingOnDateAsync(dateParsed);

            foreach (var hitter in hitters)
            {
                var (hitterSeasonStats, hitterLast7Stats) = await GetHitterStatsAsync(hitter.bbrefId, date);
                if (hitterSeasonStats == null)
                {
                    _logger.LogWarning($"No season stats found for hitter {hitter.bbrefId}. Skipping this player.");
                    continue;
                }

                if (hitterLast7Stats == null)
                {
                    _logger.LogWarning($"No last 7 days stats found for hitter {hitter.bbrefId} on {date}. Skipping this player.");
                    continue;
                }

                // Check if the player has more than 10 at-bats in the last 7 days
                if (hitterLast7Stats.AB <= 10) continue;

                // Get the full team name from the abbreviation
                if (!teamDictionary.TryGetValue(hitterLast7Stats.Team, out string fullTeamName)) continue;

                // Check if the player's team is playing today
                if (!teamsPlayingToday.Contains(fullTeamName)) continue;

                var differences = CalculateHitterStatDifferences(hitterSeasonStats, hitterLast7Stats);
                double outperformanceScore = differences.Values.Average();

                // Filter out invalid scores
                if (double.IsNaN(outperformanceScore) || double.IsInfinity(outperformanceScore))
                {
                    continue;
                }

                // Add player details to the output
                outperformingHitters.Add(new
                {
                    PlayerName = hitter.Name,
                    Team = hitterLast7Stats.Team,
                    OutperformanceScore = outperformanceScore,
                    AtBats = hitterLast7Stats.AB,
                    BA_Difference = differences["BA"],
                    OBP_Difference = differences["OBP"],
                    SLG_Difference = differences["SLG"],
                    OPS_Difference = differences["OPS"],
                    Rostered = hitterLast7Stats.ROSTERED,
                    Pos = hitterLast7Stats.Pos,
                    bbrefId = hitterLast7Stats.BbrefId
                });
            }

            if (!outperformingHitters.Any())
            {
                _logger.LogWarning("No outperforming hitters found.");
                return null;
            }

            return outperformingHitters.OrderByDescending(h => ((dynamic)h).OutperformanceScore).ToList();
        }




        public double CalculatePercentageDifferenceHitters(double recentStat, double seasonStat)
        {
            // Avoid division by zero by checking if seasonStat is zero
            if (seasonStat == 0)
            {
                return recentStat == 0 ? 0 : 100;  // If both are zero, return 0; otherwise, return 100% increase
            }

            double difference = (recentStat - seasonStat) / seasonStat * 100;

            // Handle cases where difference might be infinity or NaN
            if (double.IsInfinity(difference) || double.IsNaN(difference))
            {
                return 0;  // Default to 0 if the value is not valid
            }

            return difference;
        }
        //NEED TO REALLY THINK ABOUT HOW TO BLEND HITTERS BC HIT RATE OR TOTAL STATS IS AN ISSUE
        public TrailingGameLogSplit BlendHitterStats(TrailingGameLogSplit seasonStats, TrailingGameLogSplit last7GStats)
        {
            if (seasonStats == null || last7GStats == null)
                throw new ArgumentNullException("Both seasonStats and last7GStats must be provided for blending.");

            return new TrailingGameLogSplit

            {
                BbrefId = seasonStats.BbrefId,
                BA = (seasonStats.BA * 0.6) + (last7GStats.BA * 0.4), // Example 60/40 weight
                OBP = (seasonStats.OBP * 0.6) + (last7GStats.OBP * 0.4),
                SLG = (seasonStats.SLG * 0.6) + (last7GStats.SLG * 0.4),
                OPS = (seasonStats.OPS * 0.6) + (last7GStats.OPS * 0.4),
                HR = (int)((seasonStats.HR * 0.6) + (last7GStats.HR * 0.4)),
                PA = (int)((seasonStats.PA * 0.6) + (last7GStats.PA * 0.4)),
                // Add other stats to blend here as needed
            };
        }


        public Dictionary<string, double> CompareLast28WithTotals(PitcherPlatoonAndTrackRecord last28, PitcherPlatoonAndTrackRecord totals)
        {
            var comparison = new Dictionary<string, double>
    {
        { "BA_Change", CalculatePercentageDifference(last28.BA, totals.BA) },
        { "OBP_Change", CalculatePercentageDifference(last28.OBP, totals.OBP) },
        { "SLG_Change", CalculatePercentageDifference(last28.SLG, totals.SLG) },
        { "OPS_Change", CalculatePercentageDifference(last28.OPS, totals.OPS) },
        { "BAbip_Change", CalculatePercentageDifference(last28.BAbip, totals.BAbip) }
        // Add more stats as needed
    };

            return comparison;
        }

        // Calculate comparison metrics based on weighted comparisons of blended stats
        private Dictionary<string, double> CalculateComparisonMetrics(Dictionary<string, double> homeStats, Dictionary<string, double> awayStats)
        {
            var homeDerivedMetrics = CalculateDerivedMetrics(homeStats);
            var awayDerivedMetrics = CalculateDerivedMetrics(awayStats);

            var comparisonMetrics = new Dictionary<string, double>();

            var weights = new Dictionary<string, double>
    {
                //default weights initial backtesting
    //    {"AB/R", 1},
    //    {"AB/H", 1},
    //    {"PA/HR", 1},
    //    {"AB/SB", .01},
    //    {"SB/SB+CS", .5},// Lower is better
    //    {"PA/BB", 1},
    //    {"AB/SO", .5},// Lower is better
    //    {"SOW", .5},
    //    {"BA", 1},  // Lower is better
    //    {"OBP", 1}, // Lower is better
    //    {"SLG", 1}, // Lower is better
    //    {"OPS", 1}, // Lower is better
    //    {"PA/TB", 1},
    //    {"AB/GDP", .5},
    //    {"BAbip", 1}, // Lower is better
    //    {"tOPSPlus", 1},
    //    {"sOPSPlus", 1}
    //};
            //{
                //ARI optimal weights ?
            { "AB/R", 0.5},
            { "AB/H", 0.5},
            { "PA/HR", 1.5},
            { "AB/SB", 0.1},
            { "SB/SB+CS", 0.5},// Lower is better
            { "PA/BB", 1.5},
            { "AB/SO", .1},// Lower is better
            { "SOW", 1},
            { "BA", .5},  // Lower is better
            { "OBP", 1}, // Lower is better
            { "SLG", .5}, // Lower is better
            { "OPS", 1}, // Lower is better
            { "PA/TB", .5},
            { "AB/GDP", .25},
            { "BAbip", .5}, // Lower is better
            { "tOPSPlus", 1.5},
            { "sOPSPlus", .5}
            };

//average for 10 ballparks
            //            {
            //                'AB_R': 1.1,
            //    'AB_H': 0.7,
            //    'PA_HR': 0.55,
            //    'AB_SB': 0.034,
            //    'SB_SB_CS': 0.44,
            //    'PA_BB': 1.1,
            //    'AB_SO': 0.56,
            //    'SOW': 0.32,
            //    'BA': 0.75,
            //    'OBP': 1.05,
            //    'SLG': 0.8,
            //    'OPS': 0.55,
            //    'PA_TB': 0.6,
            //    'AB_GDP': 0.5,
            //    'BAbip': 1.05,
            //    'tOPSPlus': 0.7,
            //    'sOPSPlus': 0.55
            //}


            //    { "AB/R", 0},
            //    { "AB/H", 1.5},
            //    { "PA/HR", 1.5},
            //    { "AB/SB", 0.01},
            //    { "SB/SB+CS", 0.1},// Lower is better
            //    { "PA/BB", 1},
            //    { "AB/SO", .1},// Lower is better
            //    { "SOW", 1},
            //    { "BA", 1},  // Lower is better
            //    { "OBP", 1}, // Lower is better
            //    { "SLG", 1.5}, // Lower is better
            //    { "OPS", 1}, // Lower is better
            //    { "PA/TB", 1.5},
            //    { "AB/GDP", 1},
            //    { "BAbip", .5}, // Lower is better
            //    { "tOPSPlus", 1},
            //    { "sOPSPlus", .5}
            //};


            //{ 'AB_R': 0.5, 'AB_H': 0.5, 'PA_HR': 1.5, 'AB_SB': 0.1, 'SB_SB_CS': 0.5, 'PA_BB': 1.5, 'AB_SO': 0.1, 'SOW': 1, 'BA': 0.5, 'OBP': 1, 'SLG': 0.5, 'OPS': 1, 'PA_TB': 0.5, 'AB_GDP': 0.5, 'BAbip': 0.5, 'tOPSPlus': 1.5, 'sOPSPlus': 0.5}

            //1st runs Best Weights: { 'AB_R': 0.5, 'AB_H': 0.5, 'PA_HR': 1.5, 'AB_SB': 0.01,
            //        'SB_SB_CS': 0, 'PA_BB': 0, 'AB_SO': 1, 'SOW': 0.5, 'BA': 0.5, 'OBP': 0,
            //        'SLG': 0.5, 'OPS': 0, 'PA_TB': 0.5, 'AB_GDP': 0.5, 'BAbip': 0.5, 'tOPSPlus': 0.5,
            //        'sOPSPlus': 0}
            //2nd Best Weights: { 'AB_R': 0.5, 'AB_H': 0.5, 'PA_HR': 1.5, 'AB_SB': 0.1,
            //'SB_SB_CS': 0.5, 'PA_BB': 1.5, 'AB_SO': 0.1, 'SOW': 1, 'BA': 0.5, 'OBP': 1,
            //'SLG': 0.5, 'OPS': 1, 'PA_TB': 0.5, 'AB_GDP': 0.5, 'BAbip': 0.5, 'tOPSPlus': 1.5, 'sOPSPlus': 0.5}

            // 8kish
            //3rd best Best Weights: { 'AB_R': 0.5, 'AB_H': 0.5, 'PA_HR': 1.5, 'AB_SB': 0,
            //'SB_SB_CS': 0.1, 'PA_BB': 1.5, 'AB_SO': 1, 'SOW': 0, 'BA': 0.5, 'OBP': 0.5,
            //'SLG': 1, 'OPS': 0.5, 'PA_TB': 1.5, 'AB_GDP': 1, 'BAbip': 0.5, 'tOPSPlus': 1, 'sOPSPlus': 0}

            //4th try  10kish
            //Best Weights: { 'AB_R': 0, 'AB_H': 1.5, 'PA_HR': 1.5, 'AB_SB': 0.01, 'SB_SB_CS': 0.1, 'PA_BB': 1,
            //'AB_SO': 0.1, 'SOW': 1, 'BA': 1, 'OBP': 1, 'SLG': 1.5, 'OPS': 1, 'PA_TB': 1.5, 'AB_GDP': 1,
            //'BAbip': 0.5, 'tOPSPlus': 1, 'sOPSPlus': 0.5}
            //Total Wins: 43, Total Losses: 15


            foreach (var stat in weights.Keys)
            {
                if (homeDerivedMetrics.ContainsKey(stat) && awayDerivedMetrics.ContainsKey(stat))
                {
                    double homeValue = homeDerivedMetrics[stat];
                    double awayValue = awayDerivedMetrics[stat];
                    double relativeAdvantage;

                    // Adjust calculation for stats where lower values are better
                    if (stat == "BA" || stat == "OBP" || stat == "SLG" || stat == "OPS" || stat == "BAbip" || stat == "SB/SB+CS" || stat == "AB/SO" || stat == "tOPSPlus" || stat == "sOPSPlus")
                    {
                        // Invert the calculation
                        relativeAdvantage = (awayValue - homeValue) / ((homeValue + awayValue) / 2) * 100;
                    }
                    else
                    {
                        // Standard calculation
                        relativeAdvantage = (homeValue - awayValue) / ((homeValue + awayValue) / 2) * 100;
                    }

                    // Apply weights to the relative advantage
                    double weightedAdvantage = relativeAdvantage * weights[stat];

                    // Log the details of the comparison
                    _logger.LogInformation($"Stat: {stat}, Home Value: {homeValue}, Away Value: {awayValue}, Relative Advantage: {relativeAdvantage}, Weighted Advantage: {weightedAdvantage}");

                    // Add to the comparison metrics
                    comparisonMetrics[stat] = weightedAdvantage;
                }
            }

            return comparisonMetrics;
        }



        // Determine which pitcher has the advantage based on the sum of the weighted comparison metrics
        public string DetermineAdvantage(Dictionary<string, double> comparisonMetrics, string homePitcherId, string awayPitcherId)
        {
            var totalAdvantage = comparisonMetrics.Values.Sum();

            if (totalAdvantage > 0)
            {
                return $"{homePitcherId} (Home) has the advantage by {totalAdvantage:0.00}";
            }
            else if (totalAdvantage < 0)
            {
                return $"{awayPitcherId} (Away) has the advantage by {Math.Abs(totalAdvantage):0.00}";
            }
            else
            {
                return "No clear advantage";
            }
        }

        //public async Task<List<Dictionary<string, object>>> CalculateStartingPitcherAdvantage(DateTime date)
        //{
        //    var gamePreviews = await _context.GamePreviews.Where(g => g.Date == date).ToListAsync();
        //    var results = new List<Dictionary<string, object>>();

        //    // Extract the year from the provided date
        //    int currentYear = date.Year;

        //    foreach (var game in gamePreviews)
        //    {
        //        var homePitcherId = game.HomePitcher;
        //        var awayPitcherId = game.AwayPitcher;

        //        // Retrieve the stats for each pitcher (default to current year)
        //        var homePitcherTotalStats = await GetTotalStatsForPitcher(homePitcherId, currentYear);
        //        var homePitcherLast28Stats = await GetLast28StatsForPitcher(homePitcherId, currentYear); // Always fetch for the current year

        //        var awayPitcherTotalStats = await GetTotalStatsForPitcher(awayPitcherId, currentYear);
        //        var awayPitcherLast28Stats = await GetLast28StatsForPitcher(awayPitcherId, currentYear); // Always fetch for the current year

        //        // Helper method to compare totals and last28 stats
        //        bool areStatsEqual(Dictionary<string, double> totals, Dictionary<string, double> last28)
        //        {
        //            var keysToCompare = new[] { "G", "PA", "AB" };
        //            return keysToCompare.All(key => totals.ContainsKey(key) && last28.ContainsKey(key) && totals[key] == last28[key]);
        //        }

        //        // Method to adjust weights based on 'G' in last28 stats
        //        (double totalWeight, double last28Weight) AdjustWeightsBasedOnLast28(Dictionary<string, double> last28Stats)
        //        {
        //            if(last28Stats != null) {
        //                if (last28Stats.ContainsKey("G") && last28Stats["G"] <= 2)
        //                {
        //                    return (0.8, 0.2); // Use more weight on totals if last28 stats are based on 2 games or fewer
        //                }
        //                return (0.6, 0.4); // Default weights

        //            }
        //            else
        //            {
        //                return (1, 0);
        //            }

        //        }

        //        // Check if 2023 stats should be used for home pitcher
        //        if (homePitcherLast28Stats != null && homePitcherTotalStats != null && areStatsEqual(homePitcherTotalStats, homePitcherLast28Stats))
        //        {
        //            var lastYearTotalStats = await GetTotalStatsForPitcher(homePitcherId, currentYear - 1);

        //            if (lastYearTotalStats != null && lastYearTotalStats.ContainsKey("PA") && lastYearTotalStats["PA"] > 100)
        //            {
        //                homePitcherTotalStats = lastYearTotalStats;
        //                (double totalWeight, double last28Weight) = (0.4, 0.6); // Adjust weights when using last year's totals
        //            }
        //        }

        //        // Check if 2023 stats should be used for away pitcher
        //        if (awayPitcherLast28Stats != null && awayPitcherTotalStats != null && areStatsEqual(awayPitcherTotalStats, awayPitcherLast28Stats))
        //        {
        //            var lastYearTotalStats = await GetTotalStatsForPitcher(awayPitcherId, currentYear - 1);

        //            if (lastYearTotalStats != null && lastYearTotalStats.ContainsKey("PA") && lastYearTotalStats["PA"] > 100)
        //            {
        //                awayPitcherTotalStats = lastYearTotalStats;
        //                (double totalWeight, double last28Weight) = (0.4, 0.6); // Adjust weights when using last year's totals
        //            }
        //        }

        //        // Adjust weights based on last28 stats 'G' for home pitcher
        //        var (homeTotalWeight, homeLast28Weight) = AdjustWeightsBasedOnLast28(homePitcherLast28Stats);

        //        // Adjust weights based on last28 stats 'G' for away pitcher
        //        var (awayTotalWeight, awayLast28Weight) = AdjustWeightsBasedOnLast28(awayPitcherLast28Stats);

        //        // Blend stats for home and away pitchers
        //        var (homeBlendedStats, homeWarnings) = BlendStats(homePitcherTotalStats, homePitcherLast28Stats, homePitcherId, homeTotalWeight, homeLast28Weight);
        //        var (awayBlendedStats, awayWarnings) = BlendStats(awayPitcherTotalStats, awayPitcherLast28Stats, awayPitcherId, awayTotalWeight, awayLast28Weight);

        //        // Initialize the result dictionary
        //        var result = new Dictionary<string, object>
        //{
        //    { "Game", $"{game.HomeTeam} vs {game.AwayTeam}" },
        //    { "HomePitcher", game.HomePitcher },
        //    { "AwayPitcher", game.AwayPitcher }
        //};

        //        // Add warnings if there are any
        //        if (homeWarnings.Any())
        //            result["HomeWarnings"] = string.Join("; ", homeWarnings);

        //        if (awayWarnings.Any())
        //            result["AwayWarnings"] = string.Join("; ", awayWarnings);

        //        // Proceed only if both blended stats are not null
        //        if (homeBlendedStats != null && awayBlendedStats != null)
        //        {
        //            // Calculate comparison metrics
        //            var comparisonMetrics = CalculateComparisonMetrics(homeBlendedStats, awayBlendedStats);

        //            // Determine which pitcher has the advantage
        //            var advantage = DetermineAdvantage(comparisonMetrics, homePitcherId, awayPitcherId);

        //            // Add comparison results to the result dictionary
        //            result["ComparisonMetrics"] = comparisonMetrics;
        //            result["Advantage"] = advantage;
        //        }
        //        else
        //        {
        //            // If one of the blended stats is null, add a specific note
        //            result["Advantage"] = "Not enough data to determine advantage";
        //        }

        //        results.Add(result);
        //    }

        //    return results;
        //}
        public async Task<List<Dictionary<string, object>>> CalculateStartingPitcherAdvantage(DateTime date)
        {
            var gamePreviews = await _context.GamePreviews.Where(g => g.Date == date).ToListAsync();
            var results = new List<Dictionary<string, object>>();

            // Extract the year from the provided date
            int currentYear = date.Year;

            foreach (var game in gamePreviews)
            {
                var homePitcherId = game.HomePitcher;
                var awayPitcherId = game.AwayPitcher;

                // Apply the blending logic for home and away pitchers
                var (homeBlendedStats, homeWarnings) = await BlendPitcherStatsAsync(homePitcherId, currentYear);
                var (awayBlendedStats, awayWarnings) = await BlendPitcherStatsAsync(awayPitcherId, currentYear);

                // Initialize the result dictionary
                var result = new Dictionary<string, object>
        {
            { "Game", $"{game.HomeTeam} vs {game.AwayTeam}" },
            { "HomePitcher", game.HomePitcher },
            { "AwayPitcher", game.AwayPitcher }
        };

                // Add warnings if there are any
                if (homeWarnings.Any())
                    result["HomeWarnings"] = string.Join("; ", homeWarnings);

                if (awayWarnings.Any())
                    result["AwayWarnings"] = string.Join("; ", awayWarnings);

                // Proceed only if both blended stats are not null
                if (homeBlendedStats != null && awayBlendedStats != null)
                {
                    // Calculate comparison metrics
                    var comparisonMetrics = CalculateComparisonMetrics(homeBlendedStats, awayBlendedStats);

                    // Determine which pitcher has the advantage
                    var advantage = DetermineAdvantage(comparisonMetrics, homePitcherId, awayPitcherId);

                    // Add comparison results to the result dictionary
                    result["ComparisonMetrics"] = comparisonMetrics;
                    result["Advantage"] = advantage;
                }
                else
                {
                    // If one of the blended stats is null, add a specific note
                    result["Advantage"] = "Not enough data to determine advantage";
                }

                results.Add(result);
            }

            return results;
        }


        public async Task<(Dictionary<string, double> BlendedStats, List<string> Warnings)> BlendPitcherStatsAsync(string pitcherId, int year)
        {
            var warnings = new List<string>();
            Dictionary<string, double> blendedStats = null;

            // Retrieve stats for the pitcher
            var totalStats = await GetTotalStatsForPitcher(pitcherId, year);
            var last28Stats = await GetLast28StatsForPitcher(pitcherId, year);
            var last14Stats = await _context.PitcherPlatoonAndTrackRecord
                                             .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "last14" && p.Year == year);
            var last7Stats = await _context.PitcherPlatoonAndTrackRecord
                                            .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Split == "last7" && p.Year == year);

            // Check for last 28 days stats
            if (last28Stats != null)
            {
                blendedStats = BlendStats(totalStats, last28Stats, pitcherId, 0.6, 0.4).BlendedStats;
                if (blendedStats == null)
                {
                    warnings.Add($"{pitcherId}: Unable to blend last 28-day stats. Using only total stats.");
                    blendedStats = totalStats;
                }
            }
            else if (last14Stats != null) // Check for last 14 days stats
            {
                warnings.Add($"{pitcherId}: No last 28-day stats available, using last 14-day stats.");
                blendedStats = BlendStats(totalStats, MapToDictionary(last14Stats), pitcherId, 0.75, 0.25).BlendedStats;
            }
            else if (last7Stats != null) // Check for last 7 days stats
            {
                warnings.Add($"{pitcherId}: No last 28-day or last 14-day stats available, using last 7-day stats.");
                blendedStats = BlendStats(totalStats, MapToDictionary(last7Stats), pitcherId, 0.9, 0.1).BlendedStats;
            }
            else if (totalStats != null) // Use only total stats
            {
                warnings.Add($"{pitcherId}: No recent stats available, using total stats only.");
                blendedStats = totalStats;
            }
            else // Check for last year's total stats
            {
                var lastYearStats = await GetTotalStatsForPitcher(pitcherId, year - 1);
                if (lastYearStats != null)
                {
                    warnings.Add($"{pitcherId}: No stats for the current year, using last year's total stats.");
                    blendedStats = lastYearStats;
                }
                else
                {
                    warnings.Add($"{pitcherId}: Not enough relevant stats to make a comparison.");
                }
            }

            return (blendedStats, warnings);        


        }

        // Helper method to map a PitcherPlatoonAndTrackRecord to a dictionary of stats
        private Dictionary<string, double> MapToDictionary(PitcherPlatoonAndTrackRecord stats)
        {
            return new Dictionary<string, double>
    {
        { "G", stats.G },
        { "PA", stats.PA },
        { "AB", stats.AB },
        { "R", stats.R },
        { "H", stats.H },
        { "HR", stats.HR },
        { "SB", stats.SB },
        { "CS", stats.CS },
        { "BB", stats.BB },
        { "SO", stats.SO },
        { "SOW", stats.SOW },
        { "BA", stats.BA },
        { "OBP", stats.OBP },
        { "SLG", stats.SLG },
        { "OPS", stats.OPS },
        { "TB", stats.TB },
        { "GDP", stats.GDP },
        { "BAbip", stats.BAbip },
        { "tOPSPlus", stats.tOPSPlus },
        { "sOPSPlus", stats.sOPSPlus }
    };
        }





        private async Task<Dictionary<string, double>> GetBlendedStatsForPitcher(string pitcherId)
        {
            // Retrieve the pitcher's splits
            var splits = await _context.PitcherPlatoonAndTrackRecord
                                       .Where(p => p.BbrefID == pitcherId)
                                       .ToListAsync();

            if (splits == null || !splits.Any())
            {
                _logger.LogWarning($"No splits found for pitcher {pitcherId}");
                return null;
            }

            var blendedStats = BlendRecentAndSeasonPerformance(splits);

            if (blendedStats == null)
            {
                _logger.LogWarning($"Blended stats not generated for pitcher {pitcherId}");
                return null;
            }
            // Expand the blended stats to include additional metrics as needed
            var expandedBlendedStats = new Dictionary<string, double>
    {
        { "BA", blendedStats.BA },
        { "OBP", blendedStats.OBP },
        { "SLG", blendedStats.SLG },
        { "OPS", blendedStats.OPS },
        { "BAbip", blendedStats.BAbip }
        // Add more metrics as needed
    };

            return expandedBlendedStats;
        }

        private Dictionary<string, object> CompareBlendedStats(Dictionary<string, double> homePitcherStats, Dictionary<string, double> awayPitcherStats)
        {
            var homeDerivedMetrics = CalculateDerivedMetrics(homePitcherStats);
            var awayDerivedMetrics = CalculateDerivedMetrics(awayPitcherStats);

            var comparisonMetrics = new Dictionary<string, object>();

            // Handle sample size warnings
            AddSampleSizeWarnings(homePitcherStats, "Home", comparisonMetrics);
            AddSampleSizeWarnings(awayPitcherStats, "Away", comparisonMetrics);

            foreach (var stat in homeDerivedMetrics.Keys)
            {
                if (awayDerivedMetrics.ContainsKey(stat))
                {
                    double homeValue = homeDerivedMetrics[stat];
                    double awayValue = awayDerivedMetrics[stat];

                    double comparisonValue;

                    // Metrics where higher is better
                    if (stat == "AB/R" || stat == "AB/H" || stat == "AB/SB" || stat == "PA/BB" || stat == "SOW" || stat == "PA/TB")
                    {
                        comparisonValue = (homeValue - awayValue) / ((homeValue + awayValue) / 2);
                    }
                    // Metrics where lower is better
                    else if (stat == "SB/SB+CS" || stat == "AB/SO" || stat == "BA" || stat == "OBP" || stat == "SLG" || stat == "OPS" || stat == "AB/GDP" || stat == "BAbip" || stat == "tOPSPlus" || stat == "sOPSPlus")
                    {
                        comparisonValue = (awayValue - homeValue) / ((homeValue + awayValue) / 2);
                    }
                    else
                    {
                        // Default behavior if stat is not specifically handled
                        comparisonValue = (homeValue - awayValue) / ((homeValue + awayValue) / 2);
                    }

                    comparisonMetrics[stat] = comparisonValue;
                }
            }

            return comparisonMetrics;
        }


        public async Task<Dictionary<string, object>> Compare2SP(string pitcheraId, string pitcherbId)
        {
            // Step 1: Get total stats for pitcher A for 2024, fallback to 2023 if not significant
            var pitcheraStats2024 = await GetTotalStatsForPitcher(pitcheraId, 2024);
            var pitcheraStats2023 = await GetTotalStatsForPitcher(pitcheraId, 2023);

            var pitcheraStats = pitcheraStats2024 != null && pitcheraStats2024.Count > 0 ?
                                pitcheraStats2024 :
                                (pitcheraStats2023 != null && pitcheraStats2023.Count > 0 ? pitcheraStats2023 : null);

            // Step 2: Get total stats for pitcher B for 2024, fallback to 2023 if not significant
            var pitcherbStats2024 = await GetTotalStatsForPitcher(pitcherbId, 2024);
            var pitcherbStats2023 = await GetTotalStatsForPitcher(pitcherbId, 2023);

            var pitcherbStats = pitcherbStats2024 != null && pitcherbStats2024.Count > 0 ?
                                pitcherbStats2024 :
                                (pitcherbStats2023 != null && pitcherbStats2023.Count > 0 ? pitcherbStats2023 : null);

            // Step 3: Ensure that both pitchers have relevant stats
            if (pitcheraStats == null || pitcherbStats == null)
            {
                //_logger.LogWarning($"No relevant stats found for {pitcheraId} or {pitcherbId}.");
                return new Dictionary<string, object>
                {
                    { "message", "One or both pitchers have no relevant stats." }
                };
            }

            // Step 4: Calculate comparison metrics for both pitchers
            var comparisonMetrics = CalculateComparisonMetrics(pitcheraStats, pitcherbStats);

            // Step 5: Determine which pitcher has the advantage
            var advantage = DetermineAdvantage(comparisonMetrics, pitcheraId, pitcherbId);

            // Step 6: Return the comparison results
            return new Dictionary<string, object>
            {
                { "PitcherA", pitcheraId },
                { "PitcherB", pitcherbId },
                { "ComparisonMetrics", comparisonMetrics },
                { "Advantage", advantage }
            };
        }


        private Dictionary<string, double> CalculateDerivedMetrics(Dictionary<string, double> stats)
        {
            var derivedMetrics = new Dictionary<string, double>();

            double SafeDivision(double numerator, double denominator)
            {
                if (denominator == 0 || double.IsNaN(numerator) || double.IsInfinity(numerator) || double.IsNaN(denominator) || double.IsInfinity(denominator))
                {
                    return 0;  // Avoid division by zero, NaN, or infinity
                }
                return numerator / denominator;
            }

            // Calculating derived metrics safely
            derivedMetrics["AB/R"] = SafeDivision(stats.GetValueOrDefault("AB"), stats.GetValueOrDefault("R"));
            derivedMetrics["AB/H"] = SafeDivision(stats.GetValueOrDefault("AB"), stats.GetValueOrDefault("H"));
            derivedMetrics["PA/HR"] = SafeDivision(stats.GetValueOrDefault("PA"), stats.GetValueOrDefault("HR"));
            derivedMetrics["AB/SB"] = SafeDivision(stats.GetValueOrDefault("AB"), stats.GetValueOrDefault("SB"));
            derivedMetrics["SB/SB+CS"] = SafeDivision(stats.GetValueOrDefault("SB"), stats.GetValueOrDefault("SB") + stats.GetValueOrDefault("CS"));
            derivedMetrics["PA/BB"] = SafeDivision(stats.GetValueOrDefault("PA"), stats.GetValueOrDefault("BB"));
            derivedMetrics["AB/SO"] = SafeDivision(stats.GetValueOrDefault("AB"), stats.GetValueOrDefault("SO"));
            derivedMetrics["SOW"] = stats.GetValueOrDefault("SOW");
            derivedMetrics["BA"] = stats.GetValueOrDefault("BA");
            derivedMetrics["OBP"] = stats.GetValueOrDefault("OBP");
            derivedMetrics["SLG"] = stats.GetValueOrDefault("SLG");
            derivedMetrics["OPS"] = stats.GetValueOrDefault("OPS");
            derivedMetrics["PA/TB"] = SafeDivision(stats.GetValueOrDefault("PA"), stats.GetValueOrDefault("TB"));
            derivedMetrics["AB/GDP"] = SafeDivision(stats.GetValueOrDefault("AB"), stats.GetValueOrDefault("GDP"));
            derivedMetrics["BAbip"] = stats.GetValueOrDefault("BAbip");
            derivedMetrics["tOPSPlus"] = stats.GetValueOrDefault("tOPSPlus");
            derivedMetrics["sOPSPlus"] = stats.GetValueOrDefault("sOPSPlus");

            // Filter out NaN or infinity values from the result
            foreach (var key in derivedMetrics.Keys.ToList())
            {
                if (double.IsNaN(derivedMetrics[key]) || double.IsInfinity(derivedMetrics[key]))
                {
                    derivedMetrics[key] = 0;
                }
            }

            return derivedMetrics;
        }




        public async Task<Dictionary<string, object>> Compare2SPCustom(string pitcheraId, string pitcherbId, Dictionary<string, double> customWeights)
        {
            // Step 1: Get total stats for pitcher A for 2024
            var pitcheraStats = await GetTotalStatsForPitcher(pitcheraId, 2024);

            // Query 2023 stats only if 'G' (Games) is less than 5 or stats are missing
            if (pitcheraStats == null || !pitcheraStats.ContainsKey("G") || pitcheraStats["G"] < 2)
            {
                pitcheraStats = await GetTotalStatsForPitcher(pitcheraId, 2023);
            }

            // Step 2: Get total stats for pitcher B for 2024
            var pitcherbStats = await GetTotalStatsForPitcher(pitcherbId, 2024);

            // Query 2023 stats only if 'G' (Games) is less than 5 or stats are missing
            if (pitcherbStats == null || !pitcherbStats.ContainsKey("G") || pitcherbStats["G"] < 2)
            {
                pitcherbStats = await GetTotalStatsForPitcher(pitcherbId, 2023);
            }

            // Step 3: Ensure that both pitchers have relevant stats
            if (pitcheraStats == null || pitcherbStats == null || !pitcheraStats.ContainsKey("G") || pitcheraStats["G"] < 2 || !pitcherbStats.ContainsKey("G") || pitcherbStats["G"] < 2)
            {
                //_logger.LogWarning($"No relevant stats found for {pitcheraId} or {pitcherbId}.");
                return new Dictionary<string, object>
        {
            { "message", "One or both pitchers have no relevant stats." }
        };
            }

            // Step 4: Calculate comparison metrics for both pitchers using custom weights
            var comparisonMetrics = CalculateComparisonMetrics(pitcheraStats, pitcherbStats, customWeights);

            // Step 5: Determine which pitcher has the advantage
            var advantage = DetermineAdvantage(comparisonMetrics, pitcheraId, pitcherbId);

            // Step 6: Return the comparison results
            return new Dictionary<string, object>
    {
        { "PitcherA", pitcheraId },
        { "PitcherB", pitcherbId },
        { "ComparisonMetrics", comparisonMetrics },
        { "Advantage", advantage }
    };
        }


        private Dictionary<string, double> CalculateComparisonMetrics(Dictionary<string, double> homeStats, Dictionary<string, double> awayStats, Dictionary<string, double> customWeights)
        {
            var homeDerivedMetrics = CalculateDerivedMetrics(homeStats);
            var awayDerivedMetrics = CalculateDerivedMetrics(awayStats);

            var comparisonMetrics = new Dictionary<string, double>();

            double SafeComparison(double homeValue, double awayValue, string stat)
            {
                // Check if either value is zero
                if (homeValue == 0 && awayValue == 0)
                {
                    return 0;  // If both values are zero, there's no difference
                }
                else if (homeValue == 0)
                {
                    return -100;  // Home pitcher is "100% worse" relative to the away pitcher
                }
                else if (awayValue == 0)
                {
                    return 100;  // Away pitcher is "100% worse" relative to the home pitcher
                }

                // Perform the relative advantage calculation
                if (stat == "BA" || stat == "OBP" || stat == "SLG" || stat == "OPS" || stat == "BAbip" || stat == "SB/SB+CS" || stat == "AB/SO" || stat == "tOPSPlus" || stat == "sOPSPlus")
                {
                    // For stats where lower values are better, invert the calculation
                    return (awayValue - homeValue) / ((homeValue + awayValue) / 2) * 100;
                }
                else
                {
                    // For stats where higher values are better
                    return (homeValue - awayValue) / ((homeValue + awayValue) / 2) * 100;
                }
            }

            foreach (var stat in customWeights.Keys)
            {
                if (homeDerivedMetrics.ContainsKey(stat) && awayDerivedMetrics.ContainsKey(stat))
                {
                    double homeValue = homeDerivedMetrics[stat];
                    double awayValue = awayDerivedMetrics[stat];

                    // Use the SafeComparison function to ensure no divide-by-zero or infinity values
                    double relativeAdvantage = SafeComparison(homeValue, awayValue, stat);

                    // Apply custom weights to the relative advantage
                    double weightedAdvantage = relativeAdvantage * customWeights[stat];

                    // Add to the comparison metrics
                    comparisonMetrics[stat] = weightedAdvantage;
                }
            }

            return comparisonMetrics;
        }


        public async Task<List<PitcherRanking>> GetDailyPitcherRankings(DateTime date)
        {
            var rankings = new List<PitcherRanking>();
            var gamePreviews = await _context.GamePreviews
                                           .Where(g => g.Date.Date == date.Date)
                                           .ToListAsync();

            if (!gamePreviews.Any())
            {
                _logger.LogWarning($"No games found for date {date}");
                return rankings;
            }

            // Get all unique pitchers for the day
            var allPitchers = gamePreviews.SelectMany(g => new[] {
        new { Id = g.HomePitcher, Team = g.HomeTeam, IsHome = true },
        new { Id = g.AwayPitcher, Team = g.AwayTeam, IsHome = false }
    }).Where(p => !string.IsNullOrEmpty(p.Id)).ToList();

            // Get blended stats and trends for all pitchers
            foreach (var pitcher in allPitchers)
            {
                // Get blended stats
                var (blendedStats, warnings) = await BlendPitcherStatsAsync(pitcher.Id, date.Year);

                // Get trend analysis
                var trends = await GetBlendingResultsForPitcher(pitcher.Id);
                var trendAnalysis = trends != null ? AnalyzeTrends(pitcher.Id, trends) : null;

                if (blendedStats != null)
                {
                    // Calculate a composite score
                    double compositeScore = CalculateCompositeScore(blendedStats, trendAnalysis);

                    rankings.Add(new PitcherRanking
                    {
                        PitcherId = pitcher.Id,
                        Team = pitcher.Team,
                        IsHome = pitcher.IsHome,
                        BlendedStats = blendedStats,
                        TrendAnalysis = trendAnalysis,
                        CompositeScore = compositeScore,
                        Warnings = warnings
                    });
                }
            }

            // Sort rankings by composite score (higher is better)
            return rankings.OrderByDescending(r => r.CompositeScore).ToList();
        }

        private double CalculateCompositeScore(Dictionary<string, double> blendedStats, Dictionary<string, object> trendAnalysis)
        {
            if (blendedStats == null) return 0;

            double score = 0;

            // Get sample size weight (maxes out at 1.0 after 10 games)
            double gamesPlayed = blendedStats.GetValueOrDefault("G", 0);
            double sampleSizeWeight = Math.Min(gamesPlayed / 10.0, 1.0);

            // Calculate rate stats properly
            var rateStats = new Dictionary<string, double>
    {
        { "K_Rate", blendedStats.GetValueOrDefault("SO", 0) / blendedStats.GetValueOrDefault("PA", 1) },
        { "BB_Rate", blendedStats.GetValueOrDefault("BB", 0) / blendedStats.GetValueOrDefault("PA", 1) },
        { "HR_Rate", blendedStats.GetValueOrDefault("HR", 0) / blendedStats.GetValueOrDefault("PA", 1) },
        { "BA", blendedStats.GetValueOrDefault("BA", 0) },
        { "OBP", blendedStats.GetValueOrDefault("OBP", 0) },
        { "SLG", blendedStats.GetValueOrDefault("SLG", 0) },
        { "tOPSPlus", blendedStats.GetValueOrDefault("tOPSPlus", 100) },
        { "sOPSPlus", blendedStats.GetValueOrDefault("sOPSPlus", 100) }
    };

            // League averages/baseline for rate stats
            var leagueAverages = new Dictionary<string, double>
    {
        { "K_Rate", 0.223 },  // 22.3% K-rate
        { "BB_Rate", 0.084 }, // 8.4% BB-rate
        { "HR_Rate", 0.032 }, // 3.2% HR-rate
        { "BA", 0.248 },
        { "OBP", 0.318 },
        { "SLG", 0.411 },
        { "tOPSPlus", 100 },  // 100 is baseline for OPS+ stats
        { "sOPSPlus", 100 }   // 100 is baseline for OPS+ stats
    };

            // Calculate weighted score for each component
            foreach (var stat in rateStats.Keys)
            {
                double value = rateStats[stat];
                double leagueAvg = leagueAverages[stat];

                // Calculate percentage difference from league average
                double percentDiff = (value - leagueAvg) / leagueAvg;

                // Invert for stats where lower is better (which now includes tOPSPlus and sOPSPlus for pitchers)
                if (stat is "BA" or "OBP" or "SLG" or "BB_Rate" or "HR_Rate" or "tOPSPlus" or "sOPSPlus")
                {
                    percentDiff *= -1;
                }

                // Weight OPS+ stats more heavily since they're already normalized
                double statWeight = 1.0;
                if (stat is "tOPSPlus" or "sOPSPlus")
                {
                    statWeight = 1.5;
                }

                // Apply sample size weight and stat weight
                percentDiff *= sampleSizeWeight * statWeight;

                score += percentDiff;
            }

            // Rest of the code remains the same...
            // Apply trend modifier (weighted by sample size)
            if (trendAnalysis != null)
            {
                var trends = new[] {
            Convert.ToDouble(trendAnalysis["bA_Trend"]),
            Convert.ToDouble(trendAnalysis["obP_Trend"]),
            Convert.ToDouble(trendAnalysis["slG_Trend"]),
            Convert.ToDouble(trendAnalysis["BAbip_Trend"])
        };

                double trendScore = trends.Average() * -1; // Negative because lower is better for pitchers
                score += (trendScore * sampleSizeWeight * 0.3); // Trend counts for 30% of final score
            }

            return score;
        
    }

        public async Task<List<PitcherRanking>> GetEnhancedDailyPitcherRankings(DateTime date)
        {
            // Get base rankings first and create deep copies
            var baseRankings = await GetDailyPitcherRankings(date);
            var enhancedRankings = baseRankings.Select(r => new PitcherRanking
            {
                PitcherId = r.PitcherId,
                Team = r.Team,
                IsHome = r.IsHome,
                BlendedStats = new Dictionary<string, double>(r.BlendedStats),
                TrendAnalysis = r.TrendAnalysis != null ?
                    new Dictionary<string, object>(r.TrendAnalysis) : null,
                CompositeScore = r.CompositeScore,
                Warnings = new List<string>(r.Warnings ?? new List<string>())
            }).ToList();

            foreach (var ranking in enhancedRankings)
            {
                var warnings = new List<string>();

                var lineup = await GetLineupForGame(date, ranking.PitcherId, ranking.IsHome);
                var (lineupStrengthValue, lineupWarnings) = await CalculateLineupStrength(lineup, date);
                warnings.AddRange(lineupWarnings);

                var (parkFactorValue, parkWarnings) = await GetParkAndWeatherEffects(date, ranking.Team, ranking.IsHome);
                warnings.AddRange(parkWarnings);

                ranking.CompositeScore = AdjustScoreForMatchup(
                    ranking.CompositeScore,
                    lineupStrengthValue,
                    parkFactorValue,
                    ranking.IsHome,
                    warnings
                );

                ranking.Warnings = warnings;
            }

            return enhancedRankings.OrderByDescending(r => r.CompositeScore).ToList();
        }


        public async Task<List<string>> GetLineupForGame(DateTime date, string pitcherId, bool isHome)
        {
            var gamePreview = await _context.GamePreviews
                .FirstOrDefaultAsync(g => g.Date.Date == date.Date &&
                    (isHome ? g.HomePitcher == pitcherId : g.AwayPitcher == pitcherId));

            if (gamePreview == null)
            {
                return new List<string>();
            }

            // For a home pitcher, we want the away team's lineup (opponent)
            // For an away pitcher, we want the home team's lineup (opponent)
            string teamToFind = isHome ? gamePreview.AwayTeam : gamePreview.HomeTeam;
            string opponentToFind = isHome ? gamePreview.HomeTeam : gamePreview.AwayTeam;

            // First try to get actual lineup
            var actualLineup = await _context.ActualLineups
                .FirstOrDefaultAsync(l => l.Date.Date == date.Date &&
                                         l.Team == teamToFind &&
                                         l.Opponent == opponentToFind &&
                                         l.OpposingSP == pitcherId);

            if (actualLineup != null)
            {
                return new List<string>
        {
            actualLineup.Batting1st,
            actualLineup.Batting2nd,
            actualLineup.Batting3rd,
            actualLineup.Batting4th,
            actualLineup.Batting5th,
            actualLineup.Batting6th,
            actualLineup.Batting7th,
            actualLineup.Batting8th,
            actualLineup.Batting9th
        };
            }

            // Fallback to predicted lineup
            var predictedLineup = await _context.LineupPredictions
                .FirstOrDefaultAsync(l => l.Date.Date == date.Date &&
                                         l.Team == teamToFind &&
                                         l.Opponent == opponentToFind &&
                                         l.OpposingSP == pitcherId);

            if (predictedLineup != null)
            {
                return new List<string>
        {
            predictedLineup.Batting1st,
            predictedLineup.Batting2nd,
            predictedLineup.Batting3rd,
            predictedLineup.Batting4th,
            predictedLineup.Batting5th,
            predictedLineup.Batting6th,
            predictedLineup.Batting7th,
            predictedLineup.Batting8th,
            predictedLineup.Batting9th
        };
            }

            return new List<string>();
        }


        public async Task<(double Strength, List<string> Warnings)> CalculateLineupStrength(List<string> lineup, DateTime date)
        {
            double strength = 0;
            var warnings = new List<string>();

            if (!lineup.Any())
            {
                warnings.Add("No lineup data available");
                return (0, warnings);
            }

            // Calculate season and recent stats for each batter
            var totalOPS = 0.0;
            var recentOPS = 0.0;
            var batterCount = 0;

            foreach (var batterId in lineup)
            {
                // Get season stats
                var seasonStats = await _context.TrailingGameLogSplits
                    .Where(t => t.BbrefId == batterId && t.Split == "Season")
                    .OrderByDescending(t => t.DateUpdated)
                    .FirstOrDefaultAsync();

                // Get last 7 games stats
                var recentStats = await _context.TrailingGameLogSplits
                    .Where(t => t.BbrefId == batterId && t.Split == "Last7G")
                    .OrderByDescending(t => t.DateUpdated)
                    .FirstOrDefaultAsync();

                if (seasonStats != null)
                {
                    batterCount++;
                    totalOPS += seasonStats.OPS;

                    if (recentStats != null)
                    {
                        // Weight recent performance more heavily
                        recentOPS += recentStats.OPS;
                    }
                    else
                    {
                        recentOPS += seasonStats.OPS; // Use season stats if no recent stats
                        warnings.Add($"No recent stats for {batterId}");
                    }
                }
            }

            if (batterCount == 0)
            {
                warnings.Add("No valid batter statistics found");
                return (0, warnings);
            }

            // Blend season and recent performance (60/40 weight)
            var avgSeasonOPS = totalOPS / batterCount;
            var avgRecentOPS = recentOPS / batterCount;
            strength = (avgSeasonOPS * 0.6) + (avgRecentOPS * 0.4);

            return (strength, warnings);
        }

        private async Task<(double ParkFactor, List<string> Warnings)> GetParkAndWeatherEffects(DateTime date, string teamName, bool isHome)
        {
            var warnings = new List<string>();
            // Start with neutral park factor
            double parkEffect = 100.0; // Start at neutral

            var gamePreview = await _context.GamePreviews
                .FirstOrDefaultAsync(g => g.Date.Date == date.Date &&
                    (isHome ? g.HomeTeam == teamName : g.AwayTeam == teamName));

            if (gamePreview == null)
            {
                warnings.Add($"No game preview found for {teamName} on {date:yyyy-MM-dd}");
                return (parkEffect, warnings);
            }

            var parkFactors = await _context.ParkFactors
                .Where(p => p.Venue.ToLower() == gamePreview.Venue.ToLower())
                .FirstOrDefaultAsync();

            if (parkFactors == null)
            {
                warnings.Add($"No park factors found for {gamePreview.Venue}");
                return (parkEffect, warnings);
            }

            // Use ParkFactorRating directly - it's already normalized to 100
            parkEffect = parkFactors.ParkFactorRating;

            // Only apply weather adjustments for open-air parks
            if (parkFactors.RoofType == "Open Air")
            {
                // Temperature effects
                if (gamePreview.Temperature >= 85)
                {
                    parkEffect += 5; // Make park 5% more hitter friendly
                    warnings.Add($"Hot weather adjustment applied: {gamePreview.Temperature}°F");
                }
                else if (gamePreview.Temperature <= 50)
                {
                    parkEffect -= 5; // Make park 5% more pitcher friendly
                    warnings.Add($"Cold weather adjustment applied: {gamePreview.Temperature}°F");
                }

                // Wind effects
                if (gamePreview.WindSpeed >= 10)
                {
                    double relativeWindDirection = gamePreview.RelativeWindDirection;
                    if (Math.Abs(relativeWindDirection) <= 45)
                    {
                        parkEffect += gamePreview.WindSpeed * 0.3; // Slight increase for wind out
                        warnings.Add($"Wind blowing out adjustment: {gamePreview.WindSpeed} mph");
                    }
                    else if (Math.Abs(relativeWindDirection) >= 135)
                    {
                        parkEffect -= gamePreview.WindSpeed * 0.3; // Slight decrease for wind in
                        warnings.Add($"Wind blowing in adjustment: {gamePreview.WindSpeed} mph");
                    }
                }
            }

            return (parkEffect, warnings);
        }


        private double AdjustScoreForMatchup(
            double baseScore,
            double lineupStrength,
            double parkFactor,
            bool isHome,
            List<string> warnings)
        {
            double adjustedScore = baseScore;

            // Apply lineup strength adjustment
            double leagueAverageOPS = 0.720;
            double lineupAdjustment = (leagueAverageOPS - lineupStrength) / leagueAverageOPS;
            double lineupMultiplier = 1 + (lineupAdjustment * 0.4);
            adjustedScore *= lineupMultiplier;

            // Always show lineup adjustment if it's not zero
            double lineupPercentChange = (lineupMultiplier - 1) * 100;
            if (Math.Abs(lineupPercentChange) > 0.1) // Show if more than 0.1%
            {
                warnings.Add($"Lineup adjustment: {lineupPercentChange:F1}% " +
                    $"({(lineupPercentChange > 0 ? "favorable" : "unfavorable")} matchup)");
            }

            // Apply park factor
            double parkAdjustment = (100 - parkFactor) / 100.0;
            adjustedScore *= (1 + parkAdjustment);

            // Always show park adjustment if it's not zero
            double parkPercentChange = parkAdjustment * 100;
            if (Math.Abs(parkPercentChange) > 0.1) // Show if more than 0.1%
            {
                warnings.Add($"Park factor adjustment: {parkPercentChange:F1}% " +
                    $"({(parkPercentChange > 0 ? "favorable" : "unfavorable")} conditions)");
            }

            // Apply and show home/away adjustment
            double homeAwayAdjustment = isHome ? 5.0 : -5.0; // Make it explicit
            adjustedScore *= (1 + (homeAwayAdjustment / 100.0));
            warnings.Add($"Home/Away adjustment: {homeAwayAdjustment:F1}% " +
                $"({(isHome ? "favorable" : "unfavorable")} conditions)");

            // Log final adjustment
            double totalChange = ((adjustedScore / baseScore) - 1) * 100;
            warnings.Add($"Total adjustment: {totalChange:F1}% from base score of {baseScore:F3}");

            return adjustedScore;
        }

        public class PitcherRanking
        {
            public string PitcherId { get; set; }
            public string Team { get; set; }
            public bool IsHome { get; set; }
            public Dictionary<string, double> BlendedStats { get; set; }
            public Dictionary<string, object> TrendAnalysis { get; set; }
            public double CompositeScore { get; set; }
            public List<string> Warnings { get; set; } = new List<string>();
        }

        public class WobaCalculator
        {
            // These weights can be adjusted based on the season
            private static class WobaWeights
            {
                public const double BB = 0.55;
                public const double HBP = 0.57;
                public const double SINGLE = 0.7;
                public const double DOUBLE = 1.00;
                public const double TRIPLE = 1.27;
                public const double HR = 1.65;
            }

            public static double CalculateWoba(TrailingGameLogSplit stats)
            {
                // Calculate singles from total hits minus extra base hits
                int singles = stats.H - (stats.HR + stats.Doubles + stats.Triples);

                // Calculate the numerator (weighted events)
                double weightedEvents =
                    (stats.BB * WobaWeights.BB) +
                    (stats.HBP * WobaWeights.HBP) +
                    (singles * WobaWeights.SINGLE) +
                    (stats.Doubles * WobaWeights.DOUBLE) +
                    (stats.Triples * WobaWeights.TRIPLE) +
                    (stats.HR * WobaWeights.HR);

                // Calculate the denominator (plate appearances)
                // Note: IBB is included in BB, SF needs to be added separately
                //int plateAppearances = stats.PA;
                int AdjPlateApps = stats.AB + stats.BB - stats.IBB + stats.SF + stats.HBP;

                // Guard against division by zero
                if (AdjPlateApps == 0)
                    return 0.0;

                return weightedEvents / AdjPlateApps;
            }
        }


    }
}

































// example how to use in other services
//public async Task SomeMethod()
//{
//    var models = new List<Pitcher>
//    {
//        model1, // Some Pitcher instance
//        model2, // Another Pitcher instance
//    };

//    var weights = new List<double> { 0.6, 0.4 }; // Corresponding weights

//    var blendedModel = _blendingService.BlendModels(models, weights);

//    // Use the blendedModel in your logic

//    // Optionally, save the blendedModel
//    await _blendingService.SaveBlendedModelAsync(blendedModel, "BlendedPitcherModels");
//}
