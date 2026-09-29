FROM python:3.13-slim

WORKDIR /app

COPY requierements.txt ./requierements.txt
RUN pip install --no-cache-dir -r requierements.txt

COPY main.py normalization.py modele.joblib ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
