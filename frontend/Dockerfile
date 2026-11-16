FROM node:26.13.1-alpine@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5
RUN apk upgrade --no-cache && npm install --global npm@12.2.2 --no-audit --no-fund
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY --chown=node:node . .
RUN chown -R node:node /app
USER node
EXPOSE 5173
CMD ["npm", "run", "dev"]
