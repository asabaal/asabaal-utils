import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        watch: {
            usePolling: true,
        },
        // Add this to serve files from the public directory
        publicDir: 'public',
    }
});