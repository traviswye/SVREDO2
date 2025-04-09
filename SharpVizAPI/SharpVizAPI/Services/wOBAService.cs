using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using SharpVizAPI.Data;
using SharpVizAPI.Models;

namespace SharpVizAPI.Services
{
    public class wOBAService
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<wOBAService> _logger;

        public wOBAService(NrfidbContext context, ILogger<wOBAService> logger)
        {
            _context = context;
            _logger = logger;
        }

        // Dictionary of year-specific wOBA constants
        private static readonly Dictionary<int, WobaConstants> YearlyWobaConstants = new Dictionary<int, WobaConstants>
        {
            {
                2023, new WobaConstants
                {
                    LeagueAverage = 0.318,
                    WobaScale = 1.204,
                    BB = 0.696,
                    HBP = 0.726,
                    Single = 0.883,
                    Double = 1.244,
                    Triple = 1.569,
                    HR = 2.004
                }
            },
            {
                2024, new WobaConstants
                {
                    LeagueAverage = 0.310,
                    WobaScale = 1.242,
                    BB = 0.689,
                    HBP = 0.720,
                    Single = 0.882,
                    Double = 1.254,
                    Triple = 1.590,
                    HR = 2.050
                }
            },
            {
                2025, new WobaConstants
                {
                    LeagueAverage = 0.311,
                    WobaScale = 1.267,
                    BB = 0.696,
                    HBP = 0.728,
                    Single = 0.893,
                    Double = 1.273,
                    Triple = 1.615,
                    HR = 2.085
                }
            }
        };

        // Class to hold wOBA constants for a specific year
        private class WobaConstants
        {
            public double LeagueAverage { get; set; }
            public double WobaScale { get; set; }
            public double BB { get; set; }
            public double HBP { get; set; }
            public double Single { get; set; }
            public double Double { get; set; }
            public double Triple { get; set; }
            public double HR { get; set; }
        }

        // Get the wOBA constants for a specific year
        private WobaConstants GetWobaConstants(int year)
        {
            if (YearlyWobaConstants.TryGetValue(year, out var constants))
            {
                return constants;
            }

            // If we don't have constants for the requested year, use the most recent year's constants
            _logger.LogWarning($"No wOBA constants found for year {year}. Using the most recent year's constants.");
            return YearlyWobaConstants.OrderByDescending(kvp => kvp.Key).First().Value;
        }

        // Method to calculate wOBA for a TrailingGameLogSplit using year-specific weights
        public double CalculateWoba(TrailingGameLogSplit stats, int year)
        {
            if (stats == null)
            {
                _logger.LogWarning("Cannot calculate wOBA: stats is null");
                return 0.0;
            }

            // Get year-specific wOBA constants
            var constants = GetWobaConstants(year);

            // Calculate singles from total hits minus extra base hits
            int singles = stats.H - (stats.HR + stats.Doubles + stats.Triples);

            // Calculate the numerator (weighted events)
            double weightedEvents =
                (stats.BB * constants.BB) +
                (stats.HBP * constants.HBP) +
                (singles * constants.Single) +
                (stats.Doubles * constants.Double) +
                (stats.Triples * constants.Triple) +
                (stats.HR * constants.HR);

            // Calculate the denominator (plate appearances excluding IBB)
            int adjustedPA = stats.AB + stats.BB - stats.IBB + stats.SF + stats.HBP;

            // Guard against division by zero
            if (adjustedPA == 0)
                return 0.0;

            return weightedEvents / adjustedPA;
        }

        // Overload method that uses the year from the stats object
        public double CalculateWoba(TrailingGameLogSplit stats)
        {
            return CalculateWoba(stats, stats.Year);
        }

        // Method to get wOBA for a player for both season and last 7 days
        public async Task<Dictionary<string, object>> GetPlayerWobaAsync(string bbrefId, int year)
        {
            _logger.LogInformation($"Getting wOBA for player {bbrefId} for year {year}");

            // Get season totals
            var seasonStats = await _context.TrailingGameLogSplits
                .Where(t => t.BbrefId == bbrefId && t.Split == "Season" && t.Year == year)
                .OrderByDescending(t => t.DateUpdated)
                .FirstOrDefaultAsync();

            // Get last 7 games stats
            var last7Stats = await _context.TrailingGameLogSplits
                .Where(t => t.BbrefId == bbrefId && t.Split == "Last7G" && t.Year == year)
                .OrderByDescending(t => t.DateUpdated)
                .FirstOrDefaultAsync();

            if (seasonStats == null)
            {
                _logger.LogWarning($"No season stats found for player {bbrefId} in year {year}");
                return new Dictionary<string, object>
                {
                    ["bbrefId"] = bbrefId,
                    ["year"] = year,
                    ["error"] = "No season stats found"
                };
            }

            // Get wOBA constants for specified year
            var wobaConstants = GetWobaConstants(year);

            // Calculate wOBA for season stats
            double seasonWoba = CalculateWoba(seasonStats, year);

            // Calculate wOBA for last 7 games if available
            double? last7Woba = last7Stats != null ? CalculateWoba(last7Stats, year) : null;

            // Calculate blended wOBA if we have both season and recent stats (70/30 weight)
            double blendedWoba = last7Woba.HasValue
                ? (seasonWoba * 0.7) + (last7Woba.Value * 0.3)
                : seasonWoba;

            return new Dictionary<string, object>
            {
                ["bbrefId"] = bbrefId,
                ["year"] = year,
                ["seasonWoba"] = seasonWoba,
                ["last7Woba"] = last7Woba,
                ["blendedWoba"] = blendedWoba,
                ["wobaConstants"] = new
                {
                    LeagueAverage = wobaConstants.LeagueAverage,
                    Scale = wobaConstants.WobaScale,
                    Year = year
                },
                ["seasonStats"] = new
                {
                    PA = seasonStats.PA,
                    AB = seasonStats.AB,
                    H = seasonStats.H,
                    Singles = seasonStats.H - (seasonStats.HR + seasonStats.Doubles + seasonStats.Triples),
                    Doubles = seasonStats.Doubles,
                    Triples = seasonStats.Triples,
                    HR = seasonStats.HR,
                    BB = seasonStats.BB,
                    IBB = seasonStats.IBB,
                    HBP = seasonStats.HBP,
                    SF = seasonStats.SF
                },
                ["last7Stats"] = last7Stats != null ? new
                {
                    PA = last7Stats.PA,
                    AB = last7Stats.AB,
                    H = last7Stats.H,
                    Singles = last7Stats.H - (last7Stats.HR + last7Stats.Doubles + last7Stats.Triples),
                    Doubles = last7Stats.Doubles,
                    Triples = last7Stats.Triples,
                    HR = last7Stats.HR,
                    BB = last7Stats.BB,
                    IBB = last7Stats.IBB,
                    HBP = last7Stats.HBP,
                    SF = last7Stats.SF
                } : null
            };
        }

        // Batch process multiple players for wOBA calculations
        public async Task<List<Dictionary<string, object>>> GetMultiplePlayersWobaAsync(List<string> bbrefIds, int year)
        {
            _logger.LogInformation($"Getting wOBA for {bbrefIds.Count} players for year {year}");
            var results = new List<Dictionary<string, object>>();
            var wobaConstants = GetWobaConstants(year);

            // Get all relevant season stats in one query for better performance
            var seasonStats = await _context.TrailingGameLogSplits
                .Where(t => bbrefIds.Contains(t.BbrefId) && t.Split == "Season" && t.Year == year)
                .OrderByDescending(t => t.DateUpdated)
                .ToListAsync();

            // Get all relevant last 7 days stats in one query
            var last7Stats = await _context.TrailingGameLogSplits
                .Where(t => bbrefIds.Contains(t.BbrefId) && t.Split == "Last7G" && t.Year == year)
                .OrderByDescending(t => t.DateUpdated)
                .ToListAsync();

            // Process each player
            foreach (var bbrefId in bbrefIds)
            {
                var playerSeasonStats = seasonStats.FirstOrDefault(s => s.BbrefId == bbrefId);
                var playerLast7Stats = last7Stats.FirstOrDefault(s => s.BbrefId == bbrefId);

                if (playerSeasonStats == null)
                {
                    // Skip players with no stats or add an error entry
                    results.Add(new Dictionary<string, object>
                    {
                        ["bbrefId"] = bbrefId,
                        ["year"] = year,
                        ["error"] = "No season stats found"
                    });
                    continue;
                }

                // Calculate wOBA for season stats
                double seasonWoba = CalculateWoba(playerSeasonStats, year);

                // Calculate wOBA for last 7 games if available
                double? last7Woba = playerLast7Stats != null ? CalculateWoba(playerLast7Stats, year) : null;

                // Calculate blended wOBA (70/30 weight)
                double blendedWoba = last7Woba.HasValue
                    ? (seasonWoba * 0.7) + (last7Woba.Value * 0.3)
                    : seasonWoba;

                results.Add(new Dictionary<string, object>
                {
                    ["bbrefId"] = bbrefId,
                    ["year"] = year,
                    ["seasonWoba"] = seasonWoba,
                    ["last7Woba"] = last7Woba,
                    ["blendedWoba"] = blendedWoba,
                    ["wobaConstants"] = new
                    {
                        LeagueAverage = wobaConstants.LeagueAverage,
                        Scale = wobaConstants.WobaScale,
                        Year = year
                    },
                    ["seasonStats"] = new
                    {
                        PA = playerSeasonStats.PA,
                        Singles = playerSeasonStats.H - (playerSeasonStats.HR + playerSeasonStats.Doubles + playerSeasonStats.Triples),
                        Doubles = playerSeasonStats.Doubles,
                        Triples = playerSeasonStats.Triples,
                        HR = playerSeasonStats.HR,
                        BB = playerSeasonStats.BB,
                        HBP = playerSeasonStats.HBP,
                        SF = playerSeasonStats.SF
                    },
                    ["last7Stats"] = playerLast7Stats != null ? new
                    {
                        PA = playerLast7Stats.PA,
                        Singles = playerLast7Stats.H - (playerLast7Stats.HR + playerLast7Stats.Doubles + playerLast7Stats.Triples),
                        Doubles = playerLast7Stats.Doubles,
                        Triples = playerLast7Stats.Triples,
                        HR = playerLast7Stats.HR,
                        BB = playerLast7Stats.BB,
                        HBP = playerLast7Stats.HBP,
                        SF = playerLast7Stats.SF
                    } : null
                });
            }

            return results;
        }

        // Method to get wOBA for all pitchers in a set of games
        public async Task<List<Dictionary<string, object>>> GetPitchersWobaForGamesAsync(DateTime date)
        {
            // Get all games for the specified date
            var games = await _context.GamePreviews
                .Where(g => g.Date.Date == date.Date)
                .ToListAsync();

            // Extract all pitchers
            var allPitchers = games.SelectMany(g => new[]
            {
                new { Id = g.HomePitcher, Team = g.HomeTeam, IsHome = true, Opponent = g.AwayTeam },
                new { Id = g.AwayPitcher, Team = g.AwayTeam, IsHome = false, Opponent = g.HomeTeam }
            })
            .Where(p => !string.IsNullOrEmpty(p.Id))
            .ToList();

            var results = new List<Dictionary<string, object>>();
            int year = date.Year;

            // For each pitcher, calculate opponent wOBA against
            foreach (var pitcher in allPitchers)
            {
                var pitcherStats = await GetPitcherWobaStatsAsync(pitcher.Id, year, pitcher.IsHome);

                if (pitcherStats.ContainsKey("error"))
                {
                    results.Add(pitcherStats);
                    continue;
                }

                // Add additional game context
                pitcherStats["team"] = pitcher.Team;
                pitcherStats["opponent"] = pitcher.Opponent;
                pitcherStats["isHome"] = pitcher.IsHome;
                pitcherStats["gameDate"] = date.ToString("yyyy-MM-dd");

                results.Add(pitcherStats);
            }

            return results;
        }

        // Helper method to get wOBA stats for a pitcher
        private async Task<Dictionary<string, object>> GetPitcherWobaStatsAsync(string pitcherId, int year, bool isHome)
        {
            // First check if we have PitcherHomeAwaySplits
            var homeAwaySplit = await _context.PitcherHomeAwaySplits
                .FirstOrDefaultAsync(p => p.bbrefID == pitcherId && p.Year == year && p.Split == (isHome ? "Home" : "Away"));

            // Then check PitcherPlatoonAndTrackRecord for Totals
            var totalsRecord = await _context.PitcherPlatoonAndTrackRecord
                .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Year == year && p.Split == "Totals");

            // Check for last28 data
            var last28Record = await _context.PitcherPlatoonAndTrackRecord
                .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Year == year && p.Split == "last28");

            // Get the vsRHB and vsLHB platoon splits
            var vsRHBRecord = await _context.PitcherPlatoonAndTrackRecord
                .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Year == year && p.Split == "vsRHB");

            var vsLHBRecord = await _context.PitcherPlatoonAndTrackRecord
                .FirstOrDefaultAsync(p => p.BbrefID == pitcherId && p.Year == year && p.Split == "vsLHB");

            if (homeAwaySplit == null && totalsRecord == null)
            {
                return new Dictionary<string, object>
                {
                    ["bbrefId"] = pitcherId,
                    ["year"] = year,
                    ["error"] = "No stats found for pitcher"
                };
            }

            var wobaConstants = GetWobaConstants(year);
            var stats = new Dictionary<string, object>
            {
                ["bbrefId"] = pitcherId,
                ["year"] = year
            };

            // Calculate wOBA against for each available split
            if (totalsRecord != null)
            {
                double wobaAgainstSeason = CalculateWobaAgainstFromPlatoon(totalsRecord, year);
                stats["aWOBASeason"] = wobaAgainstSeason;
            }

            if (homeAwaySplit != null)
            {
                double wobaAgainstHomeAway = CalculateWobaAgainstFromSplit(homeAwaySplit, year);
                stats["aWOBAHomeAway"] = wobaAgainstHomeAway;
            }

            if (last28Record != null)
            {
                double wobaAgainstLast28 = CalculateWobaAgainstFromPlatoon(last28Record, year);
                stats["aWOBALast28"] = wobaAgainstLast28;
            }

            // Calculate wOBA for handedness splits if available
            if (vsRHBRecord != null)
            {
                double wobaAgainstRHB = CalculateWobaAgainstFromPlatoon(vsRHBRecord, year);
                stats["wobaVSRHB"] = wobaAgainstRHB;
            }

            if (vsLHBRecord != null)
            {
                double wobaAgainstLHB = CalculateWobaAgainstFromPlatoon(vsLHBRecord, year);
                stats["wobaVSLHB"] = wobaAgainstLHB;
            }

            // Calculate the blended wOBA against (prioritizing more specific data)
            double blendedWobaAgainst;

            if (homeAwaySplit != null && last28Record != null)
            {
                // If we have both home/away and last28, blend them with 50/50 weight
                double wobaHomeAway = (double)stats["aWOBAHomeAway"];
                double wobaLast28 = (double)stats["aWOBALast28"];
                blendedWobaAgainst = (wobaHomeAway * 0.5) + (wobaLast28 * 0.5);
            }
            else if (homeAwaySplit != null)
            {
                // If we only have home/away, blend with season at 70/30 weight
                double wobaHomeAway = (double)stats["aWOBAHomeAway"];
                double woba = totalsRecord != null ? (double)stats["aWOBASeason"] : wobaConstants.LeagueAverage;
                blendedWobaAgainst = (wobaHomeAway * 0.7) + (woba * 0.3);
            }
            else if (last28Record != null)
            {
                // If we only have last28, blend with season at 70/30 weight
                double wobaLast28 = (double)stats["aWOBALast28"];
                double woba = totalsRecord != null ? (double)stats["aWOBASeason"] : wobaConstants.LeagueAverage;
                blendedWobaAgainst = (wobaLast28 * 0.7) + (woba * 0.3);
            }
            else
            {
                // If we only have season totals, use that
                blendedWobaAgainst = (double)stats["aWOBASeason"];
            }

            // Add the blended wOBA against
            stats["wobaAgainst"] = blendedWobaAgainst;

            // Add context about the weights used
            stats["blendingInfo"] = new
            {
                HasHomeAwaySplit = homeAwaySplit != null,
                HasLast28Data = last28Record != null,
                BlendingApproach = GetBlendingDescription(homeAwaySplit != null, last28Record != null)
            };

            stats["wobaConstants"] = new
            {
                LeagueAverage = wobaConstants.LeagueAverage,
                Scale = wobaConstants.WobaScale,
                Year = year
            };

            // Add the actual stats used
            if (homeAwaySplit != null)
            {
                stats["homeAwaySplit"] = new
                {
                    Split = homeAwaySplit.Split,
                    BA = homeAwaySplit.BA,
                    OBP = homeAwaySplit.OBP,
                    SLG = homeAwaySplit.SLG,
                    OPS = homeAwaySplit.OPS,
                    PA = homeAwaySplit.PA,
                    H = homeAwaySplit.H,
                    Doubles = homeAwaySplit.TwoB,
                    Triples = homeAwaySplit.ThreeB,
                    HR = homeAwaySplit.HR,
                    BB = homeAwaySplit.BB,
                    HBP = homeAwaySplit.HBP,
                    SF = homeAwaySplit.SF
                };
            }

            if (totalsRecord != null)
            {
                stats["totalsRecord"] = new
                {
                    BA = totalsRecord.BA,
                    OBP = totalsRecord.OBP,
                    SLG = totalsRecord.SLG,
                    OPS = totalsRecord.OPS,
                    PA = totalsRecord.PA,
                    H = totalsRecord.H,
                    Doubles = totalsRecord.TwoB,
                    Triples = totalsRecord.ThreeB,
                    HR = totalsRecord.HR,
                    BB = totalsRecord.BB,
                    HBP = totalsRecord.HBP,
                    SH = totalsRecord.SH,
                    SF = totalsRecord.SF
                };
            }

            if (last28Record != null)
            {
                stats["last28Record"] = new
                {
                    BA = last28Record.BA,
                    OBP = last28Record.OBP,
                    SLG = last28Record.SLG,
                    OPS = last28Record.OPS,
                    PA = last28Record.PA,
                    H = last28Record.H,
                    Doubles = last28Record.TwoB,
                    Triples = last28Record.ThreeB,
                    HR = last28Record.HR,
                    BB = last28Record.BB,
                    HBP = last28Record.HBP,
                    SH = last28Record.SH,
                    SF = last28Record.SF
                };
            }

            // Add vsRHB and vsLHB detailed stats
            if (vsRHBRecord != null)
            {
                stats["vsRHB"] = new
                {
                    BA = vsRHBRecord.BA,
                    OBP = vsRHBRecord.OBP,
                    SLG = vsRHBRecord.SLG,
                    OPS = vsRHBRecord.OPS,
                    PA = vsRHBRecord.PA,
                    H = vsRHBRecord.H,
                    Doubles = vsRHBRecord.TwoB,
                    Triples = vsRHBRecord.ThreeB,
                    HR = vsRHBRecord.HR,
                    BB = vsRHBRecord.BB,
                    HBP = vsRHBRecord.HBP,
                    SH = vsRHBRecord.SH,
                    SF = vsRHBRecord.SF
                };
            }

            if (vsLHBRecord != null)
            {
                stats["vsLHB"] = new
                {
                    BA = vsLHBRecord.BA,
                    OBP = vsLHBRecord.OBP,
                    SLG = vsLHBRecord.SLG,
                    OPS = vsLHBRecord.OPS,
                    PA = vsLHBRecord.PA,
                    H = vsLHBRecord.H,
                    Doubles = vsLHBRecord.TwoB,
                    Triples = vsLHBRecord.ThreeB,
                    HR = vsLHBRecord.HR,
                    BB = vsLHBRecord.BB,
                    HBP = vsLHBRecord.HBP,
                    SH = vsLHBRecord.SH,
                    SF = vsLHBRecord.SF
                };
            }

            return stats;
        }

        // Helper method for generating blend description
        private string GetBlendingDescription(bool hasHomeAway, bool hasLast28)
        {
            if (hasHomeAway && hasLast28)
                return "50% Home/Away, 50% Last 28 Days";
            else if (hasHomeAway)
                return "70% Home/Away, 30% Season";
            else if (hasLast28)
                return "70% Last 28 Days, 30% Season";
            else
                return "100% Season Totals";
        }

        // Helper method to calculate wOBA against from a HomeAwaySplit
        private double CalculateWobaAgainstFromSplit(PitcherHomeAwaySplits split, int year)
        {
            var constants = GetWobaConstants(year);

            int singles = split.H - (split.HR + split.TwoB + split.ThreeB);

            double weightedEvents =
                (split.BB * constants.BB) +
                (split.HBP * constants.HBP) +
                (singles * constants.Single) +
                (split.TwoB * constants.Double) +
                (split.ThreeB * constants.Triple) +
                (split.HR * constants.HR);

            int adjustedPA = split.AB + split.BB - split.IBB + split.SF + split.HBP;

            if (adjustedPA == 0)
                return 0.0;

            return weightedEvents / adjustedPA;
        }

        // Helper method to calculate wOBA against from a PlatoonAndTrackRecord
        private double CalculateWobaAgainstFromPlatoon(PitcherPlatoonAndTrackRecord record, int year)
        {
            var constants = GetWobaConstants(year);

            int singles = record.H - (record.HR + record.TwoB + record.ThreeB);

            double weightedEvents =
                (record.BB * constants.BB) +
                (record.HBP * constants.HBP) +
                (singles * constants.Single) +
                (record.TwoB * constants.Double) +
                (record.ThreeB * constants.Triple) +
                (record.HR * constants.HR);

            int adjustedPA = record.AB + record.BB - record.IBB + record.SF + record.HBP;

            if (adjustedPA == 0)
                return 0.0;

            return weightedEvents / adjustedPA;
        }

        // Helper method to calculate wOBA against for a pitcher (using both split types if available)
        private double CalculateWobaAgainst(PitcherHomeAwaySplits homeAwaySplit, PitcherPlatoonAndTrackRecord totalsRecord, int year)
        {
            // Prefer HomeAwaySplits if available
            if (homeAwaySplit != null)
            {
                return CalculateWobaAgainstFromSplit(homeAwaySplit, year);
            }

            // Fall back to totals record
            if (totalsRecord != null)
            {
                return CalculateWobaAgainstFromPlatoon(totalsRecord, year);
            }

            return 0.0;
        }

        private string GetLineupStrengthRating(double woba, double leagueAverage)
        {
            double percentDiff = (woba - leagueAverage) / leagueAverage * 100;

            if (percentDiff >= 15) return "Elite";
            if (percentDiff >= 10) return "Great";
            if (percentDiff >= 5) return "Above Average";
            if (percentDiff >= -5) return "Average";
            if (percentDiff >= -10) return "Below Average";
            if (percentDiff >= -15) return "Weak";
            return "Very Weak";
        }

        // Get lineup strength based on wOBA for a team on a specific date
        public async Task<Dictionary<string, object>> GetRawLineupStrengthAsync(string teamName, DateTime date)
        {
            _logger.LogInformation($"Getting raw lineup strength for {teamName} on {date:yyyy-MM-dd}");
            int year = date.Year;

            // First try to get the actual lineup
            var actualLineup = await _context.ActualLineups
                .FirstOrDefaultAsync(l => l.Team == teamName && l.Date.Date == date.Date);

            // If we don't have an actual lineup, try to get a predicted lineup
            var predictedLineup = actualLineup == null ?
                await _context.LineupPredictions
                    .FirstOrDefaultAsync(l => l.Team == teamName && l.Date.Date == date.Date) : null;

            // Check if we found a lineup
            if (actualLineup == null && predictedLineup == null)
            {
                return new Dictionary<string, object>
                {
                    ["teamName"] = teamName,
                    ["date"] = date.ToString("yyyy-MM-dd"),
                    ["error"] = "No lineup found for the specified team and date"
                };
            }

            // Extract BBRef IDs from the lineup
            List<string> lineupIds = new List<string>();

            if (actualLineup != null)
            {
                lineupIds.Add(actualLineup.Batting1st);
                lineupIds.Add(actualLineup.Batting2nd);
                lineupIds.Add(actualLineup.Batting3rd);
                lineupIds.Add(actualLineup.Batting4th);
                lineupIds.Add(actualLineup.Batting5th);
                lineupIds.Add(actualLineup.Batting6th);
                lineupIds.Add(actualLineup.Batting7th);
                lineupIds.Add(actualLineup.Batting8th);
                lineupIds.Add(actualLineup.Batting9th);
            }
            else
            {
                lineupIds.Add(predictedLineup.Batting1st);
                lineupIds.Add(predictedLineup.Batting2nd);
                lineupIds.Add(predictedLineup.Batting3rd);
                lineupIds.Add(predictedLineup.Batting4th);
                lineupIds.Add(predictedLineup.Batting5th);
                lineupIds.Add(predictedLineup.Batting6th);
                lineupIds.Add(predictedLineup.Batting7th);
                lineupIds.Add(predictedLineup.Batting8th);
                lineupIds.Add(predictedLineup.Batting9th);
            }

            // Remove any null or empty player IDs
            lineupIds = lineupIds.Where(id => !string.IsNullOrEmpty(id)).ToList();

            if (!lineupIds.Any())
            {
                return new Dictionary<string, object>
                {
                    ["teamName"] = teamName,
                    ["date"] = date.ToString("yyyy-MM-dd"),
                    ["error"] = "Lineup contains no valid player IDs"
                };
            }

            // Get wOBA for all players in the lineup
            var playerWobaResults = await GetMultiplePlayersWobaAsync(lineupIds, year);

            // Calculate aggregate statistics for the entire lineup
            int seasonPA = 0;
            int seasonSingles = 0;
            int seasonDoubles = 0;
            int seasonTriples = 0;
            int seasonHR = 0;
            int seasonBB = 0;
            int seasonHBP = 0;
            int seasonSF = 0;

            int last7PA = 0;
            int last7Singles = 0;
            int last7Doubles = 0;
            int last7Triples = 0;
            int last7HR = 0;
            int last7BB = 0;
            int last7HBP = 0;
            int last7SF = 0;

            // Players with valid stats
            int validPlayers = 0;
            int playersWithLast7 = 0;

            // Collect all player stats
            foreach (var playerResult in playerWobaResults)
            {
                // Skip players with errors
                if (playerResult.ContainsKey("error"))
                    continue;

                validPlayers++;

                // Get season stats from the player
                var seasonStats = playerResult["seasonStats"] as dynamic;
                if (seasonStats != null)
                {
                    seasonPA += (int)seasonStats.PA;
                    seasonSingles += (int)seasonStats.Singles;
                    seasonDoubles += (int)seasonStats.Doubles;
                    seasonTriples += (int)seasonStats.Triples;
                    seasonHR += (int)seasonStats.HR;
                    seasonBB += (int)seasonStats.BB;
                    seasonHBP += (int)seasonStats.HBP;
                    seasonSF += (int)seasonStats.SF;
                }

                // Get last7 stats from the player if available
                var last7Stats = playerResult["last7Stats"] as dynamic;
                if (last7Stats != null)
                {
                    playersWithLast7++;
                    last7PA += (int)last7Stats.PA;
                    last7Singles += (int)last7Stats.Singles;
                    last7Doubles += (int)last7Stats.Doubles;
                    last7Triples += (int)last7Stats.Triples;
                    last7HR += (int)last7Stats.HR;
                    last7BB += (int)last7Stats.BB;
                    last7HBP += (int)last7Stats.HBP;
                    last7SF += (int)last7Stats.SF;
                }
            }

            // Get the wOBA constants for the year
            var wobaConstants = GetWobaConstants(year);

            // Calculate lineup season wOBA
            double lineupSeasonWoba = 0;
            if (seasonPA > 0)
            {
                double weightedEvents =
                    (seasonBB * wobaConstants.BB) +
                    (seasonHBP * wobaConstants.HBP) +
                    (seasonSingles * wobaConstants.Single) +
                    (seasonDoubles * wobaConstants.Double) +
                    (seasonTriples * wobaConstants.Triple) +
                    (seasonHR * wobaConstants.HR);

                int adjustedPA = seasonPA;

                lineupSeasonWoba = weightedEvents / adjustedPA;
            }

            // Calculate lineup last7 wOBA if data is available
            double? lineupLast7Woba = null;
            if (last7PA > 0)
            {
                double weightedEvents =
                    (last7BB * wobaConstants.BB) +
                    (last7HBP * wobaConstants.HBP) +
                    (last7Singles * wobaConstants.Single) +
                    (last7Doubles * wobaConstants.Double) +
                    (last7Triples * wobaConstants.Triple) +
                    (last7HR * wobaConstants.HR);

                int adjustedPA = last7PA;

                lineupLast7Woba = weightedEvents / adjustedPA;
            }

            // Calculate blended wOBA if we have both season and recent stats (70/30 weight)
            double lineupBlendedWoba = lineupLast7Woba.HasValue
                ? (lineupSeasonWoba * 0.6) + (lineupLast7Woba.Value * 0.4)
                : lineupSeasonWoba;

            // Calculate expected runs based on wOBA
            //double expectedRunsPer9 = (lineupBlendedWoba * 10 - 3.11) * 1.6 + 4.35;//simplified
            //double expectedRunsPer9 = (lineupBlendedWoba - wobaConstants.LeagueAverage)/ 0.0016 + 4.5;//low end
            //double expectedRunsPer9 = (lineupBlendedWoba * wobaConstants.WobaScale) * 9;//universal
            //double expectedRunsPer9 = ((lineupBlendedWoba - wobaConstants.LeagueAverage)  /0.0143) + 4.35;//one for all
            //double expectedRunsPer9 = 18.0 * lineupBlendedWoba * lineupBlendedWoba - 5.0 * lineupBlendedWoba + 2.7;
            //quadratic exRS = a * wOba^2 + b * wOba + c
            double expectedRunsPer9 = 175.3873 * lineupBlendedWoba * lineupBlendedWoba - 74.1545 * lineupBlendedWoba + 10.4484;


            // Calculate comparison to league average
            double comparisonToLeague = ((lineupBlendedWoba - wobaConstants.LeagueAverage) / wobaConstants.LeagueAverage) * 100;

            // Create the final result
            var result = new Dictionary<string, object>
            {
                ["teamName"] = teamName,
                ["date"] = date.ToString("yyyy-MM-dd"),
                ["lineupSource"] = actualLineup != null ? "ActualLineup" : "PredictedLineup",
                ["playersInLineup"] = lineupIds.Count,
                ["validPlayersWithStats"] = validPlayers,
                ["playersWithLast7Stats"] = playersWithLast7,
                ["lineupSeasonWoba"] = lineupSeasonWoba,
                ["lineupLast7Woba"] = lineupLast7Woba,
                ["lineupBlendedWoba"] = lineupBlendedWoba,
                ["comparisonToLeagueAverage"] = comparisonToLeague,
                ["RAWexpectedRunsPer9"] = expectedRunsPer9,
                ["lineupStrengthRating"] = GetLineupStrengthRating(lineupBlendedWoba, wobaConstants.LeagueAverage),
                ["wobaConstants"] = new
                {
                    LeagueAverage = wobaConstants.LeagueAverage,
                    Scale = wobaConstants.WobaScale,
                    Year = year
                },
                ["aggregateSeasonStats"] = new
                {
                    PA = seasonPA,
                    Singles = seasonSingles,
                    Doubles = seasonDoubles,
                    Triples = seasonTriples,
                    HR = seasonHR,
                    BB = seasonBB,
                    HBP = seasonHBP,
                    SF = seasonSF
                },
                ["aggregateLast7Stats"] = lineupLast7Woba.HasValue ? new
                {
                    PA = last7PA,
                    Singles = last7Singles,
                    Doubles = last7Doubles,
                    Triples = last7Triples,
                    HR = last7HR,
                    BB = last7BB,
                    HBP = last7HBP,
                    SF = last7SF
                } : null,
                ["individualPlayerStats"] = playerWobaResults,
                ["lineup"] = lineupIds
            };

            return result;
        }

        public async Task<List<Dictionary<string, object>>> GetWobaAdjustedRunsF5Async(DateTime date)
        {
            _logger.LogInformation($"Calculating wOBA adjusted runs for games on {date:yyyy-MM-dd}");
            var results = new List<Dictionary<string, object>>();
            int year = date.Year;

            // Get all games for the specified date
            var games = await _context.GamePreviews
                .Where(g => g.Date.Date == date.Date)
                .ToListAsync();

            if (!games.Any())
            {
                _logger.LogWarning($"No games found for date {date:yyyy-MM-dd}");
                return results;
            }

            // Constants
            var wobaConstants = GetWobaConstants(year);
            const double FIVE_INNING_SCALAR = 5.0 / 9.0;

            // Process each game
            foreach (var game in games)
            {
                try
                {
                    // Get home and away team names
                    string homeTeam = game.HomeTeam;
                    string awayTeam = game.AwayTeam;

                    // Get starting pitchers
                    string homePitcher = game.HomePitcher;
                    string awayPitcher = game.AwayPitcher;

                    if (string.IsNullOrEmpty(homePitcher) || string.IsNullOrEmpty(awayPitcher))
                    {
                        _logger.LogWarning($"Missing pitcher for game {game.Id} on {date:yyyy-MM-dd}");
                        continue;
                    }

                    // Get raw lineup strength for home team
                    var homeLineupStrength = await GetRawLineupStrengthAsync(homeTeam, date);

                    // Get raw lineup strength for away team
                    var awayLineupStrength = await GetRawLineupStrengthAsync(awayTeam, date);

                    if (homeLineupStrength.ContainsKey("error") || awayLineupStrength.ContainsKey("error"))
                    {
                        _logger.LogWarning($"Missing lineup data for game between {homeTeam} and {awayTeam}");
                        continue;
                    }

                    // Get pitcher wOBA against stats
                    var homePitcherStats = await GetPitcherWobaStatsAsync(homePitcher, year, true);
                    var awayPitcherStats = await GetPitcherWobaStatsAsync(awayPitcher, year, false);

                    if (homePitcherStats.ContainsKey("error") || awayPitcherStats.ContainsKey("error"))
                    {
                        _logger.LogWarning($"Missing pitcher stats for {homePitcher} or {awayPitcher}");
                        continue;
                    }

                    // Extract raw expected runs and pitcher wOBA against
                    double homeRawExpectedRuns = (double)homeLineupStrength["RAWexpectedRunsPer9"];
                    double awayRawExpectedRuns = (double)awayLineupStrength["RAWexpectedRunsPer9"];

                    double homePitcherWobaAgainst = (double)homePitcherStats["wobaAgainst"];
                    double awayPitcherWobaAgainst = (double)awayPitcherStats["wobaAgainst"];

                    // Calculate adjustment factors based on pitcher quality
                    // If pitcher is league average, factor is 1.0
                    // If pitcher is better than average, factor is < 1.0
                    // If pitcher is worse than average, factor is > 1.0
                    double homePitcherAdjustmentFactor = homePitcherWobaAgainst / wobaConstants.LeagueAverage;
                    double awayPitcherAdjustmentFactor = awayPitcherWobaAgainst / wobaConstants.LeagueAverage;

                    // Apply adjustment to expected runs
                    // Home team faces the away pitcher, so use away pitcher's adjustment factor
                    // Away team faces the home pitcher, so use home pitcher's adjustment factor
                    double homeAdjustedExpectedRunsF9 = homeRawExpectedRuns * awayPitcherAdjustmentFactor;
                    double awayAdjustedExpectedRunsF9 = awayRawExpectedRuns * homePitcherAdjustmentFactor;

                    // Scale to 5 innings
                    double homeAdjustedExpectedRunsF5 = homeAdjustedExpectedRunsF9 * FIVE_INNING_SCALAR;
                    double awayAdjustedExpectedRunsF5 = awayAdjustedExpectedRunsF9 * FIVE_INNING_SCALAR;

                    // Calculate run differential (positive means home team advantage)
                    double runDifferentialF5 = homeAdjustedExpectedRunsF5 - awayAdjustedExpectedRunsF5;

                    // Add results - keeping the original property names for backward compatibility
                    results.Add(new Dictionary<string, object>
                    {
                        ["gameId"] = game.Id,
                        ["date"] = date.ToString("yyyy-MM-dd"),
                        ["homeTeam"] = new Dictionary<string, object>
                        {
                            ["team"] = homeTeam,
                            ["pitcher"] = homePitcher,
                            ["rawExpectedRunsF9"] = homeRawExpectedRuns,
                            ["rawExpectedRunsF5"] = homeRawExpectedRuns * FIVE_INNING_SCALAR,
                            ["adjustedExpectedRunsF5"] = homeAdjustedExpectedRunsF5,
                            ["pitcherWobaAgainst"] = awayPitcherWobaAgainst,  // This is the AWAY pitcher's wOBA (who the home team faces)
                            ["pitcherAdjustmentFactor"] = awayPitcherAdjustmentFactor  // This is the AWAY pitcher's adjustment factor
                        },
                        ["awayTeam"] = new Dictionary<string, object>
                        {
                            ["team"] = awayTeam,
                            ["pitcher"] = awayPitcher,
                            ["rawExpectedRunsF9"] = awayRawExpectedRuns,
                            ["rawExpectedRunsF5"] = awayRawExpectedRuns * FIVE_INNING_SCALAR,
                            ["adjustedExpectedRunsF5"] = awayAdjustedExpectedRunsF5,
                            ["pitcherWobaAgainst"] = homePitcherWobaAgainst,  // This is the HOME pitcher's wOBA (who the away team faces)
                            ["pitcherAdjustmentFactor"] = homePitcherAdjustmentFactor  // This is the HOME pitcher's adjustment factor
                        },
                        ["runDifferentialF5"] = runDifferentialF5,
                        ["favoredTeam"] = runDifferentialF5 > 0 ? homeTeam : awayTeam,
                        ["totalExpectedRunsF5"] = homeAdjustedExpectedRunsF5 + awayAdjustedExpectedRunsF5
                    });
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, $"Error processing game {game.Id} on {date:yyyy-MM-dd}");
                }
            }

            return results;
        }
    }
}