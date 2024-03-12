const fs = require('fs')
const net = require('net');
const receiptline = require('receiptline');

////////////////////////////////
// Parameters
////////////////////////////////
const configDir = process.env.PRINTER_CONFIG_DIR || "config";

const args = process.argv;
if (args.length < 3) {
    console.error('Usage: node print.js <file|->');
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
// Save to SVG
////////////////////////////////
{
    const configFile = configDir + "/preview.json";
    const pr = JSON.parse(fs.readFileSync(configFile).toString());
    console.error('Printer configuration loaded:', configFile);
    console.error('Printer:', pr);

    console.error('Converting to SVG...');
    doc = loadedReceiptData;
    const svg = receiptline.transform(doc, pr);

    console.error('Saving...');
    const svgFile = args[2] === "-" ? "/dev/stdout" : receiptFile + '.svg';
    fs.writeFileSync(svgFile, svg)
    console.error('SVG saved:', svgFile);
}

////////////////////////////////
// Print
////////////////////////////////
{
    const configFile = configDir + "/print.json";
    const pr = JSON.parse(fs.readFileSync(configFile).toString());
    console.error('Printer configuration loaded:', configFile);
    console.error('Printer:', pr);

    console.error('Converting to printer command...');
    doc = loadedReceiptData;
    // adjust margin for SII RP-E11
    if (pr.upsideDown) {
        doc = '\n\n\n\n' + doc;
        if (!pr.spacing) {
            doc = doc + '\n';
        }
    } else {
        doc += '\n\n\n';
        if (!pr.spacing) {
            doc += '\n';
        }
    }
    const command = receiptline.transform(doc, pr);

    console.error('Printing...');
    const socket = net.connect(pr.port, pr.host, () => {
        socket.end(command, 'binary');
    });
    socket.on('error', err => {
        console.error(err.message);
        console.error('Print failed');
        process.exit(1);
    });
    socket.on('end', () => {
        console.error('Printed');
    });
}