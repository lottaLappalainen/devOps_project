FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libcurl4-openssl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY main.cpp .
RUN g++ -std=c++17 main.cpp -o service2 -lcurl

EXPOSE 8300
CMD ["./service2"]
