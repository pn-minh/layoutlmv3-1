const fs = require('fs');
const path = require('path');
const { Resvg } = require('@resvg/resvg-js');

// 1. Read the SVG from preview HTML
const htmlPath = path.resolve(__dirname, '../scratch/model_architecture_preview.html');
const htmlContent = fs.readFileSync(htmlPath, 'utf8');

const svgMatch = htmlContent.match(/<svg[\s\S]*?<\/svg>/);
if (!svgMatch) {
  console.error('Could not find SVG inside preview HTML!');
  process.exit(1);
}

const svgString = svgMatch[0];

// 2. Render SVG at 2x scale for ultra crisp 300 DPI academic quality
const resvg = new Resvg(svgString, {
  fitTo: {
    mode: 'zoom',
    value: 2.0 // 2x resolution
  },
  font: {
    loadSystemFonts: true,
    defaultFontFamily: 'Arial'
  }
});

const pngData = resvg.render();
const pngBuffer = pngData.asPng();

const outPngPath = path.resolve(__dirname, '../thesis/figures/model_architecture.png');
fs.writeFileSync(outPngPath, pngBuffer);
console.log(`Saved high-resolution PNG: ${outPngPath}`);
