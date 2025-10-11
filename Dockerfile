FROM odoo:18.0

USER root

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for pos_delivery module
RUN pip3 install --no-cache-dir --break-system-packages qrcode[pil]

# Clone enterprise addons
ARG GITHUB_TOKEN
RUN if [ -n "$GITHUB_TOKEN" ]; then \
    git clone --depth 1 --branch 18.0 \
    https://${GITHUB_TOKEN}@github.com/odoo/enterprise.git \
    /mnt/enterprise-addons; \
    fi

USER odoo

