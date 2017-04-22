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

			// Container DIV
			var div = $('<div></div>', {
				id: "link_div_" + data.id,
				class: 'related-link'
			});

			// Hidden INPUT field with the link value
			var hidden_field = $('<input />', {
				type: 'hidden',
				name: 'array_related_links',
				value: data.id
			});
			$(div).append(hidden_field);

			// "Remove" button
			var remove_link = $('<button></button>', {
				class: "btn btn-danger btn-xs",
				onclick: "$('#link_div_" + data.id + "').remove()",
				text: 'Remove'
			});
			$(div).append(remove_link);	

			// <span> for the title
			var title_span = $('<span></span>');

			// <a> tag to the link's URL
			var link_anchor = $('<a></a>', {
				href: data.url,
				id: 'link_anchor_' + data.id,
				target: '_new',
				text: data.title
			});
			$(title_span).append(link_anchor)
			$(div).append(title_span);
			
			// Add the Container to the document
			$('#div_related_links').append(div);
		}
	})	
});