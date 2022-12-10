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
    proxy: {
      '/api': 'http://localhost:8000',
    }
  }
};

export default config;
