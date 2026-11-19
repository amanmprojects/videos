#!/bin/sh
# Builds the folders the demo recording browses, under $1 (default /tmp/files-demo).
set -eu
D=${1:-/tmp/files-demo}
rm -rf "$D"; mkdir -p "$D"
H=$D/home
mkdir -p "$H/Documents" "$H/Photos" "$H/Music" "$H/Projects/website" "$H/Downloads" "$D/server/www/assets"

photo() { magick -size 1600x1000 "gradient:$2" -fill white -font DejaVu-Serif-Italic -pointsize 120 -gravity center -annotate 0 "$3" "$H/Photos/$1"; }
photo lisbon.jpg  '#0f2027-#2c5364' 'Lisbon'
photo porto.jpg   '#ee9ca7-#7a3e63' 'Porto'
photo alps.jpg    '#1e3c72-#a8c0ff' 'Alps'
photo sunset.webp '#f12711-#f5af19' 'Sunset'
cp "$H/Photos/lisbon.jpg" "$H/wallpaper.jpg"

cat > "$H/Projects/website/index.html" <<'HTML'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Field notes</title>
    <link rel="stylesheet" href="style.css">
  </head>
  <body>
    <main id="app"></main>
    <script type="module" src="app.js"></script>
  </body>
</html>
HTML
cat > "$H/Projects/website/app.js" <<'JS'
// Renders the trip log from posts.json.
const app = document.querySelector("#app");

async function load() {
  const posts = await (await fetch("/posts.json")).json();
  for (const post of posts) {
    const el = document.createElement("article");
    el.innerHTML = `<h2>${post.title}</h2><p>${post.body}</p>`;
    app.append(el);
  }
}

load();
JS
printf 'main { max-width: 42rem; margin: 4rem auto; }\nh2 { font: 600 1.4rem/1.2 system-ui; }\n' > "$H/Projects/website/style.css"
printf '# Field notes\n\nA small site for **trip logs**.\n\n- Lisbon, Porto, the Alps\n- Photos in `assets/`\n' > "$H/Projects/website/README.md"
(cd "$H/Projects" && bsdtar -czf "$H/website-backup.tar.gz" website)
printf '# Trip notes\n\n- Book the Porto train\n- Pack the wide lens\n' > "$H/notes.md"
printf 'buy film\nrenew passport\n' > "$H/todo.txt"
magick -size 850x1100 xc:white -fill '#222' -font DejaVu-Sans -pointsize 46 -annotate +80+150 'Itinerary' -pointsize 24 -annotate +80+230 'Lisbon  3 nights' -annotate +80+280 'Porto   2 nights' "$H/Documents/itinerary.pdf"
ffmpeg -v error -f lavfi -i "sine=frequency=330:duration=4" -metadata title="Harbour Lights" -metadata artist="The Demo Band" -metadata album="Field Notes" "$H/Music/harbour-lights.mp3"

printf '<h1>web-prod</h1>\n' > "$D/server/www/index.html"
printf 'body { margin: 0 }\n' > "$D/server/www/site.css"
echo "Fixtures in $D"
