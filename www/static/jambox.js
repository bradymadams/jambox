
function volchange(dv) {
    vurl = "/volchange/" + dv;
    $.ajax({
        url: vurl,
        cache: false,
        success: function(json){
        }
    }); 
}
