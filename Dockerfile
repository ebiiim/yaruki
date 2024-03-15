# NOTE: this is temporary until we build `printer` as a web service so that `ui` and `printer` can be deployed separately

FROM python:3.12-slim

# printer: install dependencies
WORKDIR /app/printer
RUN apt-get update && apt-get install -y curl --no-install-recommends && apt-get clean -y && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - &&\
    apt-get install -y nodejs --no-install-recommends && apt-get clean -y && rm -rf /var/lib/apt/lists/*
COPY printer/package.json printer/package-lock.json ./
RUN npm install

# ui: install dependencies
WORKDIR /app/ui
COPY ui/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# printer: copy app
WORKDIR /app/printer
COPY printer/config config
COPY printer/preview.js preview.js
COPY printer/print.js print.js

# ui: copy app
WORKDIR /app/ui
COPY ui/.streamlit .streamlit
COPY ui/app.py .
COPY ui/static static
COPY ui/tests tests
COPY ui/config.json ui/default.css ui/default.receipt.tmpl ./

# run the app
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
