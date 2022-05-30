function submitForm(formId, onSuccess) {
  var form = $(formId);
  var url = form.attr('action');

  // filter empty fields
  let data = $(formId + " :input")
      .filter((index, element) => $(element).val() != '')
      .serialize();

  // clean already existing errors
  form.find('.errors').empty();

  $.ajax({
    type: "POST",
    url: url,
    data: data,
    success: onSuccess,
    error: function(data) {
      let fields = data.responseJSON['errors']['form'];
      for (let [field, errors] of Object.entries(fields)) {
        let input = form.find('input[name=' + field + ']');
        let parentDiv = input.closest('.field');
        let errorContainer = parentDiv.find('.errors');
        for (let error of errors) {
          errorContainer.append('<p>' + error + '</p>');
        }
      }
    }
  });
}