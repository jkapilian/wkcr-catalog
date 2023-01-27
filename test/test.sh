docker compose up --build -d
sleep 10
python test.py
retVal = $?
docker compose down
exit $retVal