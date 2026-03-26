# Data Cleaning Toolkit — production image for VPS
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and data (demo datasets needed for "Sales/Customer" demo)
COPY src/ ./src/
COPY data/ ./data/

# Streamlit runs on 8501 by default; listen on all interfaces
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
