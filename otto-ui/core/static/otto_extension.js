window.ottoUI = window.ottoUI || {};
window.ottoUI.openProjectForm = function(values) {
  try {
    var params = new URLSearchParams(values || {}).toString();
    window.location.href = '/project/new/' + (params ? ('?' + params) : '');
  } catch (e) {
    console.error('openProjectForm failed', e);
  }
};
