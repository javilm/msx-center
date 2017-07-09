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

