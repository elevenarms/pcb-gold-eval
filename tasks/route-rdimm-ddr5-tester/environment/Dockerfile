# syntax=docker/dockerfile:1
# Environment for route-rdimm-ddr5-tester. Every input is pinned (image digest, file sha256s, board commit).
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
RUN set -e; base="https://raw.githubusercontent.com/antmicro/rdimm-ddr5-tester/6bd485778de747d0e34551c4c34d2419e2c2d5b9"; \
    curl -fsSL -o /tmp/gold.kicad_pcb "$base/data-center-rdimm-ddr5-tester.kicad_pcb" && echo "2d5e5a547689ca3fd14682c21f077e658007f5245c473c6598c4785c8adaa6dc  /tmp/gold.kicad_pcb" | sha256sum -c -; \
    curl -fsSL -o /app/board.kicad_pro "$base/data-center-rdimm-ddr5-tester.kicad_pro" && echo "bf66809ee42667212c29c0d4f2e704eaa3a93d0c2e9ac9584a86dddd1d173615  /app/board.kicad_pro" | sha256sum -c -; \
    curl -fsSL -o /app/board.kicad_dru "$base/data-center-rdimm-ddr5-tester.kicad_dru" && echo "2ea75f1eda038707dbd8a5e91316a61ed7c9626283c5fd3f2d20943ae0eb9980  /app/board.kicad_dru" | sha256sum -c -; \
    python3 /opt/pcbeval/pcbeval.py strip /tmp/gold.kicad_pcb /app/board.kicad_pcb 2>/dev/null; \
    rm -f /tmp/gold.kicad_pcb; chown -R kicad:kicad /app
USER kicad
