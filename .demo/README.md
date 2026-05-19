# Demo recordings

`demo.tape` is a [charmbracelet/vhs](https://github.com/charmbracelet/vhs)
script. It records the 60-second author onboarding flow:

1. `uv tool install dryade-cli`
2. `dryade plugin new my_awesome_plugin --tier starter`
3. `cd my_awesome_plugin`
4. `ls`
5. `dryade plugin validate`
6. `dryade plugin package`
7. `ls *.dryadepkg`

## Regenerate the GIF

```bash
vhs .demo/demo.tape
```

Output lands at `.demo/demo.gif`, which the top of `README.md` embeds.

## Install vhs

```bash
brew install vhs                                # macOS
go install github.com/charmbracelet/vhs@latest  # any platform with Go
```

`vhs` requires `ffmpeg` on PATH.

## Size budget

The embedded GIF should stay under ~10 MB so it loads quickly on GitHub.
After regeneration, check:

```bash
du -h .demo/demo.gif
```

If oversized, recompress with `gifsicle -O3 .demo/demo.gif -o .demo/demo.gif`
or lower the `Set Width` / `Set Height` in the tape script.

## Placeholder note

The current `demo.gif` checked into the repo is a **1-frame transparent PNG
placeholder** with a `.gif` extension — it satisfies the README image embed
on launch day. The first real recording lands when the CLI release pipeline
is wired (see `.github/workflows/release-drafter.yml`).
