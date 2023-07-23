
let Timeout = 15000;

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
    setTimeout(CheckSDR, Timeout);
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
  setTimeout(CheckRTL, Timeout);
});


function get_all_val(ele, attr_lookup )
{
  var get_checked = [];
  var get_unchecked = [];
  ele.each(function(index, v1)
  {
    if($(this).prop("checked")){
      get_checked.push($(this).attr(attr_lookup));
    }
    else{
      get_unchecked.push($(this).attr(attr_lookup));
    }
  });
  
  let get_obj= {
    checked: get_checked,
    unchecked: get_unchecked,
  }
  return get_obj;
}

$(btn_get_val).click(function(event)
{
  event.preventDefault();
  var ele = $(".data_id");
  var v1 = get_all_val(ele, 'option_id');
  var v2 = JSON.stringify(v1);

  $.ajax({
    type: "POST",
    contentType: "application/json",
    url: "/schedulePasses",
    data: v2,
    dataType: "json"
  });
});

$("#defaultCountdown").each(function StartTimer() {
  var $this = $(this);
  $.ajax({
      type: "GET",
      url: "/Countdown",
      success: function(data) {
        var austDay = new Date(data["AOS_time"]);
        console.log(austDay);
        $this.countdown({until: austDay});
        
      }
  });  
});