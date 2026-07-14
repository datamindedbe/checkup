# VHS tape for the README demo GIF (https://github.com/charmbracelet/vhs)
# Render from a folder containing a dbt project WITHOUT an existing checkup.yaml
# (the recording walks through `checkup init`), e.g.:
#   cd path/to/a/data-product && vhs path/to/checkup/images/demo.tape
Require checkup
Require fish

Output demo.gif

Set Shell fish
Set Theme { "name": "Checkup Night", "background": "#080635", "foreground": "#cdd6f4", "cursor": "#f5e0dc", "selection": "#585b70", "black": "#45475a", "red": "#f38ba8", "green": "#a6e3a1", "yellow": "#f9e2af", "blue": "#89b4fa", "magenta": "#f5c2e7", "cyan": "#94e2d5", "white": "#bac2de", "brightBlack": "#585b70", "brightRed": "#f38ba8", "brightGreen": "#a6e3a1", "brightYellow": "#f9e2af", "brightBlue": "#89b4fa", "brightMagenta": "#f5c2e7", "brightCyan": "#94e2d5", "brightWhite": "#a6adc8" }

Set FontSize 32
Set Width 3200
Set Height 2200
Set Padding 48
Set WindowBar Colorful
Set TypingSpeed 75ms
Set Framerate 24

# Disable fish autosuggestions (the greyed-out command proposals)
Env fish_autosuggestion_enabled "0"

# fish command highlighting (VHS runs fish with --no-config, so set colors here)
Env fish_color_command "89b4fa"
Env fish_color_param "cdd6f4"
Env fish_color_option "f5c2e7"
Env fish_color_error "f38ba8"

# --- checkup init: interactive config wizard ---
Type "checkup init"
Sleep 750ms
Enter
Sleep 3s

# Tags
Type "product=checkup-scorekaarten"
Sleep 400ms
Enter
Sleep 500ms
Enter
Sleep 1s

# Providers: select dbt and git
Space
Sleep 250ms
Down
Sleep 250ms
Space
Sleep 400ms
Enter
Sleep 2.5s

# Metrics: select the first five
Space
Sleep 200ms
Down
Sleep 200ms
Space
Sleep 200ms
Down
Sleep 200ms
Space
Sleep 200ms
Down
Sleep 200ms
Space
Sleep 200ms
Down
Sleep 200ms
Space
Sleep 400ms
Enter
Sleep 1s

# Materializer: accept default (console)
Enter
Sleep 2s

# --- checkup plugins: list installed plugins ---
Type "checkup plugins"
Sleep 750ms
Enter
Sleep 6s

# --- checkup run: measure the data product ---
Type "checkup run"
Sleep 750ms
Enter

# Skip the ~30s measurement wait, then reveal the results table
Hide
Sleep 30s
Show

# Linger on the results table
Sleep 5s
Screenshot demo.png
Sleep 1s

# --- checkup run --select tag:healthcheck: a focused subset ---
Type "checkup run --select tag:healthcheck"
Sleep 750ms
Enter

# Skip the measurement wait, then reveal the smaller results table
Hide
Sleep 30s
Show

# Linger on the results table
Sleep 5s
Sleep 1s
