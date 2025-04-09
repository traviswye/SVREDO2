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
    }
}