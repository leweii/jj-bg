FROM lewei/jj-bg

WORKDIR /app2

COPY . /app2

RUN pip install --no-cache-dir -r requirements.txt

VOLUME /app2/upload
VOLUME /app2/output
VOLUME /app2/background

CMD ["sh", "-c", "while true; do sleep 3600; done"]
