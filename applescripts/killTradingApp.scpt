-- Robust kill script that can find Webull even if renamed
-- Uses process signature detection instead of just app name

on run
    set debug_log to "Executing Webull kill script at " & (current date as string) & return
    
    -- First, gather information about running processes
    set debug_log to debug_log & "Looking for Webull-like processes..." & return
    
    try
        do shell script "ps -ax | grep -i '[Ww]ebull\\|trading\\|Desktop 8' | grep -v grep || echo 'No trading processes found'"
        set process_list to the result
        set debug_log to debug_log & "Found processes: " & return & process_list & return
    on error err_msg
        set debug_log to debug_log & "Error checking processes: " & err_msg & return
    end try
    
    -- Attempt to kill processes using multiple approaches
    set debug_log to debug_log & "Attempting to kill trading app processes..." & return
    
    -- Method 1: Kill by pattern matches
    try
        do shell script "pkill -9 -f '[Ww]ebull' || true"
        do shell script "pkill -9 -f 'Desktop 8\\.' || true"
        do shell script "pkill -9 -f '[Tt]rading' || true"
        set debug_log to debug_log & "Kill commands executed" & return
    on error err_msg
        set debug_log to debug_log & "Error killing processes: " & err_msg & return
    end try
    
    -- Verify after killing
    try
        do shell script "ps -ax | grep -i '[Ww]ebull\\|trading\\|Desktop 8' | grep -v grep || echo 'No trading processes remaining'"
        set after_kill_check to the result
        set debug_log to debug_log & "After kill check: " & after_kill_check & return
    on error err_msg
        set debug_log to debug_log & "Error checking remaining processes: " & err_msg & return
    end try
    
    -- Close Chrome tabs that might be related to Webull
    set chrome_closed_count to 0
    
    try
        tell application "Google Chrome"
            if it is running then
                set window_count to count windows
                repeat with w from 1 to window_count
                    set tab_count to count tabs of window w
                    repeat with t from tab_count to 1 by -1
                        try
                            set tab_url to URL of tab t of window w
                            if tab_url contains "webull.com" or tab_url contains "trading" then
                                set chrome_closed_count to chrome_closed_count + 1
                                close tab t of window w
                            end if
                        on error
                            -- Skip any tab errors and continue
                        end try
                    end repeat
                end repeat
            end if
        end tell
        set debug_log to debug_log & "Closed " & chrome_closed_count & " webull.com tabs" & return
    on error err_msg
        set debug_log to debug_log & "Error checking Chrome tabs: " & err_msg & return
    end try
    
    set debug_log to debug_log & "Kill script completed at " & (current date as string)
    
    return debug_log
end run