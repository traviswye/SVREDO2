using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.Intrinsics.Arm;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;


namespace SharpVizAPI.Services
{
    public class BJmodelingService
    {
        private readonly NrfidbContext _context;
        private readonly BlendingService _blendingService;

        public BJmodelingService(NrfidbContext context, BlendingService blendingService)
        {
            _context = context;
            _blendingService = blendingService;
        }

        public async Task<double?> GetRawWinProbabilityAsync(string teamName, DateTime date)
        {
            // Make the team name case insensitive
            teamName = teamName?.ToLowerInvariant();

            // Get the game preview for the given team and date (case-insensitive)
            var gamePreview = await _context.GamePreviews
                .FirstOrDefaultAsync(g =>
                    (g.HomeTeam.ToLower() == teamName || g.AwayTeam.ToLower() == teamName) &&
                    g.Date == date);

            if (gamePreview == null)
            {
                return null; // No game found for this date/team
            }

            // Determine the opponent team
            string opponentTeam = gamePreview.HomeTeam.ToLower() == teamName ? gamePreview.AwayTeam : gamePreview.HomeTeam;

            // Get the team record splits for both teams (case-insensitive)
            var teamRecSplit = await _context.TeamRecSplits.FirstOrDefaultAsync(t => t.Team.ToLower() == teamName);
            var opponentRecSplit = await _context.TeamRecSplits.FirstOrDefaultAsync(t => t.Team.ToLower() == opponentTeam.ToLower());

            if (teamRecSplit == null || opponentRecSplit == null)
            {
                return null; // If we couldn't find the records for either team
            }

            // Use winning percentages from the TeamRecSplits table
            double A = teamRecSplit.WinPercentage;
            double B = opponentRecSplit.WinPercentage;

            // Calculate the probability using the provided formula
            double P = (A - (A * B)) / (A + B - (2 * A * B));

            return P;
        }

        public async Task<double?> CalcPythagAsync(string teamName)
        {
            // Make the team name case insensitive
            teamName = teamName?.ToLowerInvariant();

            // Get the team record splits for the given team (case-insensitive)
            var teamRecSplit = await _context.TeamRecSplits.FirstOrDefaultAsync(t => t.Team.ToLower() == teamName);

            if (teamRecSplit == null)
            {
                return null; // No record found for the given team
            }

            // Get runs scored and runs allowed
            double runsScored = teamRecSplit.RunsScored;
            double runsAllowed = teamRecSplit.RunsAgainst;

            // Calculate the Pythagorean winning percentage
            double pythagWinPercentage = Math.Pow(runsScored, 2) / (Math.Pow(runsScored, 2) + Math.Pow(runsAllowed, 2));

            return pythagWinPercentage;
        }

        public async Task<double?> GetPythagWinProbabilityAsync(string teamName, DateTime date)
        {
            // Make the team name case insensitive
            teamName = teamName?.ToLowerInvariant();

            // Get the game preview for the given team and date (case-insensitive)
            var gamePreview = await _context.GamePreviews
                .FirstOrDefaultAsync(g =>
                    (g.HomeTeam.ToLower() == teamName || g.AwayTeam.ToLower() == teamName) &&
                    g.Date == date);

            if (gamePreview == null)
            {
                return null; // No game found for this date/team
            }

            // Determine the opponent team
            string opponentTeam = gamePreview.HomeTeam.ToLower() == teamName ? gamePreview.AwayTeam : gamePreview.HomeTeam;

            // Get the Pythagorean winning percentage for both teams (case-insensitive)
            double? teamPythag = await CalcPythagAsync(teamName);
            double? opponentPythag = await CalcPythagAsync(opponentTeam);

            if (teamPythag == null || opponentPythag == null)
            {
                return null; // If we couldn't calculate the Pythagorean winning percentage for either team
            }

            // Use Pythagorean winning percentages to calculate win probability
            double A = teamPythag.Value;
            double B = opponentPythag.Value;

            // Calculate the probability using the provided formula
            double P = (A - (A * B)) / (A + B - (2 * A * B));

            return P;
        }

        // New method to get raw win probabilities for all games on a given date
        public async Task<List<object>> GetRawWinProbabilitiesForDateAsync(DateTime date)
        {
            var gamePreviews = await _context.GamePreviews.Where(g => g.Date == date).ToListAsync();

            if (!gamePreviews.Any())
            {
                return null; // No games found for the given date
            }

            var probabilities = new List<object>();

            foreach (var game in gamePreviews)
            {
                double? homeProbability = await GetRawWinProbabilityAsync(game.HomeTeam, date);
                double? awayProbability = await GetRawWinProbabilityAsync(game.AwayTeam, date);

                probabilities.Add(new
                {
                    HomeTeam = game.HomeTeam,
                    AwayTeam = game.AwayTeam,
                    Date = date,
                    HomeTeamWinProbability = homeProbability,
                    AwayTeamWinProbability = awayProbability
                });
            }

            return probabilities;
        }

        // New method to get Pythagorean win probabilities for all games on a given date
        public async Task<List<object>> GetPythagWinProbabilitiesForDateAsync(DateTime date)
        {
            var gamePreviews = await _context.GamePreviews.Where(g => g.Date == date).ToListAsync();

            if (!gamePreviews.Any())
            {
                return null; // No games found for the given date
            }

            var probabilities = new List<object>();

            foreach (var game in gamePreviews)
            {
                double? homeProbability = await GetPythagWinProbabilityAsync(game.HomeTeam, date);
                double? awayProbability = await GetPythagWinProbabilityAsync(game.AwayTeam, date);

                probabilities.Add(new
                {
                    HomeTeam = game.HomeTeam,
                    AwayTeam = game.AwayTeam,
                    Date = date,
                    HomeTeamWinProbability = homeProbability,
                    AwayTeamWinProbability = awayProbability
                });
            }

            return probabilities;
        }
        // BASERUNS library.fangraphs.com/features/baseruns/
        public async Task<(string bbrefid, double bsr, int games, double bsrPerGame)?> CalculateBsRAsync(string bbrefid, int year)
        {
            // Find the hitter by bbrefid
            var hitter = await _context.Hitters.FirstOrDefaultAsync(h => h.bbrefId == bbrefid && h.Year == year);

            if (hitter == null)
            {
                return null; // No hitter found for the given bbrefid
            }

            // Define components A, B, and C for Base Runs
            double A = hitter.H + hitter.BB + hitter.HBP - (0.5*hitter.IBB) - hitter.HR;
            double B = 0.9*(hitter.SB-hitter.CS-hitter.GIDP)+(1.4 * hitter.TB - 0.6 * hitter.H - 3 * hitter.HR + 0.1 * (hitter.BB+hitter.HBP - hitter.IBB)) * 1.1;
            double C = hitter.PA - hitter.BB - hitter.SF - hitter.SH - hitter.H + hitter.CS + hitter.GIDP;
            double D = hitter.HR;

            // Calculate Base Runs (BsR)
            double bsr = ((A * B) / (B + C)) + D;

            // Calculate games played and BsR per game
            int games = hitter.G;
            double bsrPerGame = games > 0 ? bsr / games : 0.0;

            return (bbrefid, bsr, games, bsrPerGame);
        }

        public async Task<(string bbrefid, double rcBase24, int games, double rcBase24PerG)?> CalculateRCBase24Async(string bbrefid, int year)
        {
            // Find the hitter by bbrefid
            var hitter = await _context.Hitters.FirstOrDefaultAsync(h => h.bbrefId == bbrefid && h.Year == year);

            if (hitter == null)
            {
                return null; // No hitter found for the given bbrefid
            }

            // Define components A, B, and C for RC Base24
            double A = hitter.H + hitter.BB + hitter.HBP - hitter.CS - hitter.GIDP;
            double B = hitter.TB + 0.24 * (hitter.BB + hitter.HBP - hitter.IBB) + 0.5 * (hitter.SH + hitter.SF) + 0.62 * hitter.SB - 0.03 * hitter.SO;
            double C = hitter.AB + hitter.BB + hitter.HBP + hitter.SH + hitter.SF;

            // Calculate Runs Created (RC Base24)
            double rcBase24 = C > 0 ? (A * B) / C : 0.0;
            int games = hitter.G;
            double rcBase24PerG = games > 0 ? rcBase24 / games : 0.0;

            return (bbrefid, rcBase24, games, rcBase24PerG);
        }
        
        public async Task<(string bbrefid, double BasicRC, int games, double BasicRCPerG)?> CalculateBasicRCAsync(string bbrefid, int year)
        {
            // Find the hitter by bbrefid
            var hitter = await _context.Hitters.FirstOrDefaultAsync(h => h.bbrefId == bbrefid && h.Year == year);

            if (hitter == null)
            {
                return null; // No hitter found for the given bbrefid
            }
            int singles = hitter.H - hitter.Doubles - hitter.Triples - hitter.HR;
            // Define components A, B, and C for RC Base24
            double A = hitter.H + hitter.BB;
            double B = singles + (2 * hitter.Doubles) + (3 * hitter.Triples) + (4 * hitter.HR);
            double C = hitter.AB + hitter.BB;

            // Calculate Runs Created (RC Base24)
            double BasicRC = C > 0 ? (A * B) / C : 0.0;
            int games = hitter.G;
            double BasicRCPerG = games > 0 ? BasicRC / games : 0.0;

            return (bbrefid, BasicRC, games, BasicRCPerG);
        }

        public async Task<(string bbrefid, double TechRC, int games, double TechRCPerG)?> CalculateTechRCAsync(string bbrefid, int year)
        {
            // Find the hitter by bbrefid
            var hitter = await _context.Hitters.FirstOrDefaultAsync(h => h.bbrefId == bbrefid && h.Year == year);

            if (hitter == null)
            {
                return null; // No hitter found for the given bbrefid
            }
            int singles = hitter.H - hitter.Doubles - hitter.Triples - hitter.HR;
            // Define components A, B, and C for RC Base24
            double A = (hitter.H + hitter.BB - hitter.CS + hitter.HBP - hitter.GIDP);
            double B = (singles + (2 * hitter.Doubles) + (3 * hitter.Triples) + (4 * hitter.HR))+(.26*(hitter.BB-hitter.IBB+hitter.HBP)) + (.52 * (hitter.SH + hitter.SF + hitter.SB));
            double C = hitter.AB + hitter.BB + hitter.HBP + hitter.SH + hitter.SF;

            // Calculate Runs Created (RC Base24)
            double TechRC = C > 0 ? (A * B) / C : 0.0;
            int games = hitter.G;
            double TechRCPerG = games > 0 ? TechRC / games : 0.0;

            return (bbrefid, TechRC, games, TechRCPerG);
        }

        //*
        //*
        //*
        //above this line is all the basic calculations using only season stats as they are updated every day... below this line we start to do the same thing but we are going to be doing it via their trailing gamelog data
        //*
        //*
        //*

        // BASERUNS library.fangraphs.com/features/baseruns/
        public async Task<(string bbrefid, double bsr, int games, double bsrPerGame)?> CalculateBsRAsync(string bbrefid, int year, string Split)
        {
            // Find the hitter by bbrefid
            var hitter = await _context.TrailingGameLogSplits
                .Where(h => h.BbrefId == bbrefid && h.DateUpdated.Year == year && h.Split == Split)
                .OrderByDescending(h => h.DateUpdated)
                .FirstOrDefaultAsync();
            if (hitter == null)
            {
                return null; // No hitter found for the given bbrefid
            }

            int singles = hitter.H - (hitter.Doubles + hitter.Triples + hitter.HR);
            int tb = singles + (hitter.Doubles * 2) + (hitter.Triples * 3) + (hitter.HR * 4);

            // Define components A, B, and C for Base Runs
            double A = hitter.H + hitter.BB + hitter.HBP - (0.5 * hitter.IBB) - hitter.HR;
            double B = 0.9 * (hitter.SB - hitter.CS - hitter.GDP) + (1.4 * tb - 0.6 * hitter.H - 3 * hitter.HR + 0.1 * (hitter.BB + hitter.HBP - hitter.IBB)) * 1.1;
            double C = hitter.PA - hitter.BB - hitter.SF - hitter.SH - hitter.H + hitter.CS + hitter.GDP;
            double D = hitter.HR;

            // Calculate Base Runs (BsR)
            double bsr = ((A * B) / (B + C)) + D;

            // Calculate games played and BsR per game
            int games = hitter.G;
            double bsrPerGame = games > 0 ? bsr / games : 0.0;

            return (bbrefid, bsr, games, bsrPerGame);
        }

        public async Task<(string bbrefid, double rcBase24, int games, double rcBase24PerG)?> CalculateRCBase24Async(string bbrefid, int year, string Split)
        {
            // Find the hitter by bbrefid
            var hitter = await _context.TrailingGameLogSplits
                .Where(h => h.BbrefId == bbrefid && h.DateUpdated.Year == year && h.Split == Split)
                .OrderByDescending(h => h.DateUpdated)
                .FirstOrDefaultAsync();
            if (hitter == null)
            {
                return null; // No hitter found for the given bbrefid
            }

            int singles = hitter.H - (hitter.Doubles + hitter.Triples + hitter.HR);
            int tb = singles + (hitter.Doubles * 2) + (hitter.Triples * 3) + (hitter.HR * 4);

            // Define components A, B, and C for RC Base24
            double A = hitter.H + hitter.BB + hitter.HBP - hitter.CS - hitter.GDP;
            double B = tb + 0.24 * (hitter.BB + hitter.HBP - hitter.IBB) + 0.5 * (hitter.SH + hitter.SF) + 0.62 * hitter.SB - 0.03 * hitter.SO;
            double C = hitter.AB + hitter.BB + hitter.HBP + hitter.SH + hitter.SF;

            // Calculate Runs Created (RC Base24)
            double rcBase24 = C > 0 ? (A * B) / C : 0.0;
            int games = hitter.G;
            double rcBase24PerG = games > 0 ? rcBase24 / games : 0.0;

            return (bbrefid, rcBase24, games, rcBase24PerG);
        }

        public async Task<(string bbrefid, double BasicRC, int games, double BasicRCPerG)?> CalculateBasicRCAsync(string bbrefid, int year, string Split)
        {
            // Find the hitter by bbrefid
            var hitter = await _context.TrailingGameLogSplits
                .Where(h => h.BbrefId == bbrefid && h.DateUpdated.Year == year && h.Split == Split)
                .OrderByDescending(h => h.DateUpdated)
                .FirstOrDefaultAsync();

            if (hitter == null)
            {
                return null; // No hitter found for the given bbrefid
            }
            int singles = hitter.H - hitter.Doubles - hitter.Triples - hitter.HR;
            // Define components A, B, and C for RC Base24
            double A = hitter.H + hitter.BB;
            double B = singles + (2 * hitter.Doubles) + (3 * hitter.Triples) + (4 * hitter.HR);
            double C = hitter.AB + hitter.BB;

            // Calculate Runs Created (RC Base24)
            double BasicRC = C > 0 ? (A * B) / C : 0.0;
            int games = hitter.G;
            double BasicRCPerG = games > 0 ? BasicRC / games : 0.0;

            return (bbrefid, BasicRC, games, BasicRCPerG);
        }

        public async Task<(string bbrefid, double TechRC, int games, double TechRCPerG)?> CalculateTechRCAsync(string bbrefid, int year, string Split)
        {
            // Find the hitter by bbrefid
            var hitter = await _context.TrailingGameLogSplits
                .Where(h => h.BbrefId == bbrefid && h.DateUpdated.Year == year && h.Split == Split)
                .OrderByDescending(h => h.DateUpdated)
                .FirstOrDefaultAsync();

            if (hitter == null)
            {
                return null; // No hitter found for the given bbrefid
            }
            int singles = hitter.H - hitter.Doubles - hitter.Triples - hitter.HR;
            // Define components A, B, and C for RC Base24
            double A = (hitter.H + hitter.BB - hitter.CS + hitter.HBP - hitter.GDP);
            double B = (singles + (2 * hitter.Doubles) + (3 * hitter.Triples) + (4 * hitter.HR)) + (.26 * (hitter.BB - hitter.IBB + hitter.HBP)) + (.52 * (hitter.SH + hitter.SF + hitter.SB));
            double C = hitter.AB + hitter.BB + hitter.HBP + hitter.SH + hitter.SF;

            // Calculate Runs Created (RC Base24)
            double TechRC = C > 0 ? (A * B) / C : 0.0;
            int games = hitter.G;
            double TechRCPerG = games > 0 ? TechRC / games : 0.0;

            return (bbrefid, TechRC, games, TechRCPerG);
        }









        public async Task<(string bbrefid, double normalizedSeasonStat, double normalizedL7Stat, double nssPerG, double nL7sPerG)?> NormalizeStatAsync(string bbrefid, int year, string methodFlag)
        {
            // Find the hitter by bbrefid
            var hitterS = await _context.TrailingGameLogSplits
                .Where(h => h.BbrefId == bbrefid && h.DateUpdated.Year == year && h.Split == "Season")
                .OrderByDescending(h => h.DateUpdated)
                .FirstOrDefaultAsync();

            var hitterL7 = await _context.TrailingGameLogSplits
                .Where(h => h.BbrefId == bbrefid && h.DateUpdated.Year == year && h.Split == "Last7G")
                .OrderByDescending(h => h.DateUpdated)
                .FirstOrDefaultAsync();

            if (hitterS == null || hitterL7 == null)
            {
                return null; // No hitter found for the given bbrefid
            }
            double statToNormalize = 0;
            double statToNormalize2 = 0;

            if (methodFlag == "brc")
            {
                var result = await CalculateBasicRCAsync(bbrefid, year, "Season");
                var result2 = await CalculateBasicRCAsync(bbrefid, year, "Last7G");
                if (result.HasValue)
                {
                    statToNormalize = result.Value.BasicRC; // Extract BasicRC
                }
                if (result2.HasValue)
                {
                    statToNormalize2 = result2.Value.BasicRC; // Extract BasicRC
                }
            }
            else if (methodFlag == "trc")
            {
                var result = await CalculateTechRCAsync(bbrefid, year, "Season");
                var result2 = await CalculateTechRCAsync(bbrefid, year, "Last7G");
                if (result.HasValue)
                {
                    statToNormalize = result.Value.TechRC; // Extract TechRC
                }
                if (result2.HasValue)
                {
                    statToNormalize2 = result2.Value.TechRC; // Extract TechRC
                }
            }
            else if (methodFlag == "baseR")
            {
                var result = await CalculateBsRAsync(bbrefid, year, "Season");
                var result2 = await CalculateBsRAsync(bbrefid, year, "Last7G");
                if (result.HasValue)
                {
                    statToNormalize = result.Value.bsr; // Extract bsr
                }
                if (result2.HasValue)
                {
                    statToNormalize2 = result2.Value.bsr; // Extract bsr
                }
            }
            else if (methodFlag == "rc24")
            {
                var result = await CalculateRCBase24Async(bbrefid, year, "Season");
                var result2 = await CalculateRCBase24Async(bbrefid, year, "Last7G");
                if (result.HasValue)
                {
                    statToNormalize = result.Value.rcBase24; // Extract rcBase24
                }
                if (result2.HasValue)
                {
                    statToNormalize2 = result2.Value.rcBase24; // Extract rcBase24
                }
            }
            else
            {
                throw new ArgumentException("Invalid methodFlag provided.");
            }

            // Perform normalization
            var normalizedSeasonStat = (100.00 / hitterS.SplitParkFactor) * statToNormalize;
            var normalizedL7Stat = (100.00 / hitterL7.SplitParkFactor) * statToNormalize2;

            var nssPerG = normalizedSeasonStat / hitterS.G;
            var nL7sPerG = normalizedL7Stat / hitterL7.G;

            return (bbrefid, normalizedSeasonStat, normalizedL7Stat, nssPerG, nL7sPerG);
        }

        public double ProbabilityOfHit(double hitterBA, double pitcherBAAgainst, double leagueBA)
        {
            double numerator = (hitterBA * pitcherBAAgainst) / leagueBA;
            double denominator = numerator + ((1 - hitterBA) * (1 - pitcherBAAgainst)) / (1 - leagueBA);
            return numerator / denominator;
        }

        public double ProbabilityOfSpecificHit(double hitterRate, double pitcherRate, double leagueRate)
        {
            double numerator = (hitterRate * pitcherRate) / leagueRate;
            double denominator = numerator + ((1 - hitterRate) * (1 - pitcherRate)) / (1 - leagueRate);
            return numerator / denominator;
        }

        public double ProbabilityOfHitInXAtBats(double probabilityOfHit, int atBats)
        {
            return 1 - Math.Pow(1 - probabilityOfHit, atBats);
        }

        public async Task<HitProbabilityResult> CalculateHitProbabilities(string hitterId, string pitcherId, int year)
        {
            // Check if players exist and determine leagues
            var hitter = await _context.Hitters.FirstOrDefaultAsync(h => h.bbrefId == hitterId);
            var pitcher = await _context.Pitchers.FirstOrDefaultAsync(p => p.BbrefId == pitcherId);

            if (hitter == null || pitcher == null)
            {
                throw new Exception("Hitter or pitcher not found.");
            }

            string hitterLeague = hitter.Lg; // 'AL' or 'NL'
            string pitcherLeague = pitcher.Lg; // 'AL' or 'NL'

            // Use league to determine team names for league averages
            string leagueTeamName = hitterLeague == "AL" ? "AL Averages" : "NL Averages";

            // Query league averages
            var leaguePitching = await _context.TeamTotalPitchingTracking
                .Where(p => p.TeamName == leagueTeamName && p.Year == year)
                .OrderByDescending(p => p.DateAdded)
                .FirstOrDefaultAsync();

            var leagueBatting = await _context.TeamTotalBattingTracking
                .Where(b => b.TeamName == leagueTeamName && b.Year == year)
                .OrderByDescending(b => b.DateAdded)
                .FirstOrDefaultAsync();

            if (leaguePitching == null || leagueBatting == null)
            {
                throw new Exception("League averages not found.");
            }

            double leagueBA = (double)leagueBatting.batting_avg;
            double leagueHRRate = ((double)leagueBatting.HR / (double)leagueBatting.PA);

            // Query hitter stats (Season and Last7G)
            var seasonStats = await _context.TrailingGameLogSplits
                .Where(h => h.BbrefId == hitterId && h.Split == "Season")
                .OrderByDescending(h => h.DateUpdated)
                .FirstOrDefaultAsync();

            var last7GStats = await _context.TrailingGameLogSplits
                .Where(h => h.BbrefId == hitterId && h.Split == "Last7G")
                .OrderByDescending(h => h.DateUpdated)
                .FirstOrDefaultAsync();

            if (seasonStats == null || last7GStats == null)
            {
                throw new Exception("Hitter stats not found for both splits.");
            }

            // Blend hitter stats
            var blendedHitterStats = _blendingService.BlendHitterStats(seasonStats, last7GStats);
            double hitterBA = blendedHitterStats.BA;
            double hitterHRRate = blendedHitterStats.HR / blendedHitterStats.PA;

            // Query pitcher stats using blending service
            var blendedPitcherStats = _blendingService.BlendPitcherStatsAsync(pitcherId, year);
            if (blendedPitcherStats == null)
            {
                throw new Exception("Pitcher stats not found.");
            }

            double pitcherBAAgainst = 1.0;//blendedPitcherStats.BA;
            double pitcherHRRate = 1.0;//blendedPitcherStats.HR / blendedPitcherStats.PA;
            //------------------------------------------------------------------------------------------------------
            //clean out stats to be able to make probabilities for each then calculate probabilities of a matchup...



            // Calculate probabilities
            double hitProbability = ProbabilityOfHit(hitterBA, pitcherBAAgainst, leagueBA);
            double hrProbability = ProbabilityOfSpecificHit(hitterHRRate, pitcherHRRate, leagueHRRate);

            return new HitProbabilityResult
            {
                HitProbability = hitProbability,
                HRProbability = hrProbability,
                // Add other probabilities as needed
            };
        }


        //public async Task<HitProbabilityResult> CalculateHitProbabilities(string hitterId, string pitcherId, int year)
        //{
        //    // check if players exist... pitcher and hitter... we can look at hitters or pitchers table as there is a Lg entry in both these tables for 'NL' or 'AL'...
        //    // then depending on which lg the hitter and pitcher are in is what would dictate the teamName in the teamtotalPitchingTracking or hitting.
        //    // if the pitcher is in the AL then we would only be interested in "AL Averages" and visa versa for "NL Averages" this applies for hitter and pitchers
        //    // Query league averages
        //    var leaguePitching = await _context.TeamTotalPitchingTracking
        //        .Where(p => p.TeamName == teamName && p.Year == year)
        //        .OrderByDescending(p => p.DateAdded)  // Order by most recent
        //        .FirstOrDefaultAsync();              // Get the most recent record

        //    var leagueBatting = await _context.TeamTotalBattingTracking
        //        .Where(b => b.TeamName == teamName && b.Year == year)
        //        .OrderByDescending(b => b.DateAdded)  // Order by most recent
        //        .FirstOrDefaultAsync();

        //    double leagueBA = (double) leagueBatting.batting_avg;
        //    double leagueHRRate =(double) leagueBatting.HR / leagueBatting.PA;
        //    // ... Other league rates

        //    // Query hitter stats
        //    //we need to deal with this as well with more than just finding bbrefid. we need to actually pull the most recent entry of bbrefid = hitterid and split = Last7g and split = Season
        //    // we want to get these two rows... pass them to blendingService to get the get blended stat line between season and last7G
        //    //
        //    var hitterStats = await _context.TrailingGameLogSplits
        //        .Where(h => h.BbrefId == hitterId)
        //        .FirstOrDefaultAsync();

        //    double hitterBA = hitterStats.BA;
        //    double hitterHRRate = hitterStats.HR/hitterStats.PA;
        //    // ... Other hitter stats


        //    // Query pitcher stats needs to query more than just bbrefid we need to do bbrefid and year and split... Or we can just call on _blendingService.GetBlendingResultsForPitcher for the pitcherId
        //    // that should give us blended stats of a pitchers season and last 28 days... we can then calculate the stats from there
        //    var pitcherStats = await _context.PitcherPlatoonAndTrackRecord
        //        .Where(p => p.BbrefID == pitcherId)
        //        .FirstOrDefaultAsync();

        //    double pitcherBAAgainst = pitcherStats.BA;
        //    double pitcherHRRate = pitcherStats.HR/pitcherStats.PA;
        //    // ... Other pitcher stats

        //    // Calculate probabilities
        //    double hitProbability = ProbabilityOfHit(hitterBA, pitcherBAAgainst, leagueBA);
        //    double hrProbability = ProbabilityOfSpecificHit(hitterHRRate, pitcherHRRate, leagueHRRate);

        //    return new HitProbabilityResult
        //    {
        //        HitProbability = hitProbability,
        //        HRProbability = hrProbability,
        //        // Add other probabilities as needed
        //    };
        //}


        public async Task UpdateHitterTemperatureAsync(DateTime targetDate)
        {
            // Ensure date is in DateTime format with no time
            var date = targetDate.Date;

            // Fetch all SingleGame and SingleGame2 splits for the target date
            var gameLogs = await _context.TrailingGameLogSplits
                .Where(g => g.Split.Contains("SingleGame") && g.DateUpdated.Date == date)
                .OrderBy(g => g.Split) // Ensures SingleGame2 is processed first
                .ToListAsync();

            // Group logs by bbrefid for processing
            var groupedLogs = gameLogs.GroupBy(g => g.BbrefId);

            foreach (var group in groupedLogs)
            {
                foreach (var log in group)
                {
                    string bbrefid = log.BbrefId;
                    int year = 2024; // Assuming 2024 for consistency
                    string team = log.Team;

                    // Fetch the most recent temperature record for this player and year
                    var existingTemp = await _context.HitterTempTracking
                        .Where(t => t.BbrefId == bbrefid && t.Year == year)
                        .OrderByDescending(t => t.Date)
                        .FirstOrDefaultAsync();

                    // Initialize starting values
                    double currentTemp = existingTemp?.CurrentTemp ?? 72.0; // Default to 72 if no data
                    var trailingTemps = new List<double?>
            {
                existingTemp?.TrailingTemp1,
                existingTemp?.TrailingTemp2,
                existingTemp?.TrailingTemp3,
                existingTemp?.TrailingTemp4,
                existingTemp?.TrailingTemp5,
                existingTemp?.TrailingTemp6
            };

                    // Calculate the new temperature for each plate appearance
                    double decayFactor = 0.94;
                    for (int i = 0; i < log.PA; i++)
                    {
                        double eventValue = CalculateEventValue(log);
                        currentTemp = currentTemp * decayFactor + eventValue;
                    }

                    // Check if a row for this date already exists
                    var existingRowForDate = await _context.HitterTempTracking
                        .FirstOrDefaultAsync(t => t.BbrefId == bbrefid && t.Year == year && t.Date == date);

                    if (existingRowForDate != null)
                    {
                        // Update the existing row for this date, preserving trailing temperatures
                        trailingTemps.Insert(0, existingRowForDate.CurrentTemp);
                        trailingTemps = trailingTemps.Take(6).ToList();

                        existingRowForDate.CurrentTemp = currentTemp;
                        existingRowForDate.TrailingTemp1 = trailingTemps.ElementAtOrDefault(0);
                        existingRowForDate.TrailingTemp2 = trailingTemps.ElementAtOrDefault(1);
                        existingRowForDate.TrailingTemp3 = trailingTemps.ElementAtOrDefault(2);
                        existingRowForDate.TrailingTemp4 = trailingTemps.ElementAtOrDefault(3);
                        existingRowForDate.TrailingTemp5 = trailingTemps.ElementAtOrDefault(4);
                        existingRowForDate.TrailingTemp6 = trailingTemps.ElementAtOrDefault(5);
                    }
                    else
                    {
                        // Create a new temperature record
                        trailingTemps.Insert(0, existingTemp?.CurrentTemp ?? 72.0);
                        trailingTemps = trailingTemps.Take(6).ToList();

                        var newTempRecord = new HitterTempTracking
                        {
                            BbrefId = bbrefid,
                            Team = team,
                            Year = year,
                            Date = date,
                            CurrentTemp = currentTemp,
                            TrailingTemp1 = trailingTemps.ElementAtOrDefault(0),
                            TrailingTemp2 = trailingTemps.ElementAtOrDefault(1),
                            TrailingTemp3 = trailingTemps.ElementAtOrDefault(2),
                            TrailingTemp4 = trailingTemps.ElementAtOrDefault(3),
                            TrailingTemp5 = trailingTemps.ElementAtOrDefault(4),
                            TrailingTemp6 = trailingTemps.ElementAtOrDefault(5)
                        };

                        _context.HitterTempTracking.Add(newTempRecord);
                    }

                    // Save changes after each log to ensure proper dependency handling for doubleheaders
                    await _context.SaveChangesAsync();
                }
            }
        }



        private double CalculateEventValue(TrailingGameLogSplit log)
        {
            // Calculate the event value based on player's stats
            int singles = log.H - (log.Doubles + log.Triples + log.HR);
            double eventValue =
                (singles * 9) +
                (log.Doubles * 11) +
                (log.Triples * 13) +
                (log.HR * 15) +
                (log.BB * 6); // Adjust scoring as necessary

            return log.PA > 0 ? eventValue / log.PA : 0; // Normalize by plate appearances
        }


    }
    public class HitProbabilityResult
    {
        public double HitProbability { get; set; }
        public double HRProbability { get; set; }
        public double SingleProbability { get; set; }
        public double DoubleProbability { get; set; }
        public double TripleProbability { get; set; }
    }

}
