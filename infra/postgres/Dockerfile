FROM postgres:18.6-alpine@sha256:9ba53c7d41ea093baf5c1ba635ba5434c4f979880527d49bb7d9237d3193085b
# Retain upstream initialization, using Alpine's small privilege-drop helper.
# Removing the old Go-based gosu eliminates its bundled vulnerable Go runtime.
RUN apk upgrade --no-cache && apk add --no-cache su-exec \
    && grep -q 'exec gosu postgres' /usr/local/bin/docker-entrypoint.sh \
    && sed -i 's/exec gosu postgres/exec su-exec postgres/' /usr/local/bin/docker-*.sh \
    && rm /usr/local/bin/gosu
