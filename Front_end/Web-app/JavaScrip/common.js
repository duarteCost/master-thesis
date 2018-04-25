function Alert(title, msg) { /*change*/
    var deferred = new $.Deferred(function () {
        var $content =  "<div class='alert-modal-overlay'>" +
            "<div class='alert-modal'><header>" +
            " <h3> " + title + " </h3> " +
            "</header>" +
            "<div class='message'>" +
            " <p> " + msg + " </p> " +
            "</div>" +
            // "<footer>" +
            // "<div class='controls'>" +
            // " <button class='button button-danger doAction'>Ok</button> " +
            // "</div>" +
            // "</footer>" +
            "</div>" +
            "</div>";
        $('body').prepend($content);
        // $('.doAction').click(function () {
        //     $(this).parents('.alert-modal-overlay').fadeOut(500, function () {
        //         $(this).remove();
        //         deferred.resolve();
        //     });
        // });

        setTimeout(function(){
            $('.alert-modal-overlay').fadeOut(500, function () {
                $(this).remove();
                deferred.resolve();
            });
        }, 2000);

    });
    return deferred.promise();

}



function validateEmail(){
    var email = $("[name='email']").val();
    var regExp = /^[a-z0-9.]+@[a-z0-9]+\.[a-z]+(\.[a-z]+)?$/i;

    if(!regExp.test(email))
    {
        $("[name='email']").addClass( "invalid-field" );
        return false;
    }
    else{
        $("[name='email']").removeClass( "invalid-field" );
        return true;
    }
}


function validatePassword(){
    var password = $("[name='password']").val();
    var confirm = $("[name='confirm-password']").val();

    if(confirm != password){
        $("[name='confirm-password']").addClass( "invalid-field" );
        return false;
    }
    else{
        $("[name='confirm-password']").removeClass( "invalid-field" );
        return true;
    }
}





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

function verifyLogin() {
    if(getCookie("token") === '')
    {
        return false;
    }
    else
    {
        return true;
    }
}





$(document).ready(function () {
    $("head").append('<link rel="stylesheet" href="../Css/alert_box.css">');
    if(verifyLogin())
    {
        $('#login-state').html("Logout");
    }
    else
    {
        $('#login-state').html("Login");
    }

    $('#login-state').click(function () {
        if(verifyLogin()){
            setCookie("token", "", 0.5);
            $('#login-state').html("Login");
            location.replace('index.html');
        }
        else
        {
            location.replace('user-login.html');
        }
    });



});
