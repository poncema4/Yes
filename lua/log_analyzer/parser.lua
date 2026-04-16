-- parser.lua — Parses raw log lines into structured event tables
-- Supports: Apache/Nginx combined, bracketed timestamp, syslog, key=value, raw fallback

local M = {}

local function trim(s)
    return s:match("^%s*(.-)%s*$")
end

local function parse_timestamp(raw)
    local y, mo, d, h, mi, s = raw:match("(%d%d%d%d)-(%d%d)-(%d%d)[T ](%d%d):(%d%d):(%d%d)")
    if y then
        return string.format("%s-%s-%s %s:%s:%s", y, mo, d, h, mi, s)
    end
    local mon, day, t = raw:match("(%a+)%s+(%d+)%s+(%d+:%d+:%d+)")
    if mon then return string.format("%s %s %s", mon, day, t) end
    return raw
end

local function detect_format(line)
    if line:match('%d+%.%d+%.%d+%.%d+.-%[.-%]%s+"') then return "apache" end
    if line:match("^%[%d%d%d%d%-%d%d%-%d%d")         then return "bracketed" end
    if line:match("^%a%a%a%s+%d+%s+%d+:%d+:%d+")     then return "syslog" end
    if line:match("src=") or line:match("dst=")       then return "kv" end
    return "raw"
end

local function parse_apache(line)
    local ip, ts, method, path, status, size =
        line:match('(%d+%.%d+%.%d+%.%d+)%s+%S+%s+%S+%s+%[(.-)%]%s+"(%a+)%s+(%S+)%s+%S+"%s+(%d+)%s+(%d+)')
    if ip then
        return {
            timestamp = ts,
            level     = tonumber(status) >= 400 and "WARN" or "INFO",
            source    = ip,
            message   = string.format("%s %s -> HTTP %s (%s bytes)", method, path, status, size),
            raw       = line,
            ip        = ip,
            status    = tonumber(status),
            path      = path,
            method    = method,
        }
    end
    return nil
end

local function parse_bracketed(line)
    local ts, rest = line:match("^%[(.-)%]%s+(.*)")
    if not ts then return nil end
    local level, src, msg = rest:match("^(%u+)%s+(%S+)%s+(.*)")
    if not level then
        level, msg = rest:match("^(%u+)%s+(.*)")
        src = "system"
    end
    if not level then level, msg, src = "INFO", rest, "system" end
    local ip = msg and msg:match("(%d+%.%d+%.%d+%.%d+)")
    return {
        timestamp = parse_timestamp(ts),
        level     = level,
        source    = src or "system",
        message   = trim(msg or rest),
        raw       = line,
        ip        = ip,
    }
end

local function parse_syslog(line)
    local ts, host, proc, msg =
        line:match("^(%a+%s+%d+%s+%d+:%d+:%d+)%s+(%S+)%s+(%S+):%s+(.*)")
    if not ts then return nil end
    local ip = msg and msg:match("(%d+%.%d+%.%d+%.%d+)")
    return {
        timestamp = ts,
        level     = "INFO",
        source    = proc or host,
        message   = trim(msg or ""),
        raw       = line,
        ip        = ip,
        host      = host,
    }
end

local function parse_kv(line)
    local fields = {}
    for k, v in line:gmatch("(%w+)=([^%s]+)") do fields[k] = v end
    return {
        timestamp = fields.ts or fields.time or fields.timestamp or "",
        level     = fields.sev or fields.level or "INFO",
        source    = fields.src or fields.host or "unknown",
        message   = fields.msg or line,
        raw       = line,
        ip        = fields.src,
    }
end

local function parse_line(line)
    local fmt = detect_format(line)
    if fmt == "apache"    then return parse_apache(line)
    elseif fmt == "bracketed" then return parse_bracketed(line)
    elseif fmt == "syslog"    then return parse_syslog(line)
    elseif fmt == "kv"        then return parse_kv(line)
    else
        local ip = line:match("(%d+%.%d+%.%d+%.%d+)")
        return { timestamp="", level="INFO", source="raw", message=trim(line), raw=line, ip=ip }
    end
end

function M.parse(filepath)
    local events = {}
    local fh = io.open(filepath, "r")
    if not fh then return events end
    local n = 0
    for line in fh:lines() do
        line = trim(line)
        if line ~= "" then
            n = n + 1
            local ev = parse_line(line)
            if ev then
                ev.line_num = n
                table.insert(events, ev)
            end
        end
    end
    fh:close()
    return events
end

return M
