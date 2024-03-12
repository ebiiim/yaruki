const fs = require('fs')
const receiptline = require('receiptline');

logErr = (msg) => {
    process.stderr.write(msg + '\n');
}

////////////////////////////////
// Parameters
////////////////////////////////
const configDir = process.env.PRINTER_CONFIG_DIR || "config";

const args = process.argv;
if (args.length < 3) {
    logErr('Usage: node preview.js <file|->');
    logErr('Environment variables: PRINTER_CONFIG_DIR=<string>');
    process.exit(1);
}

const receiptFile = args[2] === "-" ? "/dev/stdin" : args[2];


////////////////////////////////
// Prepare receipt data
////////////////////////////////
const loadedReceiptData = fs.readFileSync(receiptFile).toString()
logErr('Receipt loaded:', receiptFile);

////////////////////////////////
// Print SVG to stdout
////////////////////////////////
{
    const configFile = configDir + "/preview.json";
    const pr = JSON.parse(fs.readFileSync(configFile).toString());
    logErr('Printer configuration loaded:', configFile);
    logErr('Printer:', pr);

    logErr('Converting to SVG...');
    doc = loadedReceiptData;
    const svg = receiptline.transform(doc, pr);

    logErr('Printing SVG to stdout...');
    process.stdout.write(svg);
    logErr('SVG printed');
}
