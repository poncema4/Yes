-- analyzer.lua — Runs detection rules against parsed events, aggregates results

local M = {}

local SEV_WEIGHT = { CRITICAL=4, HIGH=3, MEDIUM=2, LOW=1 }

local function ip_key(event)
    return event.ip or event.source or "unknown"
end

-- Run all rules against a single event, return list of matched rule hits
local function check_event(event, ruleset)
    local hits = {}
    for _, rule in ipairs(ruleset) do
        local ok, result = pcall(rule.match, event)
        if ok and result then
            table.insert(hits, {
                rule_id     = rule.id,
                rule_name   = rule.name,
                severity    = rule.severity,
                category    = rule.category,
                description = rule.description,
                event       = event,
            })
        end
    end
    return hits
end

function M.analyze(events, ruleset)
    local all_hits    = {}
    local by_severity = {}
    local by_category = {}
    local by_rule     = {}
    local by_ip       = {}
    local timeline    = {}   -- list of { timestamp, severity, rule_name }

    for _, event in ipairs(events) do
        local hits = check_event(event, ruleset)
        for _, hit in ipairs(hits) do
            table.insert(all_hits, hit)

            -- severity counts
            by_severity[hit.severity] = (by_severity[hit.severity] or 0) + 1

            -- category counts
            by_category[hit.category] = (by_category[hit.category] or 0) + 1

            -- per-rule counts
            by_rule[hit.rule_id] = (by_rule[hit.rule_id] or 0) + 1

            -- per-IP aggregation
            local key = ip_key(event)
            if not by_ip[key] then
                by_ip[key] = { ip=key, count=0, max_sev_weight=0, max_sev="LOW", hits={} }
            end
            by_ip[key].count = by_ip[key].count + 1
            table.insert(by_ip[key].hits, hit)
            local w = SEV_WEIGHT[hit.severity] or 0
            if w > by_ip[key].max_sev_weight then
                by_ip[key].max_sev_weight = w
                by_ip[key].max_sev        = hit.severity
            end

            -- timeline entry
            if event.timestamp and event.timestamp ~= "" then
                table.insert(timeline, {
                    timestamp = event.timestamp,
                    severity  = hit.severity,
                    rule_name = hit.rule_name,
                    source    = ip_key(event),
                    line_num  = event.line_num,
                })
            end
        end
    end

    -- Sort top IPs by hit count descending
    local top_ips = {}
    for _, v in pairs(by_ip) do
        table.insert(top_ips, v)
    end
    table.sort(top_ips, function(a, b) return a.count > b.count end)

    -- Sort timeline by line number
    table.sort(timeline, function(a, b) return (a.line_num or 0) < (b.line_num or 0) end)

    return {
        hits          = all_hits,
        total         = #all_hits,
        by_severity   = by_severity,
        by_category   = by_category,
        by_rule       = by_rule,
        top_ips       = top_ips,
        timeline      = timeline,
        event_count   = #events,
    }
end

return M
