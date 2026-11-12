FROM node:24.22.1-alpine@sha256:06d7adf3e0ef61a13f1d28682726366f97a15aa1888c934d3ecec86c33918b53
RUN apk upgrade --no-cache && npm install --global npm@12.2.2 --no-audit --no-fund
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY --chown=node:node . .
RUN chown -R node:node /app
USER node
EXPOSE 5173
CMD ["npm", "run", "dev"]
