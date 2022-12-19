import { sveltekit } from '@sveltejs/kit/vite';

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
      '/api': 'http://[::1]:8000',
      '/pics': 'http://[::1]:8000',
      '/ws': {
        target: 'ws://[::1]:8000',
        ws: true
      }
    }
  }
};

export default config;
