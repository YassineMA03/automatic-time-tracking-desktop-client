# helpers.py (macOS)
import subprocess

# App-specific AppleScript to fetch active tab title
APP_TAB_TITLE_SCRIPT = {
    "Google Chrome": r'''
        tell application "Google Chrome"
            if (count of windows) > 0 then
                set t to title of active tab of front window
                return t
            else
                return ""
            end if
        end tell
    ''',
    "Safari": r'''
        tell application "Safari"
            if (count of windows) > 0 then
                set t to name of current tab of front window
                return t
            else
                return ""
            end if
        end tell
    ''',
    "Microsoft Edge": r'''
        tell application "Microsoft Edge"
            if (count of windows) > 0 then
                set t to title of active tab of front window
                return t
            else
                return ""
            end if
        end tell
    ''',
    "Brave Browser": r'''
        tell application "Brave Browser"
            if (count of windows) > 0 then
                set t to title of active tab of front window
                return t
            else
                return ""
            end if
        end tell
    ''',
    # Add more Chromium variants if you use them:
    # "Chromium": ...,
    # "Arc": ... (Arc’s AppleScript support varies by version)
}

def _osascript(script: str) -> str:
    return subprocess.check_output(["osascript", "-e", script]).decode("utf-8").strip()

def _front_app_and_window_title():
    # Get frontmost app + (generic) front window title via System Events
    script = r'''
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        set appName to name of frontApp
        try
            set winTitle to name of front window of frontApp
        on error
            set winTitle to ""
        end try
    end tell
    return appName & "||" & winTitle
    '''
    out = _osascript(script)
    if "||" in out:
        app, title = out.split("||", 1)
        return app, title
    return out or "UnknownApp", ""

def get_active_window_title():
    """
    Returns 'AppName - TabOrWindowTitle' when available, otherwise just 'AppName'.
    Strategy:
      1) Find the frontmost app.
      2) If it's a supported browser, ask that app for the active tab title.
      3) Fallback to generic front window title from System Events.
    """
    try:
        app, generic_title = _front_app_and_window_title()
        app = app.strip()

        # If this is a supported browser, try to read the active tab title
        if app in APP_TAB_TITLE_SCRIPT:
            try:
                tab_title = _osascript(APP_TAB_TITLE_SCRIPT[app])
                # Prefer tab title if present; else use generic window title
                title = tab_title if tab_title else generic_title
            except subprocess.CalledProcessError:
                # Automation permission denied or AppleScript error -> fallback
                title = generic_title
        else:
            title = generic_title

        return f"{app} - {title}" if title else app
    except Exception:
        # Last-resort fallback: NSWorkspace app name only
        try:
            from AppKit import NSWorkspace
            app = NSWorkspace.sharedWorkspace().activeApplication().get('NSApplicationName', None)
            return app or "UnknownApp"
        except Exception:
            return "UnknownApp"
