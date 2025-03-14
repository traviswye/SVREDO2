/**
 * Process the raw API response from hitter vs pitcher endpoint
 * @param {Array} apiResponse - The raw response from the API
 * @param {string} homePitcherId - The ID of the home pitcher
 * @param {string} awayPitcherId - The ID of the away pitcher
 * @returns {Object} Processed data with home and away hitters organized
 */
export const processHvpData = (apiResponse, homePitcherId, awayPitcherId) => {
    // Initialize result object
    const result = {
        homeHittersVsAwayPitcher: [],
        awayHittersVsHomePitcher: []
    };

    if (!apiResponse || !Array.isArray(apiResponse)) {
        console.error("Invalid HVP API response format:", apiResponse);
        return result;
    }

    // The API returns a flat array of matchups, each with a pitcher and hitter
    // We need to filter by pitcher ID and organize them

    // Get all matchups for away pitcher (these will be home hitters vs away pitcher)
    const homeHitterMatchups = apiResponse.filter(item =>
        item.pitcher === awayPitcherId
    );

    // Get all matchups for home pitcher (these will be away hitters vs home pitcher)
    const awayHitterMatchups = apiResponse.filter(item =>
        item.pitcher === homePitcherId
    );

    // Transform into expected format
    result.homeHittersVsAwayPitcher = homeHitterMatchups.map(item => ({
        hitter: item.hitter,
        pa: item.pa,
        h: item.hits, // Map to both for compatibility
        hits: item.hits,
        hr: item.hr,
        rbi: item.rbi,
        bb: item.bb,
        so: item.so,
        ba: item.ba,
        obp: item.obp,
        slg: item.slg,
        ops: item.ops
    }));

    result.awayHittersVsHomePitcher = awayHitterMatchups.map(item => ({
        hitter: item.hitter,
        pa: item.pa,
        h: item.hits, // Map to both for compatibility
        hits: item.hits,
        hr: item.hr,
        rbi: item.rbi,
        bb: item.bb,
        so: item.so,
        ba: item.ba,
        obp: item.obp,
        slg: item.slg,
        ops: item.ops
    }));

    console.log(`Found ${result.homeHittersVsAwayPitcher.length} home hitters vs ${awayPitcherId}`);
    console.log(`Found ${result.awayHittersVsHomePitcher.length} away hitters vs ${homePitcherId}`);

    return result;
};

/**
 * Formats a numeric value as a baseball batting average (e.g., .324)
 * @param {number} value - The numeric value to format
 * @returns {string} The formatted batting average
 */
export const formatBattingAvg = (value) => {
    if (value === undefined || value === null) return ".000";
    return value.toFixed(3).toString().replace(/^0\./, ".");
};