
function lightleds(non, noff) {
    ul = document.getElementById('volume_leds_list');
    ul.innerHTML = '';

    for (var i = 0; i < noff; i++) {
        li = document.createElement('li');
        li.className = 'led_off';
        ul.appendChild(li);
    }

    for (var i = 0; i < non; i++) {
        li = document.createElement('li');
        li.className = 'led_on';
        ul.appendChild(li);
    }
}

function lightledsjson(data, textStatus, jqXHR) {
    led_count = JSON.parse(data);
    lightleds(led_count.non, led_count.noff);
}

function volchange(dv) {
    vurl = "/volchange/" + dv + '/';
    $.ajax({
        url: vurl,
        cache: false,
        success: lightledsjson
    });    
}
