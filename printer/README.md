
1. Initial setup
    ```
    npm install
    ```

2. Edit files below to configure printers
    - `config/preview.json` both for preview and print
    - `config/print.json` for print

    Config directory can be set with environment variable `PRINTER_CONFIG_DIR`.

3. Run
    ```
    # preview
    npm run --silent preview -- data/hello.receipt > hello.svg
    # print
    npm run --silent print -- data/hello.receipt
    ```
    or
    ```
    # preview
    echo "hello" | npm run --silent preview -- -
    # print
    echo "hello" | npm run --silent print -- -
    ```
