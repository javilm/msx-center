// If the comments have iframes in them, wrap then in a div that will scale them to the width of the container
$('iframe').wrap('<div class="iframe-wrapper" />');

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
var quill = new Quill('#reply_editor' , {
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
	$('#reply_editor').prop('disabled', true);
	button.addClass('disabled');
	button.html('Posting, please wait...');

	// Clear the error message
	$('#comment_post_error').html('&nbsp;');

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
			$("#reply_editor").prop("disabled", false);
			button.removeClass('disabled');
			button.html('Post reply');
		}
	})
	.done(function(result) {
		if (result.status == '200') {
			window.location = result.url;
		} else {
			$('#comment_post_error').html(result.status_message);
		}
	});
	return false;
});
