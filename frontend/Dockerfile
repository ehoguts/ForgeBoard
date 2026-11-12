FROM node:26.13.0-alpine@sha256:8996bb5821d62a8fd9bb27c1cb07462f3fdce6e47d640c6a881ead0b064ce216
RUN apk upgrade --no-cache && npm install --global npm@12.2.2 --no-audit --no-fund
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY --chown=node:node . .
RUN chown -R node:node /app
USER node
EXPOSE 5173
CMD ["npm", "run", "dev"]
