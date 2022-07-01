$(document).ready(function() {
	$("#search-form").submit(function(e) {
		e.preventDefault();
		search();
	});
});

function search() {
	let query = $("#search").val().trim();
	if (query) {
		window.location.href = "/search/" + query;
	}
}