FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
RUN npm install --no-save @opentelemetry/api @opentelemetry/auto-instrumentations-node @opentelemetry/sdk-node
COPY . .
EXPOSE 8004
CMD ["npm","start"]
