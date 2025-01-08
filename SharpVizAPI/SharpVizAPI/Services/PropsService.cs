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

    public class PitcherStats
    {
        public string BbrefID { get; set; }
        public int SB { get; set; }
        public int CS { get; set; }
        public double BA { get; set; }
        public double OBP { get; set; }
        public double BAbip { get; set; }

        public int IBB { get; set; }
        public int BB { get; set; }
        public int ROE { get; set; }
        public int H { get; set; }

        public int IP { get; set; }


    }

    public class HitterStats
    {
        public string PitcherBbrefID { get; set; }
        public string HitterBbrefID { get; set; }
        public string Name { get; set; }
        public int SB { get; set; }
        public int CS { get; set; }
        public int BB { get; set; }
        public int IBB { get; set; }

        public double BA { get; set; }
        public double OBP { get; set; }

        public int PA { get; set; }
        public int AB { get; set; }
        public int K { get; set; }


    }

    public class PitcherWithHitters
    {
        public string BbrefID { get; set; }
        public int SB { get; set; }
        public int CS { get; set; }
        public double BA { get; set; }
        public double OBP { get; set; }
        public double BAbip { get; set; }
        public List<HitterStats> Hitters { get; set; }
    }
    public class PitcherStrikeoutProjection
    {
        public string Team { get; set; }
        public string Pitcher { get; set; }
        public double SeasonKRate { get; set; }
        public double Last28KRate { get; set; }
        public double DeltaKRate { get; set; }
        public List<HitterProjection> Hitters { get; set; }
        public double SeasonProjection { get; set; }
        public double Last28Projection { get; set; }
    }

    public class HitterProjection
    {
        public string Name { get; set; }
        public double KRate { get; set; }
    }

    public class PropsService
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<PropsService> _logger;

        public PropsService(NrfidbContext context, ILogger<PropsService> logger)
        {
            _context = context;
            _logger = logger;
        }

        // Method to get the season stats of all pitchers pitching on a given date
        public async Task<List<PitcherPlatoonAndTrackRecord>> SPstatsTotals(DateTime date)
        {
            _logger.LogInformation($"Fetching game previews for date: {date}");
            var gamePreviews = await _context.GamePreviews.Where(g => g.Date == date).ToListAsync();
            var pitcherIds = gamePreviews.SelectMany(g => new[] { g.HomePitcher, g.AwayPitcher }).Where(p => !string.IsNullOrEmpty(p)).ToList();

            _logger.LogInformation($"Found {pitcherIds.Count} pitchers for date: {date}");
            var pitcherStats = await _context.PitcherPlatoonAndTrackRecord.Where(p => pitcherIds.Contains(p.BbrefID) && p.Split == "Totals").ToListAsync();

            _logger.LogInformation($"Retrieved {pitcherStats.Count} pitcher stats for date: {date}");
            return pitcherStats;
        }

        // Method to get the last 28 days stats of all pitchers pitching on a given date
        public async Task<List<PitcherPlatoonAndTrackRecord>> SPstatsLast28(DateTime date)
        {
            _logger.LogInformation($"Fetching game previews for date: {date}");
            var gamePreviews = await _context.GamePreviews.Where(g => g.Date == date).ToListAsync();
            var pitcherIds = gamePreviews.SelectMany(g => new[] { g.HomePitcher, g.AwayPitcher }).Where(p => !string.IsNullOrEmpty(p)).ToList();

            _logger.LogInformation($"Found {pitcherIds.Count} pitchers for date: {date}");
            var pitcherStats = await _context.PitcherPlatoonAndTrackRecord.Where(p => pitcherIds.Contains(p.BbrefID) && p.Split == "last28").ToListAsync();

            _logger.LogInformation($"Retrieved {pitcherStats.Count} pitcher stats for last 28 days (Split: last28)");
            return pitcherStats;
        }

        // Method to get the season stats of all hitters in the actual lineups for today's games
        public async Task<List<Hitter>> GetHittersStatsForToday(DateTime date)
        {
            _logger.LogInformation($"Fetching actual lineups for date: {date}");
            var actualLineups = await _context.ActualLineups.Where(l => l.Date == date).ToListAsync();
            var hitterIds = actualLineups.SelectMany(l => new[]
            {
            l.Batting1st, l.Batting2nd, l.Batting3rd, l.Batting4th, l.Batting5th,
            l.Batting6th, l.Batting7th, l.Batting8th, l.Batting9th
        }).Where(id => !string.IsNullOrEmpty(id)).Distinct().ToList();

            _logger.LogInformation($"Found {hitterIds.Count} hitters in actual lineups for date: {date}");
            var hittersStats = await _context.Hitters.Where(h => hitterIds.Contains(h.bbrefId)).ToListAsync();

            _logger.LogInformation($"Retrieved {hittersStats.Count} hitter stats for date: {date}");
            return hittersStats;
        }

        // Method to find the top 5 pitchers with the highest SB and their stats
        public async Task<List<PitcherWithHitters>> GetTopPitchersAndLineupStealers(DateTime date)
        {
            _logger.LogInformation($"Fetching top pitchers and lineup stealers for date: {date}");

            // Get all pitchers stats
            var pitcherStats = await SPstatsTotals(date);

            // Find the top 5 pitchers with the most SB
            var topPitchers = pitcherStats
                .OrderByDescending(p => p.SB)
                .Take(5)
                .Select(p => new PitcherWithHitters
                {
                    BbrefID = p.BbrefID,
                    SB = p.SB,
                    CS = p.CS,
                    BA = p.BA,
                    OBP = p.OBP,
                    BAbip = p.BAbip,
                    Hitters = new List<HitterStats>() // Initialize empty list of hitters
                })
                .ToList();

            _logger.LogInformation($"Top pitchers found: {topPitchers.Count}");

            // Get today's actual lineups
            var lineups = await GetHittersStatsForToday(date);

            foreach (var pitcher in topPitchers)
            {
                // Find the game where this pitcher is playing (home or away)
                var gamePreview = await _context.GamePreviews
                    .Where(g => g.Date == date && (g.HomePitcher == pitcher.BbrefID || g.AwayPitcher == pitcher.BbrefID))
                    .FirstOrDefaultAsync();

                if (gamePreview != null)
                {
                    // Determine the team the pitcher is facing
                    var opponentTeam = gamePreview.HomePitcher == pitcher.BbrefID ? gamePreview.AwayTeam : gamePreview.HomeTeam;

                    // Get the lineup for the opponent team
                    var lineup = await _context.ActualLineups
                        .Where(l => l.Date == date && l.Team == opponentTeam)
                        .FirstOrDefaultAsync();

                    if (lineup != null)
                    {
                        // Get the top 3 hitters in the lineup based on SB
                        var topLineupHitters = lineups
                            .Where(h => new[]
                            {
                            lineup.Batting1st,
                            lineup.Batting2nd,
                            lineup.Batting3rd,
                            lineup.Batting4th,
                            lineup.Batting5th,
                            lineup.Batting6th,
                            lineup.Batting7th,
                            lineup.Batting8th,
                            lineup.Batting9th
                            }.Contains(h.bbrefId))
                            .OrderByDescending(h => h.SB)
                            .Take(3)
                            .Select(h => new HitterStats
                            {
                                PitcherBbrefID = pitcher.BbrefID,
                                HitterBbrefID = h.bbrefId,
                                Name = h.Name,
                                SB = h.SB,
                                CS = h.CS,
                                BA = h.BA,
                                OBP = h.OBP
                            })
                            .ToList();

                        _logger.LogInformation($"Found {topLineupHitters.Count} hitters for pitcher {pitcher.BbrefID}");

                        // Add the hitters to the corresponding pitcher's Hitters list
                        pitcher.Hitters.AddRange(topLineupHitters);
                    }
                }
            }

            _logger.LogInformation($"Returning top pitchers with their respective hitters.");
            return topPitchers;
        }

        private async Task<List<HitterStats>> GetLineupStats(string teamFullName, DateTime date)
        {
            _logger.LogInformation($"Fetching lineup stats for team {teamFullName} on date: {date}");

            // Fetch the actual lineup for the team on the given date
            var lineup = await _context.ActualLineups
                .Where(l => l.Date == date && l.Team == teamFullName)
                .FirstOrDefaultAsync();

            if (lineup == null)
            {
                _logger.LogWarning($"No lineup found for team {teamFullName} on date {date}. Returning empty list.");
                return new List<HitterStats>();
            }

            // Retrieve hitter IDs from the lineup
            var hitterIds = new[]
            {
            lineup.Batting1st, lineup.Batting2nd, lineup.Batting3rd, lineup.Batting4th,
            lineup.Batting5th, lineup.Batting6th, lineup.Batting7th, lineup.Batting8th, lineup.Batting9th
        }.Where(id => !string.IsNullOrEmpty(id)).ToList();

            // Attempt to retrieve stats from HitterLast7 first
            var hitterStatsLast7 = await _context.HitterLast7
                .Where(h => hitterIds.Contains(h.BbrefId))
                .Select(h => new HitterStats
                {
                    PitcherBbrefID = null, // This will be set later when creating the projection
                    HitterBbrefID = h.BbrefId,
                    Name = h.Name,
                    SB = h.SB,
                    BA = h.AVG,
                    OBP = h.OBP,
                    AB = h.AB,
                    K = h.K
                })
                .ToListAsync();

            // If no records found in HitterLast7, fallback to Hitters table
            if (hitterStatsLast7.Count == 0)
            {
                _logger.LogInformation($"No HitterLast7 records found, falling back to season stats from Hitters table.");
                var hitterStatsSeason = await _context.Hitters
                    .Where(h => hitterIds.Contains(h.bbrefId))
                    .Select(h => new HitterStats
                    {
                        PitcherBbrefID = null, // This will be set later when creating the projection
                        HitterBbrefID = h.bbrefId,
                        Name = h.Name,
                        SB = h.SB,
                        CS = h.CS,
                        BA = h.BA,
                        OBP = h.OBP,
                        AB = h.AB,
                        K = h.SO
                    })
                    .ToListAsync();

                return hitterStatsSeason;
            }

            return hitterStatsLast7;
        }

        private double CalculateExpectedStrikeouts(double pitcherKRate, List<HitterStats> hitters, double estimatedPA)
        {
            // Check if we have a valid lineup; if not, return 0
            if (hitters == null || hitters.Count == 0)
            {
                return 0;
            }

            double totalStrikeouts = 0;
            int hittersCount = hitters.Count;
            int paCounter = 0;

            while (paCounter < estimatedPA)
            {
                for (int i = 0; i < hittersCount && paCounter < estimatedPA; i++)
                {
                    // Calculate the combined strikeout rate using the average of pitcherKRate and hitterKRate
                    double hitterKRate = CalculateHitterKRate(hitters[i].K, hitters[i].AB, hitters[i].BB); // Adjusted with BB
                    double combinedKRate = (pitcherKRate + hitterKRate) / 2;

                    // Increment the total strikeouts based on the combined strikeout rate for this PA
                    totalStrikeouts += combinedKRate;
                    paCounter++;

                    // Safeguard to prevent infinite loop
                    if (paCounter >= estimatedPA)
                    {
                        break;
                    }
                }
            }

            return totalStrikeouts;
        }




        private double CalculateHitterKRate(int strikeouts, int atBats, int walks)
        {
            return (atBats + walks) == 0 ? 0 : (double)strikeouts / (atBats + walks);
        }

        private double CalculateStrikeoutRate(int strikeouts, int plateAppearances)
        {
            return plateAppearances == 0 ? 0 : (double)strikeouts / plateAppearances;
        }

        private double CalculateWHIP(int hits, int walks, double inningsPitched)
        {
            return inningsPitched == 0 ? 0 : (hits + walks) / inningsPitched;
        }

        private double CalculateEstimatedPA(double whip)
        {
            return (6 * whip) + 18;
        }

        public async Task<List<PitcherStrikeoutProjection>> GetStrikeoutProjections(DateTime date)
        {
            var gamePreviews = await _context.GamePreviews.Where(g => g.Date == date).ToListAsync();
            var seasonStats = await SPstatsTotals(date);
            var last28Stats = await SPstatsLast28(date);

            var results = new List<PitcherStrikeoutProjection>();

            foreach (var gamePreview in gamePreviews)
            {
                foreach (var pitcherId in new[] { gamePreview.HomePitcher, gamePreview.AwayPitcher })
                {
                    var seasonStatsForPitcher = seasonStats.FirstOrDefault(p => p.BbrefID == pitcherId);
                    var last28StatsForPitcher = last28Stats.FirstOrDefault(p => p.BbrefID == pitcherId);

                    if (seasonStatsForPitcher == null || last28StatsForPitcher == null)
                    {
                        continue;
                    }

                    var pitcherData = await _context.Pitchers.FirstOrDefaultAsync(p => p.BbrefId == pitcherId);
                    if (pitcherData == null)
                    {
                        _logger.LogWarning($"No pitcher data found for {pitcherId}. Skipping this pitcher.");
                        continue;
                    }

                    double whip = pitcherData.WHIP;
                    double estimatedPA = CalculateEstimatedPA(whip);
                    var seasonKRate = CalculateStrikeoutRate(seasonStatsForPitcher.SO, seasonStatsForPitcher.PA);
                    var last28KRate = CalculateStrikeoutRate(last28StatsForPitcher.SO, last28StatsForPitcher.PA);
                    var deltaKRate = last28KRate - seasonKRate;

                    var opposingTeam = gamePreview.HomePitcher == pitcherId ? gamePreview.AwayTeam : gamePreview.HomeTeam;
                    var hitters = await GetLineupStats(opposingTeam, date);

                    // Ensure no duplicate hitters by selecting distinct HitterBbrefID
                    hitters = hitters.GroupBy(h => h.HitterBbrefID)
                                     .Select(g => g.First())
                                     .ToList();

                    // Use season K-rate for season projection
                    var seasonExpectedK = CalculateExpectedStrikeouts(seasonKRate, hitters, estimatedPA);

                    // Use last28 K-rate for last28 projection
                    var last28ExpectedK = CalculateExpectedStrikeouts(last28KRate, hitters, estimatedPA);

                    var projection = new PitcherStrikeoutProjection
                    {
                        Team = opposingTeam,
                        Pitcher = pitcherId,
                        SeasonKRate = seasonKRate,
                        Last28KRate = last28KRate,
                        DeltaKRate = deltaKRate,
                        Hitters = hitters.Select(h => new HitterProjection
                        {
                            Name = h.Name,
                            KRate = CalculateHitterKRate(h.K, h.AB, h.BB)
                        }).ToList(),
                        SeasonProjection = seasonExpectedK, // Use the season-based expected strikeouts
                        Last28Projection = last28ExpectedK  // Use the last 28 days-based expected strikeouts
                    };


                    results.Add(projection);
                }
            }

            return results;
        }

    }

}
