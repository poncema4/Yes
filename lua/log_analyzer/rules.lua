-- rules.lua — Threat detection rule definitions
-- 20 rules across 7 categories: brute_force, injection, recon, malware, exfil, auth, anomaly

local M = {}

local RULES = {

    -- BRUTE FORCE ----------------------------------------------------------
    {
        id          = "BF-001",
        name        = "SSH Brute Force Attempt",
        severity    = "HIGH",
        category    = "brute_force",
        description = "Repeated failed SSH authentication from a single source.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("failed password") or m:find("authentication failure") or
                    m:find("invalid user")    or m:find("ssh.*fail")) ~= nil
        end,
    },
    {
        id          = "BF-002",
        name        = "Multiple Login Failures",
        severity    = "MEDIUM",
        category    = "brute_force",
        description = "Generic login failure -- possible credential stuffing.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("login failed") or m:find("logon failure") or
                    m:find("bad password")  or m:find("wrong password")) ~= nil
        end,
    },
    {
        id          = "BF-003",
        name        = "Account Lockout Triggered",
        severity    = "HIGH",
        category    = "brute_force",
        description = "Account locked due to too many failed attempts.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("account locked") or m:find("too many attempts") or
                    m:find("account disabled")) ~= nil
        end,
    },

    -- SQL INJECTION / WEB ATTACKS ------------------------------------------
    {
        id          = "INJ-001",
        name        = "SQL Injection Attempt",
        severity    = "CRITICAL",
        category    = "injection",
        description = "Classic SQL injection patterns detected in a request.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("' or '1'='1") or m:find("union select") or
                    m:find("drop table")   or m:find("xp_cmdshell")  or
                    m:find("exec%(")       or m:find("';%-%-"))       ~= nil
        end,
    },
    {
        id          = "INJ-002",
        name        = "Cross-Site Scripting (XSS) Attempt",
        severity    = "HIGH",
        category    = "injection",
        description = "XSS payload detected in request.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("<script") or m:find("javascript:") or
                    m:find("onerror=")  or m:find("onload=")   or
                    m:find("alert%(")) ~= nil
        end,
    },
    {
        id          = "INJ-003",
        name        = "Path Traversal Attempt",
        severity    = "HIGH",
        category    = "injection",
        description = "Directory traversal sequences detected.",
        match = function(e)
            local m = e.message
            return (m:find("%.%.%/") or m:find("%.%.\\") or
                    m:find("%%2e%%2e") or m:find("%%2f")) ~= nil
        end,
    },
    {
        id          = "INJ-004",
        name        = "Command Injection",
        severity    = "CRITICAL",
        category    = "injection",
        description = "Shell command injection patterns in user input.",
        match = function(e)
            local m = e.message:lower()
            return (m:find(";%s*cat%s") or m:find("|%s*ls%s") or
                    m:find("`whoami`")   or m:find("%$%(id%)") or
                    m:find(";%s*wget%s") or m:find(";%s*curl%s")) ~= nil
        end,
    },

    -- RECONNAISSANCE -------------------------------------------------------
    {
        id          = "REC-001",
        name        = "Port Scan Detected",
        severity    = "MEDIUM",
        category    = "recon",
        description = "Scanning behavior -- multiple rapid port connection attempts.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("port scan") or m:find("portscan") or
                    m:find("nmap")      or m:find("masscan"))  ~= nil
        end,
    },
    {
        id          = "REC-002",
        name        = "Web Directory Enumeration",
        severity    = "MEDIUM",
        category    = "recon",
        description = "Web crawler or directory brute-force tool detected.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("gobuster") or m:find("dirb") or m:find("dirbuster") or
                    m:find("nikto")    or m:find("wfuzz")) ~= nil
        end,
    },
    {
        id          = "REC-003",
        name        = "Suspicious User-Agent",
        severity    = "LOW",
        category    = "recon",
        description = "Known scanner or exploit framework user-agent string.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("sqlmap")          or m:find("zgrab")    or
                    m:find("python%-requests") or m:find("metasploit")) ~= nil
        end,
    },

    -- MALWARE / C2 ---------------------------------------------------------
    {
        id          = "MAL-001",
        name        = "C2 Beacon Pattern",
        severity    = "CRITICAL",
        category    = "malware",
        description = "Outbound connection consistent with C2 beaconing.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("beacon")          or m:find("cobalt strike") or
                    m:find("command and control") or m:find("meterpreter")) ~= nil
        end,
    },
    {
        id          = "MAL-002",
        name        = "Ransomware Indicator",
        severity    = "CRITICAL",
        category    = "malware",
        description = "File encryption or ransomware-related activity detected.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("ransomware")     or m:find("%.locked")       or
                    m:find("%.encrypted")    or m:find("readme_to_decrypt")) ~= nil
        end,
    },
    {
        id          = "MAL-003",
        name        = "Suspicious Process Execution",
        severity    = "HIGH",
        category    = "malware",
        description = "Unusual process -- possible living-off-the-land attack.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("powershell.*%-enc") or m:find("cmd%.exe.*%/c") or
                    m:find("wscript")           or m:find("regsvr32")       or
                    m:find("mshta"))            ~= nil
        end,
    },

    -- EXFILTRATION ---------------------------------------------------------
    {
        id          = "EXF-001",
        name        = "Large Outbound Transfer",
        severity    = "HIGH",
        category    = "exfil",
        description = "Unusually large data transfer to an external host.",
        match = function(e)
            local m = e.message:lower()
            local size = m:match("(%d+)%s*mb") or m:match("(%d+)%s*gb")
            if size and tonumber(size) > 50 then return true end
            return (m:find("data exfil") or m:find("exfiltration")) ~= nil
        end,
    },
    {
        id          = "EXF-002",
        name        = "DNS Tunneling Suspected",
        severity    = "HIGH",
        category    = "exfil",
        description = "Long or encoded DNS queries -- possible DNS tunneling.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("dns tunnel") or m:find("iodine") or m:find("dnscat")) ~= nil
        end,
    },

    -- AUTH / PRIVILEGE -----------------------------------------------------
    {
        id          = "AUTH-001",
        name        = "Privilege Escalation",
        severity    = "CRITICAL",
        category    = "auth",
        description = "Attempt to gain elevated privileges.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("privilege escalation") or m:find("sudo su")   or
                    m:find("token impersonation")  or m:find("pass%-the%-hash")) ~= nil
        end,
    },
    {
        id          = "AUTH-002",
        name        = "Root / Admin Login",
        severity    = "HIGH",
        category    = "auth",
        description = "Direct login as root or administrator account.",
        match = function(e)
            local m = e.message:lower()
            return (m:find("root login") or m:find("logged in as root") or
                    (m:find("accepted.*root") and m:find("ssh")))        ~= nil
        end,
    },
    {
        id          = "AUTH-003",
        name        = "After-Hours Authentication",
        severity    = "LOW",
        category    = "auth",
        description = "Successful login between midnight and 6am.",
        match = function(e)
            local hour = e.timestamp:match("(%d%d):%d%d:%d%d")
            if hour then
                local h = tonumber(hour)
                if h ~= nil and h >= 0 and h < 6 then
                    local m = e.message:lower()
                    return (m:find("login") or m:find("accepted") or m:find("session opened")) ~= nil
                end
            end
            return false
        end,
    },

    -- ANOMALY --------------------------------------------------------------
    {
        id          = "ANO-001",
        name        = "HTTP 500 Internal Server Error",
        severity    = "MEDIUM",
        category    = "anomaly",
        description = "Server error -- may indicate exploitation or app crash.",
        match = function(e)
            return e.status == 500 or
                   (e.message:find("500") ~= nil and e.message:lower():find("internal server error") ~= nil)
        end,
    },
    {
        id          = "ANO-002",
        name        = "Repeated 403 Forbidden",
        severity    = "LOW",
        category    = "anomaly",
        description = "Multiple access-denied responses -- possible unauthorized access attempt.",
        match = function(e)
            return e.status == 403 or
                   e.message:lower():find("403 forbidden") ~= nil or
                   e.message:lower():find("access denied") ~= nil
        end,
    },
}

function M.load()
    return RULES
end

return M
