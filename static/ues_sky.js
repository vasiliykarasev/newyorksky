if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined' ? args[number] : match;
    });
  };
};

function date_from_filename(url) {
  timestamp = Number(url.replace(/^.*[\\\/]/, '').replace('.jpg', ''));
  return new Date(timestamp * 1000);
};

function pretty_print_date(d) {
  return d.toISOString('en-US', {timeZone : 'America/New_York'}).slice(0, 10) +
         " " + d.toLocaleTimeString('en-US', {timeZone : 'America/New_York'});
};
