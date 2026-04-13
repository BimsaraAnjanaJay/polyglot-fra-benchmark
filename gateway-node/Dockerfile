FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
RUN npm install --no-save @opentelemetry/api @opentelemetry/auto-instrumentations-node @opentelemetry/sdk-node
COPY . .
EXPOSE 3000
CMD ["npm","start"]
