FROM node:20-slim

WORKDIR /app/personaforge/web

COPY personaforge/web/package*.json ./
RUN npm install

COPY personaforge/web/ ./
RUN npm run build

# Next.js development server for POC (can be changed to production later)
CMD ["npm", "run", "dev"]
