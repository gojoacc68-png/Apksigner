FROM eclipse-temurin:17-jdk-jammy

RUN apt-get update && apt-get install -y unzip wget python3 python3-pip && \
    wget -q https://dl.google.com/android/repository/build-tools_r34_linux.zip && \
    unzip -q build-tools_r34_linux.zip && mv android-14 /opt/build-tools && \
    rm build-tools_r34_linux.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY app.py base.apk ./

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "--timeout", "120", "app:app"]
