import { sveltekit } from '@sveltejs/kit/vite'

/** @type {import('vite').UserConfig} */
const config = {
  plugins: [sveltekit()],
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}']
  },
  //  build: {
  //    emptyOutDir: false,
  //  },
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': 'http://localhost:8113',
      '/pics': 'http://localhost:8113',
      '/ws': {
        target: 'ws://localhost:8113',
        ws: true
      }
    }
  }
}

export default config
