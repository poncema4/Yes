-- reporter.lua — Generates a self-contained HTML threat report

local M = {}

local utils = require("utils")

-- -------------------------------------------------------------------------
-- Severity styling
-- -------------------------------------------------------------------------
local SEV_COLOR = {
    CRITICAL = "#ff3b3b",
    HIGH     = "#ff8c00",
    MEDIUM   = "#f5c400",
    LOW      = "#4caf50",
}

local SEV_BG = {
    CRITICAL = "#2a0a0a",
    HIGH     = "#2a1800",
    MEDIUM   = "#2a2200",
    LOW      = "#0a1f0a",
}

local CAT_ICON = {
    brute_force = "BF",
    injection   = "INJ",
    recon       = "REC",
    malware     = "MAL",
    exfil       = "EXF",
    auth        = "AUTH",
    anomaly     = "ANO",
}

-- -------------------------------------------------------------------------
-- HTML helpers
-- -------------------------------------------------------------------------
local function esc(s)
    if type(s) ~= "string" then s = tostring(s or "") end
    s = s:gsub("&", "&amp;")
    s = s:gsub("<", "&lt;")
    s = s:gsub(">", "&gt;")
    s = s:gsub('"', "&quot;")
    return s
end

local function sev_badge(sev)
    local col = SEV_COLOR[sev] or "#888"
    local bg  = SEV_BG[sev]   or "#1a1a1a"
    return string.format(
        '<span class="badge" style="color:%s;background:%s;border:1px solid %s">%s</span>',
        col, bg, col, esc(sev)
    )
end

local function cat_pill(cat)
    local icon = CAT_ICON[cat] or cat:upper()
    return string.format('<span class="pill">%s</span>', esc(icon))
end

-- -------------------------------------------------------------------------
-- Section builders
-- -------------------------------------------------------------------------
local function build_summary_cards(results)
    local total  = results.total
    local ev     = results.event_count
    local bysev  = results.by_severity
    local cards  = {}

    local function card(label, value, color)
        table.insert(cards, string.format([[
        <div class="card">
            <div class="card-value" style="color:%s">%s</div>
            <div class="card-label">%s</div>
        </div>]], color or "#e0e0e0", esc(tostring(value)), esc(label)))
    end

    card("Log Entries Parsed", ev,                          "#7eb8f7")
    card("Total Threats",      total,                       total > 0 and "#ff6b6b" or "#4caf50")
    card("Critical",           bysev.CRITICAL or 0,         SEV_COLOR.CRITICAL)
    card("High",               bysev.HIGH     or 0,         SEV_COLOR.HIGH)
    card("Medium",             bysev.MEDIUM   or 0,         SEV_COLOR.MEDIUM)
    card("Low",                bysev.LOW      or 0,         SEV_COLOR.LOW)

    return '<div class="cards">' .. table.concat(cards, "\n") .. "</div>"
end

local function build_category_table(by_category)
    if not next(by_category) then
        return '<p class="muted">No categories triggered.</p>'
    end
    local rows = {}
    -- Sort by count desc
    local list = {}
    for k, v in pairs(by_category) do table.insert(list, {k, v}) end
    table.sort(list, function(a, b) return a[2] > b[2] end)

    for _, pair in ipairs(list) do
        local cat, count = pair[1], pair[2]
        local pct = math.floor((count / math.max(list[1][2], 1)) * 100)
        table.insert(rows, string.format([[
        <tr>
            <td>%s %s</td>
            <td>%d</td>
            <td><div class="bar-wrap"><div class="bar" style="width:%d%%"></div></div></td>
        </tr>]], cat_pill(cat), esc(cat), count, pct))
    end
    return string.format([[
    <table>
        <thead><tr><th>Category</th><th>Hits</th><th>Relative Volume</th></tr></thead>
        <tbody>%s</tbody>
    </table>]], table.concat(rows, "\n"))
end

local function build_top_ips(top_ips)
    if #top_ips == 0 then
        return '<p class="muted">No source IPs detected.</p>'
    end
    local rows = {}
    local limit = math.min(#top_ips, 10)
    for i = 1, limit do
        local entry = top_ips[i]
        table.insert(rows, string.format([[
        <tr>
            <td><code>%s</code></td>
            <td>%d</td>
            <td>%s</td>
        </tr>]], esc(entry.ip), entry.count, sev_badge(entry.max_sev)))
    end
    return string.format([[
    <table>
        <thead><tr><th>Source IP / Host</th><th>Total Hits</th><th>Worst Severity</th></tr></thead>
        <tbody>%s</tbody>
    </table>]], table.concat(rows, "\n"))
end

local function build_hits_table(hits)
    if #hits == 0 then
        return '<p class="muted">No threats detected.</p>'
    end
    local rows = {}
    -- Show up to 200 hits to keep the file manageable
    local limit = math.min(#hits, 200)
    for i = 1, limit do
        local h = hits[i]
        local e = h.event
        table.insert(rows, string.format([[
        <tr>
            <td class="mono small">%s</td>
            <td>%s</td>
            <td><strong>%s</strong><br><span class="muted small">%s — %s</span></td>
            <td>%s</td>
            <td class="mono small truncate" title="%s">%s</td>
        </tr>]],
            esc(e.timestamp or ""),
            sev_badge(h.severity),
            esc(h.rule_name),
            esc(h.rule_id),
            esc(h.description),
            cat_pill(h.category),
            esc(e.raw or ""),
            esc((e.raw or ""):sub(1, 120))
        ))
    end
    local note = ""
    if #hits > 200 then
        note = string.format('<p class="muted">Showing first 200 of %d total hits.</p>', #hits)
    end
    return note .. string.format([[
    <div class="table-scroll">
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Severity</th>
                <th>Rule</th>
                <th>Category</th>
                <th>Raw Log (truncated)</th>
            </tr>
        </thead>
        <tbody>%s</tbody>
    </table>
    </div>]], table.concat(rows, "\n"))
end

-- -------------------------------------------------------------------------
-- Full HTML page
-- -------------------------------------------------------------------------
local function build_html(results, log_file)
    local summary_cards  = build_summary_cards(results)
    local category_table = build_category_table(results.by_category)
    local top_ips_table  = build_top_ips(results.top_ips)
    local hits_table     = build_hits_table(results.hits)
    local generated_at   = utils.readable_now()
    local clean_log      = esc(utils.basename(log_file))

    return string.format([[<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LuaShield Report — %s</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

  :root {
    --bg:         #0d0f14;
    --surface:    #13161e;
    --surface2:   #1a1e2a;
    --border:     #252a38;
    --text:       #c9d1e0;
    --muted:      #5a6278;
    --accent:     #4a8fff;
    --red:        #ff3b3b;
    --orange:     #ff8c00;
    --yellow:     #f5c400;
    --green:      #4caf50;
    --mono:       'IBM Plex Mono', monospace;
    --sans:       'IBM Plex Sans', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    line-height: 1.6;
  }

  /* Header */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 28px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  header h1 {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #fff;
  }
  header h1 span { color: var(--accent); }
  .header-meta { color: var(--muted); font-size: 12px; font-family: var(--mono); text-align: right; }

  /* Layout */
  main { max-width: 1280px; margin: 0 auto; padding: 32px 40px 60px; }

  h2 {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 36px 0 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }

  /* Cards */
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 14px;
    margin-bottom: 8px;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px 18px 16px;
  }
  .card-value {
    font-size: 34px;
    font-weight: 700;
    font-family: var(--mono);
    line-height: 1;
    margin-bottom: 6px;
  }
  .card-label {
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }

  /* Tables */
  table {
    width: 100%%;
    border-collapse: collapse;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
  }
  th {
    background: var(--surface2);
    color: var(--muted);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }
  td {
    padding: 9px 14px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: var(--surface2); }

  .table-scroll { overflow-x: auto; }

  /* Badge & pill */
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 700;
    font-family: var(--mono);
    letter-spacing: 0.05em;
    white-space: nowrap;
  }
  .pill {
    display: inline-block;
    padding: 2px 7px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 3px;
    font-size: 11px;
    font-family: var(--mono);
    color: var(--muted);
    margin-right: 4px;
  }

  /* Bar chart */
  .bar-wrap {
    background: var(--surface2);
    border-radius: 2px;
    height: 8px;
    width: 200px;
  }
  .bar {
    background: var(--accent);
    height: 8px;
    border-radius: 2px;
    min-width: 2px;
  }

  /* Utility */
  .mono  { font-family: var(--mono); }
  .small { font-size: 12px; }
  .muted { color: var(--muted); }
  .truncate { max-width: 480px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  code { font-family: var(--mono); color: var(--accent); font-size: 12px; }

  /* No threats message */
  .no-threats {
    text-align: center;
    padding: 60px 20px;
    color: var(--green);
    font-size: 18px;
    font-weight: 600;
  }

  footer {
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    font-family: var(--mono);
  }
</style>
</head>
<body>

<header>
  <div>
    <h1>Lua<span>Shield</span></h1>
    <div style="color:var(--muted);font-size:12px;margin-top:4px">Log Analyzer and Threat Detection Report</div>
  </div>
  <div class="header-meta">
    <div>File: %s</div>
    <div>Generated: %s</div>
  </div>
</header>

<main>

  <h2>Summary</h2>
  %s

  <h2>Threats by Category</h2>
  %s

  <h2>Top Source IPs / Hosts</h2>
  %s

  <h2>Threat Event Log</h2>
  %s

</main>

<footer>
  LuaShield v1.0 — generated %s
</footer>

</body>
</html>]],
        clean_log,
        clean_log,
        generated_at,
        summary_cards,
        category_table,
        top_ips_table,
        hits_table,
        generated_at
    )
end

-- -------------------------------------------------------------------------
-- Public API
-- -------------------------------------------------------------------------
function M.generate(results, log_file)
    local html      = build_html(results, log_file)
    local timestamp = utils.now_string()
    local base      = utils.basename(log_file):gsub("%.[^%.]+$", "")
    local out_path  = string.format("reports/report_%s_%s.html", base, timestamp)

    -- Ensure reports dir exists
    os.execute("mkdir -p reports 2>nul || mkdir -p reports 2>/dev/null || true")

    local fh = io.open(out_path, "w")
    if not fh then
        -- Fallback to current directory
        out_path = string.format("report_%s_%s.html", base, timestamp)
        fh = io.open(out_path, "w")
    end

    if fh then
        fh:write(html)
        fh:close()
    else
        utils.err("Could not write report file.")
    end

    return out_path
end

return M
