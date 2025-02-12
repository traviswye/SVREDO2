using System;
using System.Collections.Generic;
using System.Linq;

namespace SharpVizApi.Services
{
    public class StackStrategy
    {
        public string Name { get; set; }
        public int PrimaryStackSize { get; set; }
        public int SecondaryStackSize { get; set; }
        public double WinRate { get; set; }
    }

    public class SlateStrategy
    {
        public string RecommendedStrategy { get; set; }
        public List<StackStrategy> AlternativeStrategies { get; set; }
        public string Reasoning { get; set; }
    }

    public interface IMLBStrategyService
    {
        SlateStrategy GetOptimalStrategy(int numberOfGames);
        List<(string Team, int StackSize)> GetStackRequirements(string strategyName);
    }

    public class MLBStrategyService : IMLBStrategyService
    {
        // Historical win rates by number of games and stack type
        private readonly Dictionary<int, Dictionary<string, double>> _winRatesBySlateSize = new()
        {
            {
                2, new Dictionary<string, double>
                {
                    { "5-3", 0.14 },
                    { "5-2", 0.19 },
                    { "5-1", 0.05 },
                    { "4-4", 0.12 },
                    { "4-3", 0.16 },
                    { "4-2", 0.23 },
                    { "3-3", 0.07 }
                }
            },
            {
                3, new Dictionary<string, double>
                {
                    { "5-3", 0.15 },
                    { "5-2", 0.15 },
                    { "5-1", 0.05 },
                    { "4-4", 0.05 },
                    { "4-3", 0.10 },
                    { "4-2", 0.08 },
                    { "3-3", 0.23 }
                }
            },
            {
                4, new Dictionary<string, double>
                {
                    { "5-3", 0.04 },
                    { "5-2", 0.20 },
                    { "5-1", 0.08 },
                    { "4-4", 0.04 },
                    { "4-3", 0.04 },
                    { "4-2", 0.12 },
                    { "3-3", 0.08 }
                }
            },
            {
                5, new Dictionary<string, double>
                {
                    { "5-3", 0.08 },
                    { "5-2", 0.32 },
                    { "5-1", 0.05 },
                    { "4-4", 0.00 },
                    { "4-3", 0.08 },
                    { "4-2", 0.08 },
                    { "3-3", 0.13 }
                }
            },
            {
                6, new Dictionary<string, double>
                {
                    { "5-3", 0.10 },
                    { "5-2", 0.46 },
                    { "5-1", 0.15 },
                    { "4-4", 0.03 },
                    { "4-3", 0.03 },
                    { "4-2", 0.05 },
                    { "3-3", 0.03 }
                }
            },
            {
                7, new Dictionary<string, double>
                {
                    { "5-3", 0.09 },
                    { "5-2", 0.20 },
                    { "5-1", 0.15 },
                    { "4-4", 0.06 },
                    { "4-3", 0.06 },
                    { "4-2", 0.09 },
                    { "3-3", 0.00 }
                }
            },
            {
                8, new Dictionary<string, double>
                {
                    { "5-3", 0.07 },
                    { "5-2", 0.21 },
                    { "5-1", 0.19 },
                    { "4-4", 0.02 },
                    { "4-3", 0.05 },
                    { "4-2", 0.12 },
                    { "3-3", 0.02 }
                }
            },
            {
                9, new Dictionary<string, double>
                {
                    { "5-3", 0.09 },
                    { "5-2", 0.31 },
                    { "5-1", 0.13 },
                    { "4-4", 0.07 },
                    { "4-3", 0.09 },
                    { "4-2", 0.07 },
                    { "3-3", 0.00 }
                }
            },
            {
                10, new Dictionary<string, double>
                {
                    { "5-3", 0.24 },
                    { "5-2", 0.21 },
                    { "5-1", 0.17 },
                    { "4-4", 0.05 },
                    { "4-3", 0.02 },
                    { "4-2", 0.05 },
                    { "3-3", 0.02 }
                }
            },
            {
                11, new Dictionary<string, double>
                {
                    { "5-3", 0.09 },
                    { "5-2", 0.14 },
                    { "5-1", 0.14 },
                    { "4-4", 0.03 },
                    { "4-3", 0.11 },
                    { "4-2", 0.11 },
                    { "3-3", 0.03 }
                }
            },
            {
                12, new Dictionary<string, double>
                {
                    { "5-3", 0.12 },
                    { "5-2", 0.15 },
                    { "5-1", 0.24 },
                    { "4-4", 0.06 },
                    { "4-3", 0.03 },
                    { "4-2", 0.12 },
                    { "3-3", 0.06 }
                }
            },
            {
                13, new Dictionary<string, double>
                {
                    { "5-3", 0.21 },
                    { "5-2", 0.18 },
                    { "5-1", 0.04 },
                    { "4-4", 0.11 },
                    { "4-3", 0.14 },
                    { "4-2", 0.04 },
                    { "3-3", 0.00 }
                }
            },
            {
                14, new Dictionary<string, double>
                {
                    { "5-3", 0.26 },
                    { "5-2", 0.22 },
                    { "5-1", 0.09 },
                    { "4-4", 0.04 },
                    { "4-3", 0.04 },
                    { "4-2", 0.13 },
                    { "3-3", 0.04 }
                }
            },
            {
                15, new Dictionary<string, double>
                {
                    { "5-3", 0.33 },
                    { "5-2", 0.19 },
                    { "5-1", 0.14 },
                    { "4-4", 0.05 },
                    { "4-3", 0.10 },
                    { "4-2", 0.10 },
                    { "3-3", 0.00 }
                }
            }
        };

        public SlateStrategy GetOptimalStrategy(int numberOfGames)
        {
            // If we don't have exact data for this slate size, find the closest
            var closestSlateSize = _winRatesBySlateSize.Keys
                .OrderBy(x => Math.Abs(x - numberOfGames))
                .First();

            var winRates = _winRatesBySlateSize[closestSlateSize];

            // Get the top strategies (those within 5 percentage points of the best)
            var bestWinRate = winRates.Max(x => x.Value);
            var viableStrategies = winRates
                .Where(x => x.Value >= bestWinRate - 0.05)
                .OrderByDescending(x => x.Value)
                .Select(x => new StackStrategy
                {
                    Name = x.Key,
                    PrimaryStackSize = int.Parse(x.Key.Split('-')[0]),
                    SecondaryStackSize = int.Parse(x.Key.Split('-')[1]),
                    WinRate = x.Value
                })
                .ToList();

            var bestStrategy = viableStrategies.First();

            return new SlateStrategy
            {
                RecommendedStrategy = bestStrategy.Name,
                AlternativeStrategies = viableStrategies.Skip(1).ToList(),
                Reasoning = $"For a {numberOfGames}-game slate{(numberOfGames != closestSlateSize ? $" (using {closestSlateSize}-game data)" : "")}, " +
                          $"the {bestStrategy.Name} stack has historically won {bestStrategy.WinRate:P0} of GPPs. " +
                          $"This strategy suggests using {bestStrategy.PrimaryStackSize} players from one team " +
                          $"and {bestStrategy.SecondaryStackSize} from another team."
            };
        }

        public List<(string Team, int StackSize)> GetStackRequirements(string strategyName)
        {
            var parts = strategyName.Split('-');
            return new List<(string Team, int StackSize)>
            {
                ("Primary", int.Parse(parts[0])),
                ("Secondary", int.Parse(parts[1]))
            };
        }
    }
}