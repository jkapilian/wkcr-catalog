$(document).ready(function() {
	$("#search-form").submit(function(e) {
		e.preventDefault();
		search();
	});

	$("#open").click(function() {
		console.log('clicked!')
		window.open(this.dataset.link, '_blank');
	});

	fixContent();

	$(window).resize(fixContent);
});

function search() {
	let query = $("#search").val().trim();
	if (query) {
		window.location.href = "/search/" + query;
	}
}

function fixContent() {
	$(".main-content").css("margin-top", $("#navbar").css("height"));
}