/* Support legacy ?lang= links and send the Spanish domain to its Spanish page. */
(function () {
  var params = new URLSearchParams(window.location.search);
  var requested = params.get('lang');
  var languages = ['en', 'it', 'fr', 'es', 'de', 'zh', 'ja', 'id', 'pt', 'ru'];
  var spanishDomain = /^(www\.)?fermentaciondeprecision\.com$/i.test(window.location.hostname);
  var englishDomain = /^(www\.)?precisionfermentationfood\.com$/i.test(window.location.hostname);
  if (!requested && spanishDomain && window.location.pathname === '/') requested = 'es';
  if (languages.indexOf(requested) === -1 || document.documentElement.lang === requested) return;
  var target;
  if (spanishDomain || englishDomain) {
    var origin = requested === 'es' ? 'https://fermentaciondeprecision.com/' : 'https://precisionfermentationfood.com/';
    target = new URL(requested === 'en' ? '' : requested + '/', origin);
  } else {
    target = new URL(requested + '/', new URL('../../', document.currentScript.src));
  }
  params.delete('lang');
  target.search = params.toString();
  target.hash = window.location.hash;
  window.location.replace(target.href);
}());
