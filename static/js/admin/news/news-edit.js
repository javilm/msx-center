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
	console.log("Save button pressed");

	$.ajax({
		method: "POST",
		processData: true,
		data: {
			headline_en: $('#field_headline_en').val(),
			subhead_en: $('#field_subhead_en').val(),
			summary_en: $('#field_summary_en').val(),
			body_en: quill_en.root.innerHTML,
			is_draft_en: $('#field_is_draft_en').is(':checked')?'on':'off',
			headline_ja: $('#field_headline_ja').val(),
			subhead_ja: $('#field_subhead_ja').val(),
			summary_ja: $('#field_summary_ja').val(),
			body_ja: quill_ja.root.innerHTML,
			is_draft_ja: $('#field_is_draft_ja').is(':checked')?'on':'off',
			headline_nl: $('#field_headline_nl').val(),
			subhead_nl: $('#field_subhead_nl').val(),
			summary_nl: $('#field_summary_nl').val(),
			body_nl: quill_nl.root.innerHTML,
			is_draft_nl: $('#field_is_draft_nl').is(':checked')?'on':'off',
			headline_es: $('#field_headline_es').val(),
			subhead_es: $('#field_subhead_es').val(),
			summary_es: $('#field_summary_es').val(),
			body_es: quill_es.root.innerHTML,
			is_draft_es: $('#field_is_draft_es').is(':checked')?'on':'off',
			headline_pt: $('#field_headline_pt').val(),
			subhead_pt: $('#field_subhead_pt').val(),
			summary_pt: $('#field_summary_pt').val(),
			body_pt: quill_pt.root.innerHTML,
			is_draft_pt: $('#field_is_draft_pt').is(':checked')?'on':'off',
			headline_kr: $('#field_headline_kr').val(),
			subhead_kr: $('#field_subhead_kr').val(),
			summary_kr: $('#field_summary_kr').val(),
			body_kr: quill_kr.root.innerHTML,
			is_draft_kr: $('#field_is_draft_kr').is(':checked')?'on':'off',
			author_id: $('#field_author_id').val(),
            slug: $('#field_slug').val(),
            category_id: $('#field_category_id').val(),
			header_image_id: $('#field_image_id').val(),
			date_published: $('#field_date_published').val(),
			is_feature: $('#field_is_feature').is(':checked')?'on':'off',
			is_hidden: $('#field_is_hidden').is(':checked')?'on':'off',
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
			alert("textStatus: " + textStatus + ", errorThrown: " + errorThrown);
		}
	});
	//.done(function(result) {
	//    window.location = result.url;
	//});
	quill_en.enable(false);
	quill_ja.enable(false);
	quill_nl.enable(false);
	quill_es.enable(false);
	quill_pt.enable(false);
	quill_kr.enable(false);
	$("#saveButton").prop("disabled", true);
});	

// Link event to the upload button
$("#uploadButton").click(function (e) {
	e.preventDefault();
	console.log("Upload button pressed");

	var fd = new FormData(document.getElementById('feature_image_form'));

	$.ajax({
		data: fd,
		url: '/admin/news/add/feature_image',
		processData: false,
		contentType: false,
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

