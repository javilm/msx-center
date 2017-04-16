// Link event to the submit button
$("#saveButton").click(function (e) {
	e.preventDefault();
	console.log("Save button pressed");

	$.ajax({
		method: "POST",
		processData: true,
		data: {
			desc_en: $('#field_desc_en').val(),
			desc_ja: $('#field_desc_ja').val(),
			desc_nl: $('#field_desc_nl').val(),
			desc_es: $('#field_desc_es').val(),
			desc_pt: $('#field_desc_pt').val(),
			desc_kr: $('#field_desc_kr').val(),
			url: $('#field_url').val(),
			title: $('#field_title').val(),
		},
		success: function(data) {
			window.location = data.url;
		},
		error: function(jqXHR, textStatus, errorThrown) {
			alert("textStatus: " + textStatus + ", errorThrown: " + errorThrown);
		}
	})
	.done(function(result) {
	    window.location = result.url;
	});
	$("#saveButton").prop("disabled", true);
});
