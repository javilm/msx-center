// Initialize Quill editors
var toolbarOptions = [
	[{ 'header': [1, 2, 3, false] }],
	[{ 'size': ['small', false, 'large', 'huge'] }],  // custom dropdown
	['bold', 'italic', 'underline', 'strike'],        // toggled buttons
	[{ 'color': [] },],          // dropdown with defaults from theme
	['link', 'image', 'video', 'blockquote', 'code-block'],
	[{ 'list': 'ordered'}, { 'list': 'bullet' }],
	[{ 'indent': '-1'}, { 'indent': '+1' }],          // outdent/indent
];

var quill_en = new Quill('#quillEditor_en' , {
	modules : {
		toolbar: toolbarOptions
	},
	theme: 'snow'
});
var quill_ja = new Quill('#quillEditor_ja' , {
	modules : {
		toolbar: toolbarOptions
	},
	theme: 'snow'
});
var quill_nl = new Quill('#quillEditor_nl' , {
	modules : {
		toolbar: toolbarOptions
	},
	theme: 'snow'
});
var quill_es = new Quill('#quillEditor_es' , {
	modules : {
		toolbar: toolbarOptions
	},
	theme: 'snow'
});
var quill_pt = new Quill('#quillEditor_pt' , {
	modules : {
		toolbar: toolbarOptions
	},
	theme: 'snow'
});
var quill_kr = new Quill('#quillEditor_kr' , {
	modules : {
		toolbar: toolbarOptions
	},
	theme: 'snow'
});

// Initialize datepicker
$(function () {
	$("#field_date_published").datepicker({
		changeMonth: true,
		changeYear: true,
		yearRange: "2013:2020",
		dateFormat: 'DD MM d, yy'
	});
	// Code here to initialize the datepicker to the date entered in the form, or today's date if not especified
	var date = Date.now()
	$("#field_date_published").datepicker("setDate", date);
});

// Link event to the submit button
$("#saveButton").click(function (e) {
	e.preventDefault();

	$.ajax({
		method: "POST",
		processData: true,
		data: {
			title_en: $('#field_title_en').val(),
			summary_en: $('#field_summary_en').val(),
			body_en: quill_en.root.innerHTML,
			is_draft_en: $('#field_is_draft_en').is(':checked')?'on':'off',

			title_ja: $('#field_title_ja').val(),
			summary_ja: $('#field_summary_ja').val(),
			body_ja: quill_ja.root.innerHTML,
			is_draft_ja: $('#field_is_draft_ja').is(':checked')?'on':'off',

			title_nl: $('#field_title_nl').val(),
			summary_nl: $('#field_summary_nl').val(),
			body_nl: quill_nl.root.innerHTML,
			is_draft_nl: $('#field_is_draft_nl').is(':checked')?'on':'off',

			title_es: $('#field_title_es').val(),
			summary_es: $('#field_summary_es').val(),
			body_es: quill_es.root.innerHTML,
			is_draft_es: $('#field_is_draft_es').is(':checked')?'on':'off',

			title_pt: $('#field_title_pt').val(),
			summary_pt: $('#field_summary_pt').val(),
			body_pt: quill_pt.root.innerHTML,
			is_draft_pt: $('#field_is_draft_pt').is(':checked')?'on':'off',

			title_kr: $('#field_title_kr').val(),
			summary_kr: $('#field_summary_kr').val(),
			body_kr: quill_kr.root.innerHTML,
			is_draft_kr: $('#field_is_draft_kr').is(':checked')?'on':'off',

			author_id: $('#field_author_id').val(),
			category_id: $('#field_category_id').val(),
			series_id: $('#field_series_id').val(),
			chapter: $('#field_chapter').val(),
			priority: $('#field_priority').val(),
			level: $('#field_level').val(),
			slug: $('#field_slug').val(),
			header_image_id: $('#field_image_id').val(),
			date_published: $('#field_date_published').val(),
			is_hidden: $('#field_is_hidden').is(':checked')?'on':'off',
			is_published: $('#field_is_published').is(':checked')?'on':'off',
			is_pinned: $('#field_is_pinned').is(':checked')?'on':'off',
			is_archived: $('#field_is_archived').is(':checked')?'on':'off',
			allows_comments: $('#field_allows_comments').is(':checked')?'on':'off',
			links: JSON.stringify($("input[name='array_related_links']")
					.map(function() {
						return $(this).val();
					})
					.get())
		},
		success: function(data) {
			window.location = data.url;
		},
		error: function(jqXHR, textStatus, errorThrown) {
			console.log("textStatus: " + textStatus + ", errorThrown: " + errorThrown);
		}
	});
});	

// Link event to the upload button
$("#uploadButton").click(function (e) {
	e.preventDefault();

	var fd = new FormData(document.getElementById('feature_image_form'));

	$.ajax({
		data: fd,
		processData: false,
		contentType: false,
		url: '/admin/articles/add/feature_image',
		method: 'POST',
		success: function(data) {
			if (data.success == true) {
				$("#feature_image_img").remove();
				$("#feature_image_div").append('<img id="feature_image_img" class="img-responsive" src="/image/' + data.image_id + '/feature_image">');
				$("#field_image_id").val(data.image_id);
				console.log(JSON.stringify(data));
			} else {
				$("#feature_image_img").remove();
			}
		}
	});
});

