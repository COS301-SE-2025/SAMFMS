# Use an official Node.js image as the base
FROM node:18

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies including http-proxy-middleware for WebSocket proxy
RUN npm install
RUN npm install http-proxy-middleware --save-dev

# Copy the rest of the app's source code
COPY . .

# Expose the port the app runs on
EXPOSE 3000

# Start the React app
CMD ["npm", "start"]