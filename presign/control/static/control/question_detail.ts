const CHOICE_KINDS = ["M", "C"];

let optionEditor: HTMLDivElement | null;
let kindField: HTMLSelectElement | null;
let emptyForm: HTMLElement | null;

window.addEventListener("load", () => {
	optionEditor = document.getElementById("option-editor") as HTMLDivElement;

	kindField = document.getElementById("id_kind") as HTMLSelectElement;
	kindChanged();
	kindField.addEventListener("change", kindChanged);

	setupAddOptionButton();
});

function kindChanged() {
	if (optionEditor === null || kindField === null) {
		return;
	}
	console.log(kindField.value, CHOICE_KINDS.includes(kindField.value));
	if (CHOICE_KINDS.includes(kindField.value)) {
		optionEditor.style.display = "block";
	} else {
		optionEditor.style.display = "none";
	}
}

function setupAddOptionButton() {
	if (optionEditor === null || kindField === null) {
		return;
	}
	const forms = optionEditor.querySelectorAll(".formset-form");
	if (forms.length < 1) {
		return;
	}
	emptyForm = forms[forms.length - 1].cloneNode(true) as HTMLElement;

	const addOptionButton = document.getElementById(
		"add-option",
	) as HTMLButtonElement;
	console.log(addOptionButton);
	addOptionButton.addEventListener("click", addOptionForm);
}

function addOptionForm() {
	if (optionEditor === null || kindField === null || emptyForm === null) {
		return;
	}

	const formsetContainer = optionEditor.querySelector(".formset-container");
	const totalForms = document.getElementById(
		"id_form-TOTAL_FORMS",
	) as HTMLInputElement;
	if (formsetContainer === null || totalForms === null) {
		return;
	}

	const newForm = emptyForm.cloneNode(true) as HTMLElement;

	const formNum = optionEditor.querySelectorAll(".formset-form").length;
	newForm.innerHTML = newForm.innerHTML.replace(
		/form-\d+-/g,
		`form-${formNum}-`,
	);
	formsetContainer.insertAdjacentElement("beforeend", newForm);
	totalForms.value = (formNum + 1).toString();
}
