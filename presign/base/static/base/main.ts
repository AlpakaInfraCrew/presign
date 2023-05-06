window.addEventListener("load", () => {
	setupFormsAutoSlugify();
});

function setupFormsAutoSlugify() {
	(
		document.querySelectorAll(
			"[data-auto-slugify-from]"
		) as NodeListOf<HTMLInputElement>
	).forEach((elem: HTMLInputElement) => {
		const slugifyFrom = elem.dataset.autoSlugifyFrom;
		if (!slugifyFrom) {
			return;
		}
		let sourceElems: NodeListOf<HTMLInputElement> = document.querySelectorAll(
			`input[name="${CSS.escape(slugifyFrom)}"]`
		);
		if (sourceElems.length == 0) {
			sourceElems = document.querySelectorAll(
				`input[name^="${CSS.escape(slugifyFrom)}_"]`
			);
		}

		const onInput = () => {
			let event_name = "";
			for (const elem of sourceElems) {
				event_name = elem.value;
				if (event_name) {
					break;
				}
			}

			const slug = slugify(event_name);
			const auto_slug = elem.dataset.slugifyAutoValue || "";
			const slug_value = elem.value;
			if (auto_slug === slug_value) {
				elem.value = slug;
				elem.dataset.slugifyAutoValue = slug;
			}
		};
		sourceElems.forEach((e) => e.addEventListener("input", onInput));
	});
}
function slugify(text: string) {
	return text
		.normalize("NFD")
		.replace(/[\u0300-\u036f]/g, "")
		.toLowerCase()
		.trim()
		.replace(/\s+/g, "-")
		.replace(/[^\w-]+/g, "")
		.replace(/--+/g, "-");
}
