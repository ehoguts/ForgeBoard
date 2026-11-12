FROM node:24.22.0-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY --chown=node:node . .
RUN chown -R node:node /app
USER node
EXPOSE 5173
CMD ["npm", "run", "dev"]
