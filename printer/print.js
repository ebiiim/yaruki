const fs = require('fs')
const net = require('net');
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
    logErr('Usage: node print.js <file|->');
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
// Save to SVG
////////////////////////////////
{
    const configFile = configDir + "/preview.json";
    const pr = JSON.parse(fs.readFileSync(configFile).toString());
    logErr('Printer configuration loaded:', configFile);
    logErr('Printer:', pr);

    logErr('Converting to SVG...');
    doc = loadedReceiptData;
    const svg = receiptline.transform(doc, pr);

    logErr('Saving...');
    const svgFile = args[2] === "-" ? "/dev/stdout" : receiptFile + '.svg';
    fs.writeFileSync(svgFile, svg)
    logErr('SVG saved:', svgFile);
}

////////////////////////////////
// Print
////////////////////////////////
{
    const configFile = configDir + "/print.json";
    const pr = JSON.parse(fs.readFileSync(configFile).toString());
    logErr('Printer configuration loaded:', configFile);
    logErr('Printer:', pr);

    logErr('Converting to printer command...');
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

    logErr('Printing...');
    const socket = net.connect(pr.port, pr.host, () => {
        socket.end(command, 'binary');
    });
    socket.on('error', err => {
        logErr(err.message);
    });
    logErr('Printed');
}