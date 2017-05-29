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

var reply_editor = new Quill('#reply_editor' , {
	modules : {
		toolbar: toolbarOptions
	},
	theme: 'snow'
});

// Link event to the submit button
$("#submit_button").click(function (e) {
	e.preventDefault();

	$.ajax({
		method: "POST",
		processData: true,
		data: {
			reply: reply_editor.root.innerHTML
		}
	})
	.done(function(result) {
		window.location = result.url;
	});
	return false;
});	
