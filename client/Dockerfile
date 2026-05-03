FROM nginx:alpine

# Copy client files to nginx html directory
COPY . /usr/share/nginx/html

# Create an entrypoint script to inject the environment variable into config.js
# This runs every time the container starts
RUN echo '#!/bin/sh' > /docker-entrypoint.d/99-env.sh && \
    echo 'echo "window.BACKEND_URL = '\''${BACKEND_URL:-http://localhost:4010}'\'';" > /usr/share/nginx/html/config.js' >> /docker-entrypoint.d/99-env.sh && \
    chmod +x /docker-entrypoint.d/99-env.sh

EXPOSE 80
