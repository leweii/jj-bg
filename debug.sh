
docker build -t lewei/jj-bg-app .

docker run \
-v /Users/lewei/playground/jj-bg/upload:/app2/upload \
-v /Users/lewei/playground/jj-bg/output:/app2/output \
-v /Users/lewei/playground/jj-bg/background:/app2/background \
-v /Users/lewei/playground/jj-bg/output_with_background:/app2/output_with_background \
-it \
--name jj-bg-app \
lewei/jj-bg-app

docker exec jj-bg-app python main.py
cp /Users/lewei/playground/jj-bg/output /Users/lewei/playground/jj-bg/output-host
docker stop jj-bg-app
docker rm jj-bg-app
