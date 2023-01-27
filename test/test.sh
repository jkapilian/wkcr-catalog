docker compose up --build -d
sleep 10
python test.py
retVal=$?
docker logs wkcr-catalog-web-1
docker compose down
# exit $retVal