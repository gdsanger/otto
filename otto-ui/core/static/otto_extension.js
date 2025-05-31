window.ottoUI = window.ottoUI || {};
window.ottoUI.openProjectForm = function(values) {
  try {
    var params = Object.keys(values || {})
      .map(function(key) {
        var v = values[key];
        return encodeURIComponent(key) + "=" + encodeURIComponent(v);
      })
      .join("&");
    window.location.href = '/project/new/' + (params ? ('?' + params) : '');
  } catch (e) {
    console.error('openProjectForm failed', e);
  }
};
