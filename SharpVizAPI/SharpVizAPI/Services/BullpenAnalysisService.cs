using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;


namespace SharpVizAPI.Services
{


    public class BullpenStats
    {
        public string Team { get; set; }
        public int AvailablePitchers { get; set; }
        public int TotalG { get; set; }
        public int TotalGF { get; set; }
        public int TotalSV { get; set; }
        public double TotalIP { get; set; }
        public int TotalH { get; set; }
        public int TotalR { get; set; }
        public int TotalER { get; set; }
        public int TotalHR { get; set; }
        public int TotalBB { get; set; }
        public int TotalIBB { get; set; }
        public int TotalSO { get; set; }
        public int TotalHBP { get; set; }
        public int TotalBF { get; set; }
        public double BA { get; set; }
        public double OBP { get; set; }
        public double SLG { get; set; }
        public double OPS { get; set; }
        public double OOPS { get; set; }
    }

    public class BullpenAnalysisService
    {
        private readonly NrfidbContext _context;

        public BullpenAnalysisService(NrfidbContext context)
        {
            _context = context;
        }

        public async Task<BullpenStats> GetBullpenAnalysis(int year, string team, DateTime date)
        {
            // Step 1: Get all relief pitchers for the team
            var allReliefPitchers = await _context.Pitchers
                .Where(p => p.Team == team && p.Year == year && p.GS < 1)
                .ToListAsync();

            // Step 2: Get bullpen usage from previous day
            var previousDay = date.AddDays(-1);
            var recentlyUsedPitchers = await _context.BullpenUsage
                .Where(b => b.Team == team && b.Year == year && b.DatePitched == previousDay)
                .Select(b => b.Bbrefid)
                .ToListAsync();

            // Step 3: Check rest days for recently used pitchers
            // Step 3: Check rest days for recently used pitchers
            var unavailablePitchers = new List<string>();
            foreach (var pitcherId in recentlyUsedPitchers)
            {
                var hasZeroRestAppearances = await _context.BullpenUsage
                    .AnyAsync(b => b.Bbrefid == pitcherId && b.Team == team &&
                                   b.Year == year && b.DaysOfRest == 0);

                // If they've never pitched on 0 days rest, they're unavailable
                if (!hasZeroRestAppearances)
                {
                    unavailablePitchers.Add(pitcherId);
                }
            }

            // Step 4: Filter out unavailable pitchers
            var availablePitchers = allReliefPitchers
                .Where(p => !unavailablePitchers.Contains(p.BbrefId))
                .ToList();

            // Step 5: Calculate aggregate stats
            var stats = new BullpenStats
            {
                Team = team,
                AvailablePitchers = availablePitchers.Count,
                TotalG = availablePitchers.Sum(p => p.G),
                TotalGF = availablePitchers.Sum(p => p.GF),
                TotalSV = availablePitchers.Sum(p => p.SV),
                TotalIP = availablePitchers.Sum(p => p.IP),
                TotalH = availablePitchers.Sum(p => p.H),
                TotalR = availablePitchers.Sum(p => p.R),
                TotalER = availablePitchers.Sum(p => p.ER),
                TotalHR = availablePitchers.Sum(p => p.HR),
                TotalBB = availablePitchers.Sum(p => p.BB),
                TotalIBB = availablePitchers.Sum(p => p.IBB),
                TotalSO = availablePitchers.Sum(p => p.SO),
                TotalHBP = availablePitchers.Sum(p => p.HBP),
                TotalBF = availablePitchers.Sum(p => p.BF)
            };

            // Calculate advanced metrics
            CalculateAdvancedMetrics(stats);

            return stats;
        }

        private void CalculateAdvancedMetrics(BullpenStats stats)
        {
            // Calculate AB (At-Bats)
            int atBats = stats.TotalBF - stats.TotalBB - stats.TotalHBP;

            // Calculate BA (Batting Average)
            stats.BA = stats.TotalH / (double)atBats;

            // Calculate OBP (On-Base Percentage)
            double reachBase = stats.TotalH + stats.TotalBB + stats.TotalHBP;
            stats.OBP = reachBase / stats.TotalBF;

            // Calculate SLG using MLB average hit distribution
            int nonHRHits = stats.TotalH - stats.TotalHR;

            // Estimate hit types based on MLB averages
            double singles = Math.Round(0.70 * nonHRHits);  // 70% singles
            double doubles = Math.Round(0.20 * nonHRHits);  // 20% doubles
            double triples = Math.Round(0.02 * nonHRHits);  // 2% triples

            // Calculate total bases
            double totalBases = (singles * 1) + (doubles * 2) + (triples * 3) + (stats.TotalHR * 4);

            // Calculate SLG
            stats.SLG = totalBases / atBats;

            // Calculate OPS
            stats.OPS = stats.OBP + stats.SLG;

            // Calculate oOPS (using 1.6 multiplier for OBP)
            stats.OOPS = (1.6 * stats.OBP) + stats.SLG;
        }
    }
}
