typescriptEslint = require("typescript-eslint");
prettier = require("eslint-config-prettier");
js = require("@eslint/js");

module.exports = [
	{
		ignores: ["**/node_modules", "static/**", "**/build"],
	},
	js.configs.recommended,
	...typescriptEslint.configs.recommended,
	prettier,
];
