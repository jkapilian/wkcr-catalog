$(document).ready(function() {
	$("#search").keydown(e => {
		if (e.which == 13) {
			search();
		}
	});
	$("#search-button").click(() => search());
});

function search() {
	let query = $("#search").val().trim();
	if (query) {
		window.location.href = "/search/" + query;
	}
}