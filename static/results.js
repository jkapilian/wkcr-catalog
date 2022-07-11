$(document).ready(function() {
	listResults();

	$("input").click(function() {
		filters[this.id] = this.checked;
		listResults();
	});
});

let filters = {
	"cd": true,
	"vinyl": true,
	"jazz": true,
	"classical": true,
	"nm": true,
}

const mapping = {
	"Jazz": "jazz",
	"Classical": "classical",
	"New": "nm",
	"CD": "cd",
	"Vinyl": "vinyl"
}

function listResults() {
	let count = 0;
	$("#results").empty();
	for (item of results) {
		let location = item.folder.split(' ');
		if (filters[mapping[location[0]]] && filters[mapping[location[location.length - 1]]]) {
			let container = $("<div class='result'>");
			let firstRow = $("<div class='row larger'>");
			let secondRow = $("<div class='row'>");
			container.append(firstRow);
			container.append(secondRow);

			let linkContainer = $("<div class='col-md-8'>");
			let link = $(`<a class='info' href='/view/${item.id}'>${item.title}</a>`);
			linkContainer.append(link)

			let locationContainer = $("<div class='col-md-4 right'>");
			let location = $("<b>");
			if (item.wkcr_location) {
				location.html(`${item.folder} ${item.wkcr_location[0].value}`);
			}
			else {
				location.html(`${item.folder}`);
			}
			locationContainer.append(location);

			firstRow.append(linkContainer);
			firstRow.append(locationContainer);

			let imageContainer = $("<div class='col-md-1'>");
			let imageLink = $(`<a href='/view/${item.id}'>`);
			let image = $(`<img class='full' src='${item.image}'>`);
			imageLink.append(image)
			imageContainer.append(imageLink);
			secondRow.append(imageContainer);

			let otherInfo = $("<div class='col-md-11'>");
			let otherInfoTop = $("<div class='row truncate info'>");
			let otherInfoBottom = $("<div class='row truncate'>");
			
			let artists = item.artists.reduce(
				(prev, cur, ind) => ind == (item.artists.length-1) ? prev += cur.name : prev += `${cur.name}, `, ""
			);
			let credits = item.credits.reduce(
				(prev, cur, ind) => ind == (item.credits.length-1) ? prev += cur.name : prev += `${cur.name}, `, ""
			);
			if (item.artists.length > 0 && item.credits.length > 0) {
				otherInfoTop.html(`${artists}, ${credits}`);
			}
			else if (item.artists.length == 0) {
				otherInfoTop.html(credits);
			}
			else {
				otherInfoTop.html(artists);
			}
			
			otherInfo.append(otherInfoTop);

			let tracks = item.tracklist.reduce(
				(prev, cur, ind) => ind == (item.tracklist.length-1) ? prev += cur : prev += `${cur}, `, ""
			);
			otherInfoBottom.html(`Tracks: <span class='info'>${tracks}</span>`)
			otherInfo.append(otherInfoBottom);
			secondRow.append(otherInfo);


			$("#results").append(container);
			count ++;
		}
	}

	$("#num-results").html(
		`${count === 0 ? 'No' : count} result${count === 1 ? '' : 's'} found`
	);

	let regex = new RegExp(term, "i");
	$(".info").each(function(_, element) {
		$(element).html($(element).html().replace(regex, "<span class='bold'>$&</span>"))
	});
}