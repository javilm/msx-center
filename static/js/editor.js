// Initialize MediumEditor - Insert Plugin
$(function() {
	$('.editable').mediumInsert({
		editor: editor,
		enabled: true,
		addons: {
			images: {
				label: '<span class="fa fa-camera"></span>',
				uploadScript: null, // DEPRECATED
				deleteScript: 'delete',
				deleteMethod: 'POST',
				fileDeleteOptions: {},
				preview: true,
				captions: true,
				captionPlaceHolder: 'Type caption for image (optional)',
				autoGrid: 3,
				formData: {},       // DEPRECATED
				fileUploadOptions: {
					url: 'upload',
					acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i
				},
				styles: {
					wide: {
						label: '<span class="fa fa-align-justify"></span>',
						added: function ($el) {},   // Callback function called after the style was selected
						removed: function ($el) {}  // Called after a different style was selected and this one removed
					},
					left: {
						label: '<span class="fa fa-align-left"></span>'
					},
					right: {
						label: '<span class="fa fa-align-right"></span>'
					},
					grid: {
						label: '<span class="fa fa-th"></span>'
					}
				},
				actions: {
					remove: {
						label: '<span class="fa fa-times"></span>',
						clicked: function ($el) {
							var $event = $.Event('keydown');

							$event.which = 8;
							$(document).trigger($event);
						}
					}
				},
				messages: {
					acceptFileTypesError: 'This file is not in a supported format: ',
					maxFileSizeError: 'This file is too big: '
				},
				uploadCompleted: function ($el, data) {},       // Called when upload completed
				uploadFailed: function (uploadErrors, data) {}  // Called when the upload failed
			},
			embeds: {
				label: '<span class="fa, fa-youtube-play"></span>',
				placeHolder: 'Paste a YouTube, Vimeo, Facebook, Twitter or Instagram link and press Enter',
				captions: true,
				captionPlaceholder: 'Type caption (optional)',
				oembedProxy: 'http://medium.iframe.ly/api/oembed?iframe=1',
				styles: {
					wide: {
						label: '<span class="fa fa-align-justify"></span>',
						added: function ($el) {},
						removed: function ($el) {}
					},
					left: {
						label: '<span class="fa fa-align-left"></span>'
					},
					right: {
						label: 'span class="fa fa-align-right"></span>'
					}
				},
				actions: {
					remove: {
						label: '<span class="fa fa-times"></span>',
						clicked: function ($el) {
							var $event = $.Event('keydown');

							$event.which = 8;
							$(document).trigger($event);
						}
					}
				}
			}
		}
	});
})

