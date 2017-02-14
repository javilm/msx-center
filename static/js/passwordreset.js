var minPasswordLength = 8;
var validPassLen = false;
var validPassCase = false;
var validPassNumb = false;

$("#submitButton").attr("disabled", "disabled");

// Initialize all popovers
$(function () {
  $('[data-toggle="popover"]').popover()
})

// Enable/disable the submit button depending on the status of the form
function updateButtonStatus()
{
	passwordsMatch = ($("#formPassword").val() == $("#formPasswordConfirm").val());
	if (validPassLen && validPassCase && validPassNumb && passwordsMatch) {
		$("#submitButton").attr("disabled", null);
	} else {
		$("#submitButton").attr("disabled", "disabled");
	}
}

function updatePopoverStatus()
{
	if ($("#formPasswordConfirm").val()) {
		if ($("#formPassword").val() == $("#formPasswordConfirm").val()) {
			$("#formPasswordConfirm").popover('hide');
		} else {
			$("#formPasswordConfirm").popover('show');
		}
	} else {
		$("#formPasswordConfirm").popover('hide');
	}
}

$("#formPassword").keyup(function() {

	var password = $("#formPassword").val();

	// Check that the password length is at least 8 characters
	if (password.length > 7) {
		$("#reqlen").removeClass("text-danger").addClass("text-success");
		validPassLen = true;
	} else {
		$("#reqlen").removeClass("text-success").addClass("text-danger");
		validPassLen = false;
	}

	// Check that the password contains uppercase and lowercase letters
	if (password.match(/[A-Z]/) && password.match(/[a-z]/)) {
		$("#reqcase").removeClass("text-danger").addClass("text-success");
		validPassCase = true;
	} else {
		$("#reqcase").removeClass("text-success").addClass("text-danger");
		validPassCase = false;
	}

	// Check that the password contains at least one number
	if (password.match(/[0-9]/)) {
		$("#reqnumb").removeClass("text-danger").addClass("text-success");
		validPassNumb = true;
	} else {
		$("#reqnumb").removeClass("text-success").addClass("text-danger");
		validPassNumb = false;
	}

	updatePopoverStatus();
	updateButtonStatus();
});

$("#formPasswordConfirm").keyup(function() {
	updatePopoverStatus();
	updateButtonStatus();
});
