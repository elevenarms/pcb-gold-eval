# syntax=docker/dockerfile:1
# Environment for route-gmsl-deserializer. Every input is pinned (image digest, file sha256s, board commit).
FROM --platform=linux/amd64 kicad/kicad:10.0.7@sha256:3224d1bf143185ecc1bd3a1082a36f37f0f4e59d707983a16515a845e3737fc6
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates python3-pip git build-essential \
    && rm -rf /var/lib/apt/lists/*
# Java 25 (Freerouting 2.5 needs >= 25) and Freerouting, both sha256-pinned
RUN curl -fsSL -o /tmp/jdk.tgz "https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.5%2B8/OpenJDK25U-jdk_x64_linux_hotspot_25.0.5_8.tar.gz" && echo "68982529869257d0ee6b824ec5aa270ff8b118bb438670da0b97ebdab178d7fb  /tmp/jdk.tgz" | sha256sum -c - \
    && mkdir -p /opt/jdk && tar -xzf /tmp/jdk.tgz -C /opt/jdk --strip-components=1 && rm /tmp/jdk.tgz \
    && curl -fsSL -o /opt/freerouting.jar "https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar" && echo "f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7  /opt/freerouting.jar" | sha256sum -c -
ENV PATH=/opt/jdk/bin:$PATH
COPY pcbeval.py /opt/pcbeval/pcbeval.py
# Fetch the human-routed gold board, strip its copper and delete it in ONE layer: the agent never sees the gold.
WORKDIR /app
RUN set -e; base="https://raw.githubusercontent.com/antmicro/gmsl-deserializer/43d9aad97bb4ee6b41d31b778ddc4b8d0eceaa63"; \
    curl -fsSL -o /tmp/gold.kicad_pcb "$base/gmsl-deserializer.kicad_pcb" && echo "85ce074fbe28119dd255a336a26358324c64322e60c6e1279d474e0bc3ce87d2  /tmp/gold.kicad_pcb" | sha256sum -c -; \
    curl -fsSL -o /app/board.kicad_pro "$base/gmsl-deserializer.kicad_pro" && echo "f2bdae84b017ad83052f27f376db36fe776f373c24fb8b3760de74f689c279a2  /app/board.kicad_pro" | sha256sum -c -; \
    python3 /opt/pcbeval/pcbeval.py strip /tmp/gold.kicad_pcb /app/board.kicad_pcb 2>/dev/null; \
    rm -f /tmp/gold.kicad_pcb; chown -R kicad:kicad /app
USER kicad
