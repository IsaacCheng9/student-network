var input = document.getElementById("search");
input.addEventListener("keyup", function(event) {
	if (event.keyCode === 13) {
	event.preventDefault();
	location.href = "/profile/" + input.value;
	}
});
