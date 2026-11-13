FROM postgres:18.0-alpine@sha256:48c8ad3a7284b82be4482a52076d47d879fd6fb084a1cbfccbd551f9331b0e40
# Retain upstream initialization, using Alpine's small privilege-drop helper.
# Removing the old Go-based gosu eliminates its bundled vulnerable Go runtime.
RUN apk upgrade --no-cache && apk add --no-cache su-exec \
    && grep -q 'exec gosu postgres' /usr/local/bin/docker-entrypoint.sh \
    && sed -i 's/exec gosu postgres/exec su-exec postgres/' /usr/local/bin/docker-*.sh \
    && rm /usr/local/bin/gosu
