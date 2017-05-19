// Initialize MediumEditor
var toolbarOptions = [
	[{ 'header': [1, 2, 3, false] }],
	[{ 'size': ['small', false, 'large', 'huge'] }],  // custom dropdown
	['bold', 'italic', 'underline', 'strike'],        // toggled buttons
	[{ 'color': [] },],          // dropdown with defaults from theme
	['link', 'image', 'video', 'blockquote', 'code-block'],
	[{ 'list': 'ordered'}, { 'list': 'bullet' }],
	[{ 'indent': '-1'}, { 'indent': '+1' }],          // outdent/indent
];
var quill = new Quill('#quillEditor' , {
	modules : {
		toolbar: toolbarOptions
	},
	theme: 'snow'
});

// Attach event to button
$("#submitButton").click(function (e) {
	e.preventDefault();

	var button = $(this);

	// Disable input
	quill.enable(false);
	$('#quillEditor').prop('disabled', true);
	button.addClass('disabled');
	button.html('Posting, please wait...');

	$.ajax({
		method: "POST",
		processData: true,
		dataType: 'json',
		data: {
			thread_id: $('#field_thread_id').val(),
			post_as: $('#field_post_as').val(),
			message: quill.root.innerHTML
		},
		complete: function(request, status) {
			quill.enable(true);
			$("#quillEditor").prop("disabled", false);
			button.removeClass('disabled');
			button.html('Post reply');
		}
	})
	.done(function(result) {
		window.location = result.url;
	});
});
