self.addEventListener('message', async (event) => {
	const { id, code } = event.data;

	let result = null;
	let stdout = '';
	let stderr = '';

	try {
		const consolelog = console.log;
		const consoleError = console.error;

		console.log = (...args) => {
			stdout += args.join(' ') + '\n';
		};

		console.error = (...args) => {
			stderr += args.join(' ') + '\n';
		};

		result = eval(code);

		console.log = consolelog;
		console.error = consoleError;

		self.postMessage({
			id,
			stdout,
			stderr,
			result: result !== null || result !== undefined ? String(result) : '[NO OUTPUT]'
		});
	} catch (error) {
		stderr = String(error);
		self.postMessage({ id, stdout, stderr, result: null });
	}
});
