function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function  verify_obp_auth() {
    return $.ajax({
        url: "https://127.0.0.1:5001/user/account/obp/authorization",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}


$(document).ready(function(){
    $.support.cors = true;

    $('#login-form').submit(function signup(e){
        e.preventDefault();
        $.ajax({
            method: "POST",
            url: "https://127.0.0.1:5001/user/login",
            data: $(this).serializeArray(),
            success: function (data) {
                setCookie("token", data.token, 0.5);
                verify_obp_auth(getCookie('token')).done(function (data) {
                    if (data.obp_authorization === "NULL") {
                        location.replace('index.html');
                    } else {
                        location.replace('user-page.html');
                    }
                }).fail(function () {
                    Alert("Error", "Login fail.");
                })
            },
            error: function (data) {
                $('#error-message').html('O email e/ou password introduzidos estão incorrectos.');
                console.log('An error occurred.');
                console.log(data);
            }
        })
    });
});