FROM python:3.11-slim
LABEL authors="Murtada Ahmed"

ARG WEBSITE_URL
ENV WEBSITE_URL=${WEBSITE_URL}

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]