USE [master]
GO
/****** Object:  Database [NRFI]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE DATABASE [NRFI]
 CONTAINMENT = NONE
 ON  PRIMARY 
( NAME = N'NRFI', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL15.MSSQLSERVER\MSSQL\DATA\NRFI.mdf' , SIZE = 8192KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON 
( NAME = N'NRFI_log', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL15.MSSQLSERVER\MSSQL\DATA\NRFI_log.ldf' , SIZE = 73728KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
 WITH CATALOG_COLLATION = DATABASE_DEFAULT
GO
ALTER DATABASE [NRFI] SET COMPATIBILITY_LEVEL = 150
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [NRFI].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [NRFI] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [NRFI] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [NRFI] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [NRFI] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [NRFI] SET ARITHABORT OFF 
GO
ALTER DATABASE [NRFI] SET AUTO_CLOSE OFF 
GO
ALTER DATABASE [NRFI] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [NRFI] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [NRFI] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [NRFI] SET CURSOR_DEFAULT  GLOBAL 
GO
ALTER DATABASE [NRFI] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [NRFI] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [NRFI] SET QUOTED_IDENTIFIER OFF 
GO
ALTER DATABASE [NRFI] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [NRFI] SET  DISABLE_BROKER 
GO
ALTER DATABASE [NRFI] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
GO
ALTER DATABASE [NRFI] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [NRFI] SET TRUSTWORTHY OFF 
GO
ALTER DATABASE [NRFI] SET ALLOW_SNAPSHOT_ISOLATION OFF 
GO
ALTER DATABASE [NRFI] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [NRFI] SET READ_COMMITTED_SNAPSHOT OFF 
GO
ALTER DATABASE [NRFI] SET HONOR_BROKER_PRIORITY OFF 
GO
ALTER DATABASE [NRFI] SET RECOVERY FULL 
GO
ALTER DATABASE [NRFI] SET  MULTI_USER 
GO
ALTER DATABASE [NRFI] SET PAGE_VERIFY CHECKSUM  
GO
ALTER DATABASE [NRFI] SET DB_CHAINING OFF 
GO
ALTER DATABASE [NRFI] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF ) 
GO
ALTER DATABASE [NRFI] SET TARGET_RECOVERY_TIME = 60 SECONDS 
GO
ALTER DATABASE [NRFI] SET DELAYED_DURABILITY = DISABLED 
GO
ALTER DATABASE [NRFI] SET ACCELERATED_DATABASE_RECOVERY = OFF  
GO
ALTER DATABASE [NRFI] SET QUERY_STORE = OFF
GO
USE [NRFI]
GO
/****** Object:  Schema [HangFire]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE SCHEMA [HangFire]
GO
/****** Object:  Table [dbo].[GameOdds]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[GameOdds](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[GamePreviewId] [int] NOT NULL,
	[HomeML] [nvarchar](50) NULL,
	[AwayML] [nvarchar](50) NULL,
	[F5HomeML] [nvarchar](50) NULL,
	[F5AwayML] [nvarchar](50) NULL,
	[OverUnder] [nvarchar](10) NULL,
	[F5OverUnder] [nvarchar](10) NULL,
	[OddsLink] [nvarchar](255) NULL,
	[PreviewLink] [nvarchar](255) NOT NULL,
	[DateModified] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[gamePreviews]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[gamePreviews](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[Date] [date] NOT NULL,
	[Time] [nvarchar](50) NOT NULL,
	[HomeTeam] [nvarchar](100) NOT NULL,
	[AwayTeam] [nvarchar](100) NOT NULL,
	[Venue] [nvarchar](100) NOT NULL,
	[HomePitcher] [nvarchar](50) NULL,
	[AwayPitcher] [nvarchar](50) NULL,
	[PreviewLink] [nvarchar](255) NULL,
	[DateModified] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[gameResults]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[gameResults](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[GamePreviewId] [int] NULL,
	[HomeTeamScore] [int] NOT NULL,
	[AwayTeamScore] [int] NOT NULL,
	[GameResult] [nvarchar](50) NOT NULL,
	[WinningPitcher] [nvarchar](50) NULL,
	[LosingPitcher] [nvarchar](50) NULL,
	[NRFI] [bit] NOT NULL,
	[F5Score] [nvarchar](10) NULL,
	[F5Result] [nvarchar](50) NULL,
	[OUResult] [nvarchar](10) NULL,
	[DateModified] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[NRFIrecords2024]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[NRFIrecords2024](
	[Team] [nvarchar](100) NULL,
	[NRFIRecord] [nvarchar](50) NULL,
	[Home] [nvarchar](50) NULL,
	[Away] [nvarchar](50) NULL,
	[RunsPerFirst] [float] NULL,
	[LastGame] [int] NULL,
	[RunsAtHome] [float] NULL,
	[RunsAtAway] [float] NULL,
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[DateModified] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ParkFactors]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ParkFactors](
	[Team] [nvarchar](100) NULL,
	[Venue] [nvarchar](100) NULL,
	[Year] [int] NULL,
	[ParkFactorRating] [int] NULL,
	[wOBACon] [int] NULL,
	[BACON] [int] NULL,
	[R] [int] NULL,
	[OBP] [int] NULL,
	[H] [int] NULL,
	[1B] [int] NULL,
	[2B] [int] NULL,
	[3B] [int] NULL,
	[HR] [int] NULL,
	[BB] [int] NULL,
	[SO] [int] NULL,
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[zipcode] [nvarchar](10) NULL,
	[RoofType] [nvarchar](50) NULL,
PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Pitcher1stInning]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Pitcher1stInning](
	[bbrefID] [nvarchar](50) NOT NULL,
	[G] [int] NOT NULL,
	[IP] [real] NOT NULL,
	[ER] [int] NOT NULL,
	[ERA] [real] NOT NULL,
	[PA] [int] NOT NULL,
	[AB] [int] NOT NULL,
	[R] [int] NOT NULL,
	[H] [int] NOT NULL,
	[2B] [int] NOT NULL,
	[3B] [int] NOT NULL,
	[HR] [int] NOT NULL,
	[SB] [int] NOT NULL,
	[CS] [int] NOT NULL,
	[BB] [int] NOT NULL,
	[SO] [int] NOT NULL,
	[SO_W] [real] NOT NULL,
	[BA] [real] NOT NULL,
	[OBP] [real] NOT NULL,
	[SLG] [real] NOT NULL,
	[OPS] [real] NOT NULL,
	[TB] [int] NOT NULL,
	[GDP] [int] NOT NULL,
	[HBP] [int] NOT NULL,
	[SH] [int] NOT NULL,
	[SF] [int] NOT NULL,
	[IBB] [int] NOT NULL,
	[ROE] [int] NOT NULL,
	[BAbip] [real] NOT NULL,
	[tOPSPlus] [int] NOT NULL,
	[sOPSPlus] [int] NOT NULL,
	[DateModified] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[bbrefID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Pitchers]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Pitchers](
	[bbrefID] [nvarchar](50) NOT NULL,
	[Year] [int] NOT NULL,
	[Age] [int] NOT NULL,
	[Team] [nvarchar](50) NOT NULL,
	[Lg] [nvarchar](5) NOT NULL,
	[WL] [nvarchar](10) NOT NULL,
	[WLPercentage] [real] NOT NULL,
	[ERA] [real] NOT NULL,
	[G] [int] NOT NULL,
	[GS] [int] NOT NULL,
	[GF] [int] NOT NULL,
	[CG] [int] NOT NULL,
	[SHO] [int] NOT NULL,
	[SV] [int] NOT NULL,
	[IP] [real] NOT NULL,
	[H] [int] NOT NULL,
	[R] [int] NOT NULL,
	[ER] [int] NOT NULL,
	[HR] [int] NOT NULL,
	[BB] [int] NOT NULL,
	[IBB] [int] NOT NULL,
	[SO] [int] NOT NULL,
	[HBP] [int] NOT NULL,
	[BK] [int] NOT NULL,
	[WP] [int] NOT NULL,
	[BF] [int] NOT NULL,
	[ERAPlus] [int] NOT NULL,
	[FIP] [real] NOT NULL,
	[WHIP] [real] NOT NULL,
	[H9] [real] NOT NULL,
	[HR9] [real] NOT NULL,
	[BB9] [real] NOT NULL,
	[SO9] [real] NOT NULL,
	[SOW] [real] NOT NULL,
	[DateModified] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[bbrefID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[TeamSplits]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[TeamSplits](
	[Team] [nvarchar](100) NULL,
	[Wins] [int] NULL,
	[Losses] [int] NULL,
	[L10] [nvarchar](50) NULL,
	[L20] [nvarchar](50) NULL,
	[L30] [nvarchar](50) NULL,
	[HomeRec] [nvarchar](50) NULL,
	[AwayRec] [nvarchar](50) NULL,
	[ExtRec] [nvarchar](50) NULL,
	[vsRHP] [nvarchar](50) NULL,
	[vsLHP] [nvarchar](50) NULL,
	[vsInterLeague] [nvarchar](50) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[AggregatedCounter]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[AggregatedCounter](
	[Key] [nvarchar](100) NOT NULL,
	[Value] [bigint] NOT NULL,
	[ExpireAt] [datetime] NULL,
 CONSTRAINT [PK_HangFire_CounterAggregated] PRIMARY KEY CLUSTERED 
(
	[Key] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[Counter]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[Counter](
	[Key] [nvarchar](100) NOT NULL,
	[Value] [int] NOT NULL,
	[ExpireAt] [datetime] NULL,
	[Id] [bigint] IDENTITY(1,1) NOT NULL,
 CONSTRAINT [PK_HangFire_Counter] PRIMARY KEY CLUSTERED 
(
	[Key] ASC,
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[Hash]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[Hash](
	[Key] [nvarchar](100) NOT NULL,
	[Field] [nvarchar](100) NOT NULL,
	[Value] [nvarchar](max) NULL,
	[ExpireAt] [datetime2](7) NULL,
 CONSTRAINT [PK_HangFire_Hash] PRIMARY KEY CLUSTERED 
(
	[Key] ASC,
	[Field] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = ON, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[Job]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[Job](
	[Id] [bigint] IDENTITY(1,1) NOT NULL,
	[StateId] [bigint] NULL,
	[StateName] [nvarchar](20) NULL,
	[InvocationData] [nvarchar](max) NOT NULL,
	[Arguments] [nvarchar](max) NOT NULL,
	[CreatedAt] [datetime] NOT NULL,
	[ExpireAt] [datetime] NULL,
 CONSTRAINT [PK_HangFire_Job] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[JobParameter]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[JobParameter](
	[JobId] [bigint] NOT NULL,
	[Name] [nvarchar](40) NOT NULL,
	[Value] [nvarchar](max) NULL,
 CONSTRAINT [PK_HangFire_JobParameter] PRIMARY KEY CLUSTERED 
(
	[JobId] ASC,
	[Name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[JobQueue]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[JobQueue](
	[Id] [bigint] IDENTITY(1,1) NOT NULL,
	[JobId] [bigint] NOT NULL,
	[Queue] [nvarchar](50) NOT NULL,
	[FetchedAt] [datetime] NULL,
 CONSTRAINT [PK_HangFire_JobQueue] PRIMARY KEY CLUSTERED 
(
	[Queue] ASC,
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[List]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[List](
	[Id] [bigint] IDENTITY(1,1) NOT NULL,
	[Key] [nvarchar](100) NOT NULL,
	[Value] [nvarchar](max) NULL,
	[ExpireAt] [datetime] NULL,
 CONSTRAINT [PK_HangFire_List] PRIMARY KEY CLUSTERED 
(
	[Key] ASC,
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[Schema]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[Schema](
	[Version] [int] NOT NULL,
 CONSTRAINT [PK_HangFire_Schema] PRIMARY KEY CLUSTERED 
(
	[Version] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[Server]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[Server](
	[Id] [nvarchar](200) NOT NULL,
	[Data] [nvarchar](max) NULL,
	[LastHeartbeat] [datetime] NOT NULL,
 CONSTRAINT [PK_HangFire_Server] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[Set]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[Set](
	[Key] [nvarchar](100) NOT NULL,
	[Score] [float] NOT NULL,
	[Value] [nvarchar](256) NOT NULL,
	[ExpireAt] [datetime] NULL,
 CONSTRAINT [PK_HangFire_Set] PRIMARY KEY CLUSTERED 
(
	[Key] ASC,
	[Value] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = ON, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [HangFire].[State]    Script Date: 8/12/2024 12:30:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [HangFire].[State](
	[Id] [bigint] IDENTITY(1,1) NOT NULL,
	[JobId] [bigint] NOT NULL,
	[Name] [nvarchar](20) NOT NULL,
	[Reason] [nvarchar](100) NULL,
	[CreatedAt] [datetime] NOT NULL,
	[Data] [nvarchar](max) NULL,
 CONSTRAINT [PK_HangFire_State] PRIMARY KEY CLUSTERED 
(
	[JobId] ASC,
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Index [IX_HangFire_AggregatedCounter_ExpireAt]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_AggregatedCounter_ExpireAt] ON [HangFire].[AggregatedCounter]
(
	[ExpireAt] ASC
)
WHERE ([ExpireAt] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_HangFire_Hash_ExpireAt]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_Hash_ExpireAt] ON [HangFire].[Hash]
(
	[ExpireAt] ASC
)
WHERE ([ExpireAt] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_HangFire_Job_ExpireAt]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_Job_ExpireAt] ON [HangFire].[Job]
(
	[ExpireAt] ASC
)
INCLUDE([StateName]) 
WHERE ([ExpireAt] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_HangFire_Job_StateName]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_Job_StateName] ON [HangFire].[Job]
(
	[StateName] ASC
)
WHERE ([StateName] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_HangFire_List_ExpireAt]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_List_ExpireAt] ON [HangFire].[List]
(
	[ExpireAt] ASC
)
WHERE ([ExpireAt] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_HangFire_Server_LastHeartbeat]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_Server_LastHeartbeat] ON [HangFire].[Server]
(
	[LastHeartbeat] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_HangFire_Set_ExpireAt]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_Set_ExpireAt] ON [HangFire].[Set]
(
	[ExpireAt] ASC
)
WHERE ([ExpireAt] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_HangFire_Set_Score]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_Set_Score] ON [HangFire].[Set]
(
	[Key] ASC,
	[Score] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_HangFire_State_CreatedAt]    Script Date: 8/12/2024 12:30:02 AM ******/
CREATE NONCLUSTERED INDEX [IX_HangFire_State_CreatedAt] ON [HangFire].[State]
(
	[CreatedAt] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
ALTER TABLE [dbo].[GameOdds] ADD  DEFAULT (getdate()) FOR [DateModified]
GO
ALTER TABLE [dbo].[gamePreviews] ADD  DEFAULT (getdate()) FOR [DateModified]
GO
ALTER TABLE [dbo].[gameResults] ADD  DEFAULT (getdate()) FOR [DateModified]
GO
ALTER TABLE [dbo].[NRFIrecords2024] ADD  DEFAULT (getdate()) FOR [DateModified]
GO
ALTER TABLE [dbo].[Pitcher1stInning] ADD  DEFAULT (getdate()) FOR [DateModified]
GO
ALTER TABLE [dbo].[Pitchers] ADD  DEFAULT (getdate()) FOR [DateModified]
GO
ALTER TABLE [dbo].[GameOdds]  WITH CHECK ADD FOREIGN KEY([GamePreviewId])
REFERENCES [dbo].[gamePreviews] ([Id])
GO
ALTER TABLE [dbo].[gameResults]  WITH CHECK ADD FOREIGN KEY([GamePreviewId])
REFERENCES [dbo].[gamePreviews] ([Id])
GO
ALTER TABLE [HangFire].[JobParameter]  WITH CHECK ADD  CONSTRAINT [FK_HangFire_JobParameter_Job] FOREIGN KEY([JobId])
REFERENCES [HangFire].[Job] ([Id])
ON UPDATE CASCADE
ON DELETE CASCADE
GO
ALTER TABLE [HangFire].[JobParameter] CHECK CONSTRAINT [FK_HangFire_JobParameter_Job]
GO
ALTER TABLE [HangFire].[State]  WITH CHECK ADD  CONSTRAINT [FK_HangFire_State_Job] FOREIGN KEY([JobId])
REFERENCES [HangFire].[Job] ([Id])
ON UPDATE CASCADE
ON DELETE CASCADE
GO
ALTER TABLE [HangFire].[State] CHECK CONSTRAINT [FK_HangFire_State_Job]
GO
USE [master]
GO
ALTER DATABASE [NRFI] SET  READ_WRITE 
GO
