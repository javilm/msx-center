$(".button-comment-upvote").click(function (e) {
	e.preventDefault();

	var comment_id = $(this).attr('comment_id')

	$.ajax({
		method: 'GET',
		dataType: 'json',
		processData: true,
		url: 'https://dev.msx-center.com/message/' + comment_id  + '/upvote',
		success: function(data) {
			if (data.result == '200') {
				$('#button_comment_' + comment_id + '_upvote').addClass('btn-success disabled').removeClass('btn-default');
				$('#button_comment_' + comment_id + '_score').html(data.score);
				$('#button_comment_' + comment_id + '_downvote').addClass('disabled');
				console.log('New score is ' + data.score);
			} else {
				console.log('Upvote rejected.');
			}
		}
	});
});

$(".button-comment-downvote").click(function (e) {
	e.preventDefault();

	var comment_id = $(this).attr('comment_id')

	$.ajax({
		method: 'GET',
		dataType: 'json',
		processData: true,
		url: 'https://dev.msx-center.com/message/' + comment_id + '/downvote',
		success: function(data) {
			if (data.result == '200') {
				$('#button_comment_' + comment_id + '_upvote').addClass('disabled');
				$('#button_comment_' + comment_id + '_score').html(data.score);
				$('#button_comment_' + comment_id + '_downvote').addClass('btn-danger disabled').removeClass('btn-default');
				console.log('New score is ' + data.score);
			} else {
				console.log('Downvote rejected.');
			}
		}
	});
});

