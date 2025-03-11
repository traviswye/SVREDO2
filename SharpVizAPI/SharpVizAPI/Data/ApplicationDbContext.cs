using Microsoft.EntityFrameworkCore;
using SharpVizApi.Models;
using SharpVizAPI.Models;
using SharpVizAPI.Models.MLmodels; // Directly import the GamePreview class
// Directly import the GamePreview class

namespace SharpVizAPI.Data
{
    public class NrfidbContext : DbContext
    {
        public DbSet<ParkFactor> ParkFactors { get; set; }
        public DbSet<MLBplayer> MLBplayers { get; set; }

        public DbSet<PitcherPlatoonAndTrackRecord> PitcherPlatoonAndTrackRecord { get; set; }
        
        public DbSet<NRFIRecord2024> NRFIRecords2024 { get; set; }
        public DbSet<Pitcher> Pitchers { get; set; }
        public DbSet<Hitter> Hitters { get; set; }
        public DbSet<HitterLast7> HitterLast7 { get; set; }

        public DbSet<HitterVsPitcher> HitterVsPitchers { get; set; }
        

        public DbSet<GameResultsWithOdds> GameResultsWithOdds { get; set; }
        public DbSet<GamePreview> GamePreviews { get; set; }
        public DbSet<GameResults> GameResults { get; set; }
        public DbSet<GameOdds> GameOdds { get; set; }
        public DbSet<Pitcher1stInning> Pitcher1stInnings { get; set; }
        public DbSet<PitcherByInningStats> PitcherByInningStats { get; set; }

        public DbSet<TeamRecSplits> TeamRecSplits { get; set; }
        public DbSet<TeamSplits> TeamSplits { get; set; }

        public DbSet<PitchingAverage> PitchingAverages { get; set; }
        public DbSet<PitcherHomeAwaySplits> PitcherHomeAwaySplits { get; set; }

        
        public DbSet<Lineup> Lineups { get; set; }
        public DbSet<ActualLineup> ActualLineups { get; set; }

        public DbSet<LineupPrediction> LineupPredictions { get; set; }

        public DbSet<Injury> Injuries { get; set; }
        public DbSet<HittersTrailingGamelog> HittersTrailingGamelogs { get; set; }//replaced with trailinggamelogsplit
        public DbSet<TrailingGameLogSplit> TrailingGameLogSplits { get; set; }
        public DbSet<HitterTempTracking> HitterTempTracking { get; set; }

        public DbSet<BullpenUsage> BullpenUsage { get; set; }
        public DbSet<DKPlayerPool> DKPlayerPools { get; set; }

        //ML model

        public DbSet<ML_Games> ML_Games { get; set; }
        public DbSet<ML_Ballparks> ML_Ballparks { get; set; }
        public DbSet<ML_Teams> ML_Teams { get; set; }
        public DbSet<ML_Players> ML_Players { get; set; }
        public DbSet<ML_Weather> ML_Weather { get; set; }
        public DbSet<ML_Lineups> ML_Lineups { get; set; }
        public DbSet<ML_PitchingStats> ML_PitchingStats { get; set; }
        public DbSet<ML_BoxScores> ML_BoxScores { get; set; }
        public DbSet<PlayerIDMapping> PlayerIDMappings { get; set; }

        public DbSet<TeamTemperatureTracking> TeamTemperatureTrackings { get; set; }
        

        public DbSet<TeamRecSplitsArchive> TeamRecSplitsArchive { get; set; }

        public DbSet<TeamTotalBattingTracking> TeamTotalBattingTracking { get; set; }
        public DbSet<TeamTotalPitchingTracking> TeamTotalPitchingTracking { get; set; }

        public DbSet<PlayerLookup> PlayerLookup { get; set; }
        public DbSet<DKPoolsMap> DKPoolsMaps { get; set; }
        
        public NrfidbContext(DbContextOptions<NrfidbContext> options)
            : base(options)
        {
        }


        public override int SaveChanges(bool acceptAllChangesOnSuccess)
        {
            UpdateDateModified();
            return base.SaveChanges(acceptAllChangesOnSuccess);
        }

        public override Task<int> SaveChangesAsync(bool acceptAllChangesOnSuccess, CancellationToken cancellationToken = default)
        {
            UpdateDateModified();
            return base.SaveChangesAsync(acceptAllChangesOnSuccess, cancellationToken);
        }

        private void UpdateDateModified()
        {
            var entries = ChangeTracker.Entries()
                .Where(e => e.Entity is NRFIRecord2024 && (e.State == EntityState.Modified));

            foreach (var entityEntry in entries)
            {
                ((NRFIRecord2024)entityEntry.Entity).DateModified = DateTime.Now;
            }
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            // Existing configurations
            modelBuilder.Entity<ParkFactor>().HasKey(p => new { p.Venue, p.Year });
            modelBuilder.Entity<NRFIRecord2024>()
                .HasKey(n => new { n.Team, n.Year }); // Composite primary key: Team + Year

            modelBuilder.Entity<Pitcher1stInning>()
                .HasKey(p => new { p.BbrefId, p.Year });

            // Configure BbrefId as the primary key for the Pitcher entity
            modelBuilder.Entity<Pitcher>().HasKey(p => p.BbrefId);
            modelBuilder.Entity<TeamSplits>().ToTable("TeamSplits");
            modelBuilder.Entity<TeamSplits>()
                .HasKey(ts => ts.Team); // Specify that Team is the primary key
                                        // Other configurations if needed

            modelBuilder.Entity<PitcherHomeAwaySplits>()
                .HasKey(p => new { p.bbrefID, p.Year, p.Split });

            modelBuilder.Entity<PitcherByInningStats>()
                .HasKey(p => new { p.BbrefId, p.Inning, p.Year });


            modelBuilder.Entity<PitcherPlatoonAndTrackRecord>()
                .HasKey(p => new { p.BbrefID, p.Year, p.Split });
            modelBuilder.Entity<HitterLast7>().ToTable("HitterLast7");

            modelBuilder.Entity<TeamTemperatureTracking>()
                .ToTable("TeamTemperatureTracking") // Specify the exact table name in the database
                .HasKey(tt => new { tt.Team, tt.Year, tt.Date, tt.GameNumber });
            // GameOdds Entity
            modelBuilder.Entity<GameOdds>()
                .HasKey(go => go.Id);  // Primary key

            modelBuilder.Entity<GameOdds>()
                .HasOne(go => go.GamePreview)
                .WithMany()  // Assuming there is no navigation property in GamePreview
                .HasForeignKey(go => go.GamePreviewID)
                .OnDelete(DeleteBehavior.Cascade);  // Foreign key with cascade delete

            modelBuilder.Entity<TeamTotalBattingTracking>()
                .HasKey(t => new { t.TeamName, t.Year, t.DateAdded });
            modelBuilder.Entity<TeamTotalPitchingTracking>()
                .HasKey(t => new { t.TeamName, t.Year, t.DateAdded });
            modelBuilder.Entity<HitterTempTracking>()
                .HasKey(ht => new { ht.BbrefId, ht.Year, ht.Date }); // Composite Primary Key

            modelBuilder.Entity<PlayerLookup>()
                .HasKey(pl => new { pl.BbrefId, pl.BsID });


            // GameResults Entity
            modelBuilder.Entity<GameResults>()
                .HasKey(gr => gr.Id);  // Primary key
            modelBuilder.Entity<TrailingGameLogSplit>()
                .HasKey(t => new { t.BbrefId, t.Split, t.DateUpdated });
            //modelBuilder.Entity<GameResults>()
            //    .HasOne(gr => gr.GamePreview)
            //    .WithMany()  // Assuming there is no navigation property in GamePreview
            //    .HasForeignKey(gr => gr.GamePreviewID)
            //    .OnDelete(DeleteBehavior.Cascade);  // Foreign key with cascade delete

            //modelBuilder.Entity<GameResults>()
            //    .HasOne(gr => gr.GameOdds)
            //    .WithMany()  // Assuming there is no navigation property in GameOdds
            //    .HasForeignKey(gr => gr.OddsID)
            //    .OnDelete(DeleteBehavior.Cascade);  // Foreign key with cascade delete





            //ML SIDE



            modelBuilder.Entity<ParkFactor>(entity =>
            {
                entity.HasKey(pf => new { pf.Venue, pf.Year });  // Composite primary key
            });

            modelBuilder.Entity<ParkFactor>(entity =>
            {
                entity.HasKey(pf => new { pf.Venue, pf.Year });  // Composite primary key
            });
            // Explicitly map the HitterVsPitcher model to the correct table name
            modelBuilder.Entity<HitterVsPitcher>().ToTable("HitterVsPitcher");

            // ML_Games configuration
            modelBuilder.Entity<ML_Games>(entity =>
            {
                entity.HasKey(e => e.GameID);

                // Define one-to-one relationship with ML_Weather
                entity.HasOne(e => e.Weather)
                      .WithOne(e => e.Game)
                      .HasForeignKey<ML_Weather>(e => e.GameID);  // Specify the foreign key
            });

            // ML_BoxScores configuration
            modelBuilder.Entity<ML_BoxScores>(entity =>
            {
                entity.HasKey(e => e.BoxScoreID);
            });

            // ML_Lineups configuration
            modelBuilder.Entity<ML_Lineups>(entity =>
            {
                entity.HasKey(e => e.LineupID);
            });

            // ML_PitchingStats configuration
            modelBuilder.Entity<ML_PitchingStats>(entity =>
            {
                entity.HasKey(e => e.PitchingID);
            });

            // ML_Players configuration
            modelBuilder.Entity<ML_Players>(entity =>
            {
                entity.HasKey(e => e.PlayerID);
            });

            // ML_Teams configuration
            modelBuilder.Entity<ML_Teams>(entity =>
            {
                entity.HasKey(e => e.TeamID);
            });

            // ML_Weather configuration
            modelBuilder.Entity<ML_Weather>(entity =>
            {
                entity.HasKey(e => e.WeatherID);

                // Define one-to-one relationship with ML_Games
                entity.HasOne(e => e.Game)
                      .WithOne(e => e.Weather)
                      .HasForeignKey<ML_Weather>(e => e.GameID);  // Specify the foreign key
            });


            // HittersTrailingGamelog configuration
            modelBuilder.Entity<HittersTrailingGamelog>()
                .ToTable("HittersTrailingGamelog") // Specify the exact table name in the database
                .HasKey(htg => new { htg.BbrefId, htg.Date }); // Primary key is BbrefId and Date

            modelBuilder.Entity<BullpenUsage>()
                .HasKey(b => new { b.Bbrefid, b.TeamGameNumber });
        }
    }
}