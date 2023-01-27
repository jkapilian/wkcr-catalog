docker compose up --build -d
sleep 10
python test.py
docker compose down