(function () {
  document.addEventListener('click', function (event) {
    var trigger = event.target.closest('[data-survey-popup]');
    if (trigger) {
      var dialog = document.getElementById(trigger.dataset.surveyPopup);
      if (dialog && typeof dialog.showModal === 'function') {
        event.preventDefault();
        dialog.showModal();
      }
      return;
    }
    var close = event.target.closest('.survey-close');
    if (close) {
      var parent = close.closest('dialog');
      if (parent) parent.close();
      return;
    }
    if (event.target.matches('dialog.survey-dialog')) event.target.close();
  });
}());
