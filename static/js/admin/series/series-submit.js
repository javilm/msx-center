// Link event to the submit button
$("#saveButton").click(function (e) {
	e.preventDefault();

	$.ajax({
		method: "POST",
		processData: true,
		data: {
			title_en: $('#field_title_en').val(),
			title_ja: $('#field_title_ja').val(),
			title_nl: $('#field_title_nl').val(),
			title_es: $('#field_title_es').val(),
			title_pt: $('#field_title_pt').val(),
			title_kr: $('#field_title_kr').val(),
			desc_en: $('#field_desc_en').val(),
			desc_ja: $('#field_desc_ja').val(),
			desc_nl: $('#field_desc_nl').val(),
			desc_es: $('#field_desc_es').val(),
			desc_pt: $('#field_desc_pt').val(),
			desc_kr: $('#field_desc_kr').val(),
			slug: $('#field_slug').val(),
			title: $('#field_title').val(),
			category_id: $('#field_category_id').val(),
			is_hidden: $('#field_is_hidden').is(':checked')?'on':'off',
			is_numbered: $('#field_is_numbered').is(':checked')?'on':'off'
		},
		success: function(data) {
			window.location = data.url;
		}
	})
	.done(function(result) {
	    window.location = result.url;
	});
});
