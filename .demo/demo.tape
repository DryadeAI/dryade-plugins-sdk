# charmbracelet/vhs script — records the 60-second author onboarding flow.
#
# Regenerate the GIF after CLI changes:
#   vhs .demo/demo.tape
#
# Requires: vhs (brew install vhs | go install github.com/charmbracelet/vhs@latest)
#           ffmpeg     (vhs uses it under the hood)
#           dryade-cli (uv tool install dryade-cli)

Output .demo/demo.gif

Set Theme "Catppuccin Frappe"
Set FontSize 14
Set Width 1200
Set Height 700
Set Padding 24
Set FontFamily "Fira Code"
Set CursorBlink true
Set TypingSpeed 30ms
Set Shell "bash"

Type "uv tool install dryade-cli"
Sleep 200ms
Enter
Sleep 3s

Type "dryade plugin new my_awesome_plugin --tier starter"
Sleep 200ms
Enter
Sleep 4s

Type "cd my_awesome_plugin"
Sleep 200ms
Enter
Sleep 500ms

Type "ls"
Sleep 200ms
Enter
Sleep 2s

Type "dryade plugin validate"
Sleep 200ms
Enter
Sleep 4s

Type "dryade plugin package"
Sleep 200ms
Enter
Sleep 4s

Type "ls *.dryadepkg"
Sleep 200ms
Enter
Sleep 2s
