const fs = require('fs')
const receiptline = require('receiptline');

////////////////////////////////
// Parameters
////////////////////////////////
const configDir = process.env.PRINTER_CONFIG_DIR || "config";

const args = process.argv;
if (args.length < 3) {
    console.error('Usage: node preview.js <file|->');
    console.error('Environment variables: PRINTER_CONFIG_DIR=<string>');
    process.exit(1);
}

const receiptFile = args[2] === "-" ? "/dev/stdin" : args[2];


////////////////////////////////
// Prepare receipt data
////////////////////////////////
const loadedReceiptData = fs.readFileSync(receiptFile).toString()
console.error('Receipt loaded:', receiptFile);

////////////////////////////////
// Print SVG to stdout
////////////////////////////////
{
    const configFile = configDir + "/preview.json";
    const pr = JSON.parse(fs.readFileSync(configFile).toString());
    console.error('Printer configuration loaded:', configFile);
    console.error('Printer:', pr);

    console.error('Converting to SVG...');
    doc = loadedReceiptData;
    const svg = receiptline.transform(doc, pr);

    console.error('Printing SVG to stdout...');
    process.stdout.write(svg);
    console.error('SVG printed');
}
