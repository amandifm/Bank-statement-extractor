// Server entry point
const app = require('./app');
const { connectDB } = require('./config/db');
const env = require('./config/env');

const PORT = env.PORT;

const startServer = async () => {
  try {
    await connectDB();
    
    // Start server
    const server = app.listen(PORT, () => {
      console.log(`Server is running on port ${PORT}`);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => {
      console.log('SIGTERM signal received: closing HTTP server');
      server.close(() => {
        console.log('HTTP server closed');
      });
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();
