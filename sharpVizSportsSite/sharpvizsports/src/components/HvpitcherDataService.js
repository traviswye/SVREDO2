/**
 * HvpDataService.js
 * Service to handle parsing and processing Hitter vs Pitcher data
 */

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

    // Loop through all game entries
    apiResponse.forEach(item => {
        if (!item.game || !item.game.pitcher || !item.game.hitters) return;

        // Find data related to our pitchers
        if (item.game.pitcher === awayPitcherId) {
            // This represents home hitters vs away pitcher
            result.homeHittersVsAwayPitcher = item.game.hitters.map(h => ({
                hitter: h.hitter,
                pa: h.stats.pa,
                h: h.stats.h, // we keep both h and hits for compatibility
                hits: h.stats.h,
                hr: h.stats.hr,
                rbi: h.stats.rbi,
                bb: h.stats.bb,
                so: h.stats.so,
                ba: h.stats.ba,
                obp: h.stats.obp,
                slg: h.stats.slg,
                ops: h.stats.ops
            }));
        } else if (item.game.pitcher === homePitcherId) {
            // This represents away hitters vs home pitcher
            result.awayHittersVsHomePitcher = item.game.hitters.map(h => ({
                hitter: h.hitter,
                pa: h.stats.pa,
                h: h.stats.h,
                hits: h.stats.h, // we keep both for compatibility
                hr: h.stats.hr,
                rbi: h.stats.rbi,
                bb: h.stats.bb,
                so: h.stats.so,
                ba: h.stats.ba,
                obp: h.stats.obp,
                slg: h.stats.slg,
                ops: h.stats.ops
            }));
        }
    });

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