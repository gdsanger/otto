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

window.ottoUI.openTaskForm = function(values) {
  try {
    var params = new URLSearchParams(values || {});
    if (window.ottoContext && window.ottoContext.id) {
      params.set('project_id', window.ottoContext.id);
    }
    window.location.href = '/task/new/' + (params.toString() ? ('?' + params.toString()) : '');
  } catch (e) {
    console.error('openTaskForm failed', e);
  }
};
