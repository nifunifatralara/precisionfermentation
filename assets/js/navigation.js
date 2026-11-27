(function () {
  var nav = document.querySelector('.site-nav');
  if (!nav) return;
  var button = nav.querySelector('.menu-button');
  var menu = nav.querySelector('.nav-links');
  var mobile = window.matchMedia('(max-width: 800px)');
  if (!button || !menu) return;

  function setOpen(open) {
    button.setAttribute('aria-expanded', String(open));
    menu.hidden = mobile.matches && !open;
  }
  function sync() {
    button.hidden = !mobile.matches;
    setOpen(false);
  }
  button.addEventListener('click', function () {
    setOpen(button.getAttribute('aria-expanded') !== 'true');
  });
  menu.addEventListener('click', function (event) {
    if (event.target.closest('a') && mobile.matches) setOpen(false);
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && mobile.matches && !menu.hidden) {
      setOpen(false);
      button.focus();
    }
  });
  if (mobile.addEventListener) mobile.addEventListener('change', sync);
  else mobile.addListener(sync);
  sync();
}());
