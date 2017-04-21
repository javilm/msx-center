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

// Link event to the button to add related links
$("#button_add_link").click(function (e) {
	e.preventDefault();

	var link_id = $('#field_link_id').val();

	// Make a request to the server to retrieve the link's URL and title
	$.ajax({
		statusCode: {
			401: function() {
				alert('Credentials expired. Please sign in again');
			},
			404: function() {
				alert("The selected link doesn't exist. Please reload the page.");
			}
		},
		url: '/admin/link/' + link_id + '/info',
		method: 'GET',
		success: function(data, textStatus, jqXHR) {
			var div = $('<div></div>', {
				id: "link_div_" + data.id
			});

			var hidden_field = $('<input />', {
				type: 'hidden',
				name: 'array_related_links',
				value: data.id
			});
			var link_anchor = $('<a></a>', {
				href: data.url,
				id: 'link_anchor_' + data.id
			});
			var link_title = $('<strong></strong>', {
				id: 'link_title_' + data.id
			});
			var remove_link = $('<a></a>', {
				onclick: "$('#link_div_" + data.id + "').remove()",
				text: '(remove)'
			});

			link_anchor.append(link_title)
			$(div).append(hidden_field);
			$(div).append(link_anchor);
			$(div).append(remove_link);	
			
			$('#div_related_links').append(div);
		}
	})	
});

// Link event to the submit button
$("#saveButton").click(function (e) {
	e.preventDefault();

	$.ajax({
		method: "POST",
		processData: true,
		data: {
			'en': {
				headline: $('#field_headline_en').val(),
				subhead: $('#field_subhead_en').val(),
				summary: $('#field_summary_en').val(),
				body: quill_en.root.innerHTML,
				is_draft: $('#field_is_draft_en').is(':checked')?'on':'off'
			},
			'ja': {
				headline: $('#field_headline_ja').val(),
				subhead: $('#field_subhead_ja').val(),
				summary: $('#field_summary_ja').val(),
				body: quill_ja.root.innerHTML,
				is_draft: $('#field_is_draft_ja').is(':checked')?'on':'off'
			},
			'nl': {
				headline: $('#field_headline_nl').val(),
				subhead: $('#field_subhead_nl').val(),
				summary: $('#field_summary_nl').val(),
				body: quill_nl.root.innerHTML,
				is_draft: $('#field_is_draft_nl').is(':checked')?'on':'off'
			},
			'es': {
				headline: $('#field_headline_es').val(),
				subhead: $('#field_subhead_es').val(),
				summary: $('#field_summary_es').val(),
				body: quill_es.root.innerHTML,
				is_draft: $('#field_is_draft_es').is(':checked')?'on':'off'
			},
			'pt': {
				headline: $('#field_headline_pt').val(),
				subhead: $('#field_subhead_pt').val(),
				summary: $('#field_summary_pt').val(),
				body: quill_pt.root.innerHTML,
				is_draft: $('#field_is_draft_pt').is(':checked')?'on':'off'
			},
			'kr': {
				headline: $('#field_headline_kr').val(),
				subhead: $('#field_subhead_kr').val(),
				summary: $('#field_summary_kr').val(),
				body: quill_kr.root.innerHTML,
				is_draft: $('#field_is_draft_kr').is(':checked')?'on':'off'
			},
			author_id: $('#field_author_id').val(),
			slug: $('#field_slug').val(),
			category_id: $('#field_category_id').val(),
			header_image_id: $('#field_image_id').val(),
			date_published: $('#field_date_published').val(),
			is_feature: $('#field_is_feature').is(':checked')?'on':'off',
			is_hidden: $('#field_is_hidden').is(':checked')?'on':'off',
			allows_comments: $('#field_allows_comments').is(':checked')?'on':'off'
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
		processData: false,
		contentType: false,
		url: '/admin/news/add/feature_image',
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

