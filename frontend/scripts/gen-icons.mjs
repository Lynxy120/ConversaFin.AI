import sharp from "sharp";
import { mkdirSync } from "node:fs";

mkdirSync("public/icons", { recursive: true });
const svg = ({
  radius,
  scale,
}) => `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0EA5E9"/><stop offset="1" stop-color="#3B82F6"/></linearGradient></defs>
<rect width="512" height="512" rx="${radius}" fill="url(#g)"/>
<g transform="translate(256 256) scale(${scale}) translate(-256 -256)" fill="#fff">
<rect x="136" y="256" width="64" height="120" rx="16"/><rect x="224" y="196" width="64" height="180" rx="16"/><rect x="312" y="136" width="64" height="240" rx="16"/></g></svg>`;

const out = [
  ["icon-192.png", 192, { radius: 112, scale: 1 }],
  ["icon-512.png", 512, { radius: 112, scale: 1 }],
  ["icon-maskable-512.png", 512, { radius: 0, scale: 0.8 }],
  ["apple-touch-icon.png", 180, { radius: 0, scale: 0.9 }],
];
for (const [f, s, o] of out)
  await sharp(Buffer.from(svg(o)))
    .resize(s, s)
    .png()
    .toFile(`public/icons/${f}`);
console.log("icons generated:", out.map((o) => o[0]).join(", "));
