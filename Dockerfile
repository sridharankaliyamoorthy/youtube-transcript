# FastAPI YouTube Transcript Extractor Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (yt-dlp, if needed)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install spacy
RUN python -m spacy download en_core_web_sm

# Expose port
EXPOSE 8000

# Set environment variable for Perplexity API key (optional)
# ENV PPLX_API_KEY=your_real_api_key_here

# Start FastAPI app with Uvicorn
CMD ["uvicorn", "scripts.api_app:app", "--host", "0.0.0.0", "--port", "8000"]
