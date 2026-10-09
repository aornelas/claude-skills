// Copy button for the Ready-to-Use Prompt block. Inlined into the report by finalize_report.py.
document.addEventListener('click', function (e) {
  var btn = e.target.closest('[data-copy]');
  if (!btn) return;
  var pre = document.getElementById(btn.getAttribute('data-copy'));
  if (!pre) return;
  var done = function () { var t = btn.textContent; btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = t; }, 1500); };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(pre.innerText).then(done, function () { fallback(pre, done); });
  } else { fallback(pre, done); }
});
function fallback(pre, done) {
  var r = document.createRange(); r.selectNodeContents(pre);
  var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
  try { document.execCommand('copy'); done(); } catch (err) {}
  s.removeAllRanges();
}
