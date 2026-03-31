# smux Setup

Read this file only when `smux` or `tmux-bridge` is missing, or when you need to create a collaboration session from scratch.

## Install

If the `smux` repo is available locally:

```bash
bash install.sh
source ~/.bashrc
```

If you want the hosted installer:

```bash
curl -fsSL shawnpana.com/smux/install.sh | bash
source ~/.bashrc
```

If the current shell still cannot find `smux`, reload `PATH` explicitly:

```bash
export PATH="$HOME/.smux/bin:$PATH"
```

## Verify

```bash
smux help
tmux-bridge version
```

## Start a Collaboration Session

```bash
tmux new -As collaboration
```

Create panes with `Option+n` or raw tmux:

```bash
tmux split-window -h
tmux select-layout tiled
```

Start the tools you want in different panes, for example:

- one pane running Claude Code
- one pane running Codex CLI
- one pane for tests, logs, or a shell

Prefer mixed-runtime critique when possible, but do not block on it. If the current agent is running in Claude Code and no Codex pane is available, open another pane and start a fresh Claude Code instance there. Do the symmetric fallback for Codex CLI.

```bash
tmux split-window -h
tmux select-layout tiled
claude   # or codex
```

## Label Panes Early

In each pane, label it once:

```bash
tmux-bridge name "$(tmux-bridge id)" claude
tmux-bridge name "$(tmux-bridge id)" codex
tmux-bridge name "$(tmux-bridge id)" claude-review
tmux-bridge name "$(tmux-bridge id)" tests
```

Then confirm the layout:

```bash
tmux-bridge list
```

## Fast Sanity Checks

```bash
tmux-bridge id
tmux-bridge list
tmux-bridge read codex 20
```

## Failure Modes

**Issue**: `tmux-bridge` says it cannot find a reachable tmux server.
**Fix**: Run inside tmux, not from a plain shell.

**Issue**: `must read the pane before interacting`
**Fix**: Run `tmux-bridge read <target> ...` before `message`, `type`, or `keys`.

**Issue**: Wrong pane received the message.
**Fix**: Use labels with `tmux-bridge name` and verify targets with `tmux-bridge list` or `tmux-bridge resolve`.
