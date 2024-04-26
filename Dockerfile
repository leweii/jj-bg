FROM lewei/jj-bg
RUN rm -rf /var/lib/apt/lists/*
WORKDIR /app2
COPY . /app2
RUN rm -rf .venv

RUN pip install --no-cache-dir -r requirements.txt

VOLUME /app2/upload
VOLUME /app2/output
VOLUME /app2/background

CMD ["python", "main.py"]