window.addEventListener("load", () => {
	(
		document.querySelectorAll(
			"[data-auto-slugify-from]"
		) as NodeListOf<HTMLInputElement>
	).forEach((elem: HTMLInputElement) => {
		const slugifyFrom = elem.dataset.autoSlugifyFrom;
		if (!slugifyFrom) {
			return;
		}
		const sourceElem = document.querySelector(
			`input[name=${CSS.escape(slugifyFrom)}]`
		);
		if (!sourceElem) {
			return;
		}
		const onInput: { (event: InputEvent): void } = (event: InputEvent) => {
			const event_name = (event.target as HTMLInputElement).value;
			const slug = slugify(event_name);
			console.log(slug);
			const auto_slug = elem.dataset.slugifyAutoValue || "";
			const slug_value = elem.value;
			console.log(`'${slug_value}' '${auto_slug}'`, auto_slug !== slug_value);
			if (auto_slug === slug_value) {
				elem.value = slug;
				elem.dataset.slugifyAutoValue = slug;
			}
		};
		sourceElem.addEventListener("input", onInput as EventListener);
	});
});

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
