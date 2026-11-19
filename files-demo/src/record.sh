#!/bin/sh
# Records the README demo: builds fixture folders and a throwaway sshd (the "web-prod" server),
# replays demo/script.json in real time on Rune's headless renderer, and writes the video and
# the GIF. Needs ffmpeg, ImageMagick and openssh.
#
#   demo/record.sh [out-dir]      (default: demo/out)
set -eu
cd "$(dirname "$0")/.."
OUT=${1:-demo/out}
D=/tmp/files-demo
mkdir -p "$OUT"

demo/fixtures.sh "$D"
python3 demo/storyboard.py

# A server on 127.0.0.1:2299 whose $HOME is the fixture's www folder, and an ssh config naming it.
S=$D/sshd
mkdir -p "$S"
rm -f "$S/host_key" "$S/host_key.pub" "$S/client_key" "$S/client_key.pub" "$S/known_hosts"
ssh-keygen -q -t ed25519 -N '' -f "$S/host_key"
ssh-keygen -q -t ed25519 -N '' -f "$S/client_key"
cp "$S/client_key.pub" "$S/authorized_keys"
cat > "$S/sshd_config" <<CONF
Port 2299
ListenAddress 127.0.0.1
HostKey $S/host_key
PidFile $S/sshd.pid
AuthorizedKeysFile $S/authorized_keys
PasswordAuthentication no
UsePAM no
StrictModes no
SetEnv HOME=$D/server/www
Subsystem sftp /usr/lib/ssh/sftp-server
CONF
cat > "$S/client_config" <<CONF
Host web-prod
  HostName 127.0.0.1
  Port 2299
  IdentityFile $S/client_key
  IdentitiesOnly yes
  UserKnownHostsFile $S/known_hosts
  StrictHostKeyChecking accept-new
Host build-box
  HostName 192.0.2.10
Host staging
  HostName 192.0.2.20
CONF
/usr/bin/sshd -D -e -f "$S/sshd_config" 2>"$S/log" &
SSHD=$!
trap 'kill $SSHD 2>/dev/null; ssh -F "$S/client_config" -O exit web-prod 2>/dev/null || true' EXIT
sleep 0.5

mkdir -p "$D/cfg/files"
echo web-prod > "$D/cfg/files/pinned"

# Rune's headless tooling and keycaps in an optimized build, beside the installed one.
cargo build --release --features rune/keys-overlay --target-dir target/demo

# Real time (--realtime), so previews, completions and the upload land as they would live.
HOME=$D/home XDG_CONFIG_HOME=$D/cfg XDG_CACHE_HOME=$D/cache FILES_SSH_CONFIG=$S/client_config SHELL=/bin/sh \
  target/demo/release/files "$D/home" --realtime --script demo/script.json \
  --video "$OUT/files-demo.mp4" --fps 30 --size 1280x800 --scale 2 --keys bottom-right --pointer

ffmpeg -v error -y -i "$OUT/files-demo.mp4" -vf "fps=15,scale=960:-1:flags=lanczos,palettegen=max_colors=256:stats_mode=diff" "$D/palette.png"
ffmpeg -v error -y -i "$OUT/files-demo.mp4" -i "$D/palette.png" \
  -lavfi "fps=15,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=sierra2_4a:diff_mode=rectangle" "$OUT/files-demo.gif"
echo "Wrote $OUT/files-demo.mp4 and $OUT/files-demo.gif"
