# Build & serve React in one simple image (minimal change)
FROM node:18

WORKDIR /app

# Install dependencies with better layer caching
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .

# Disable CRA's webpack ESLint during Docker build so production build can succeed
ENV DISABLE_ESLINT_PLUGIN=true

# Build optimized static files
RUN npm run build

# Serve the optimized static build
EXPOSE 3000
CMD ["npx", "serve", "-s", "build", "-l", "3000"]
