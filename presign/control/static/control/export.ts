window.addEventListener("load", () => {
	const selectButton = document.getElementById(
		"select_all_fields"
	) as HTMLButtonElement;
	const deselectButton = document.getElementById(
		"deselect_all_fields"
	) as HTMLButtonElement;
	selectButton.addEventListener("click", () =>
		setAllCheckbox("id_fields", true)
	);
	deselectButton.addEventListener("click", () =>
		setAllCheckbox("id_fields", false)
	);
});

function setAllCheckbox(parent_id, checked) {
	(
		document
			.getElementById(parent_id)
			?.querySelectorAll(
				'input[type="checkbox"]'
			) as NodeListOf<HTMLInputElement>
	).forEach((e: HTMLInputElement) => (e.checked = checked));
}
