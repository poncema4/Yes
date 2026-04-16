-- config.lua — LuaShield runtime configuration
-- Edit these values to customize behavior

return {
    -- Max hits to show in the HTML report table
    max_report_hits = 200,

    -- Minimum severity to include in report: LOW | MEDIUM | HIGH | CRITICAL
    min_severity = "LOW",

    -- Output directory for reports (relative to project root)
    reports_dir = "reports",

    -- Whether to print each hit to the terminal during analysis
    verbose = false,
}
