
$("#status1").each(function CheckSDR() {
    var $this = $(this);
    $.ajax({
        type: "GET",
        url: "/statusSDR",
        success: function(data) {
          if(data['SDRstatus']== "OK")
          {
            $this.removeClass('inactive').addClass('active').text("Active")
          }
          else{
            $this.removeClass('active').addClass('inactive').text("InActive");
          }
        }
    });
    setTimeout(CheckSDR, 15000);
});
$("#status2").each(function CheckRTL() {
  var $this = $(this);
  $.ajax({
      type: "GET",
      url: "/statusRTL",
      success: function(data) {
        if(data['RTLstatus']== "OK")
        {
          $this.removeClass('inactive').addClass('active').text("Active")
        }
        else{
          $this.removeClass('active').addClass('inactive').text("InActive");
        }
      }
  });
  setTimeout(CheckRTL, 15000);
});
