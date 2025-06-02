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
    var params = Object.keys(values || {})
      .map(function(key) {
        var v = values[key];
        return encodeURIComponent(key) + "=" + encodeURIComponent(v);
      })
      .join("&");

    // Nur project_id aus dem Context hinzufügen, wenn nicht bereits in values enthalten
    if (!(values && values.project_id) && window.ottoContext && window.ottoContext.project_id) {
      params += (params ? '&' : '') + 'project_id=' + encodeURIComponent(window.ottoContext.project_id);
    }

    // requester_id analog
    if (!(values && values.requester_id) && window.ottoContext && window.ottoContext.requester_id) {
      params += '&requester_id=' + encodeURIComponent(window.ottoContext.requester_id);
    }

    window.location.href = '/task/new/' + (params ? ('?' + params) : '');
  } catch (e) {
    console.error('openTaskForm failed', e);
  }
};