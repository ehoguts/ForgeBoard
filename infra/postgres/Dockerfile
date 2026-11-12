FROM postgres:16.16-alpine@sha256:0adbf25a9e96d38823bb813f3ac0ed41fadb665c88f1df7fe6dbfb060cbdc106
# Retain upstream initialization, using Alpine's small privilege-drop helper.
# Removing the old Go-based gosu eliminates its bundled vulnerable Go runtime.
RUN apk upgrade --no-cache && apk add --no-cache su-exec \
    && grep -q 'exec gosu postgres' /usr/local/bin/docker-entrypoint.sh \
    && sed -i 's/exec gosu postgres/exec su-exec postgres/' /usr/local/bin/docker-*.sh \
    && rm /usr/local/bin/gosu
