-- LuaShield | Advanced Log Analyzer & Threat Detector
-- Entry point: lua main.lua [logfile]

package.path = package.path .. ";./src/?.lua"

local analyzer = require("analyzer")
local reporter = require("reporter")
local parser   = require("parser")
local rules    = require("rules")
local utils    = require("utils")

utils.banner()

local log_file = arg[1] or "logs/sample.log"

if not utils.file_exists(log_file) then
    utils.err("Log file not found: " .. log_file)
    os.exit(1)
end

utils.info("Scanning: " .. log_file)

local events  = parser.parse(log_file)
utils.info(string.format("Parsed %d log entries", #events))

local ruleset = rules.load()
utils.info(string.format("Loaded %d detection rules", #ruleset))

local results = analyzer.analyze(events, ruleset)

utils.info(string.format(
    "Analysis complete -- %d threats found  (CRITICAL: %d  HIGH: %d  MEDIUM: %d  LOW: %d)",
    results.total,
    results.by_severity.CRITICAL or 0,
    results.by_severity.HIGH     or 0,
    results.by_severity.MEDIUM   or 0,
    results.by_severity.LOW      or 0
))

local report_path = reporter.generate(results, log_file)
utils.success("Report saved -> " .. report_path)
