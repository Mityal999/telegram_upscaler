FROM python:3.10

WORKDIR /app

COPY ./src .

COPY .env /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

RUN chmod +x start.sh

CMD ["./start.sh"]