-- utils.lua — Console output helpers and misc utilities

local M = {}

local function color(code, text)
    return string.format("\27[%sm%s\27[0m", code, text)
end

function M.banner()
    print(color("36;1", "======================================"))
    print(color("36;1", "  LuaShield - Log Analyzer v1.0"))
    print(color("36;1", "  Threat Detection & Reporting Tool"))
    print(color("36;1", "======================================"))
    print("")
end

function M.info(msg)
    print(color("37", "[INFO]  " .. msg))
end

function M.success(msg)
    print(color("32;1", "[OK]    " .. msg))
end

function M.warn(msg)
    print(color("33;1", "[WARN]  " .. msg))
end

function M.err(msg)
    print(color("31;1", "[ERROR] " .. msg))
end

function M.file_exists(path)
    local f = io.open(path, "r")
    if f then f:close(); return true end
    return false
end

function M.basename(path)
    return path:match("([^/\\]+)$") or path
end

function M.now_string()
    return os.date("%Y-%m-%d_%H-%M-%S")
end

function M.readable_now()
    return os.date("%Y-%m-%d %H:%M:%S")
end

return M
