import { sveltekit } from '@sveltejs/kit/vite';
import { execSync } from 'child_process';
import { defineConfig } from 'vite';
// import NodeRollupPolyfills from 'rollup-plugin-node-polyfills';
import packageJson from './package.json';

const buildHash = execSync('git rev-parse --short HEAD').toString().trim();
const fallbackVersion = packageJson.version;

// /** @type {import('vite').Plugin} */
// const viteServerConfig = {
// 	name: 'log-request-middleware',
// 	configureServer(server) {
// 		server.middlewares.use((req, res, next) => {
// 			res.setHeader('Access-Control-Allow-Origin', '*');
// 			res.setHeader('Access-Control-Allow-Methods', 'GET');
// 			res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
// 			res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
// 			next();
// 		});
// 	}
// };

export default defineConfig({
	server: {
		fs: {
			allow: ['.'] // Allows serving files from project root
		}
	},
	plugins: [sveltekit()],
	define: {
		APP_VERSION: JSON.stringify(process.env.npm_package_version) || JSON.stringify(fallbackVersion),
		APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build'),
		BUILD_HASH: JSON.stringify(buildHash)
	},
	build: {
		sourcemap: true
		// rollupOptions: {
		// 	plugins: [NodeRollupPolyfills({ crypto: true, fs: true })]
		// }
	},
	worker: {
		format: 'es'
	}
});
