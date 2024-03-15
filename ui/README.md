1. Initial setup
    ```
    pip install -r requirements.txt
    ```

2. Edit files below to configure the app
    - `config.json`
    - `default.css` (optional)
    - `default.receipt.tmpl` (optional)

    Config file can be set with environment variable `YARUKI_UI_CONFIG`.

3. Run
    ```
    streamlit run app.py
    ```

    Log level can be set with environment variable `YARUKI_UI_LOG_LEVEL` (`INFO` or `DEBUG`, default is `INFO`).
