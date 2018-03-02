function verify_login() {
    if(!verifyLogin()){
        location.replace('user-login.html');
        alert('You need to be logged in to access page');
        return false
    }
    return true
}

$(document).ready(function () {
    $.support.cors = true;
    if(verify_login())
    {
        $.ajax({
            method: "GET",
            url: "https://127.0.0.1:5002/ob/my/account",
            beforeSend: function (xhr) {
                /* Authorization header */
                xhr.setRequestHeader("Authorization", getCookie("token"));
            },
            success: function (data) {
                console.log('Success.');
                console.log(data);
                $("#show-open-bank-user").append("<h2><label>You have already associated your open bank account!</label></h2>");
                $("#show-open-bank-user").append("<br>");
                $("#show-open-bank-user").append("<ul>");
                $("#show-open-bank-user").append("<li id ='ob-list-active' style='background-color: #333; color:rgb(246,255,255);'><label>Your account data:</label></li>");
                $("#show-open-bank-user").append("<li><label><span class=\"glyphicon glyphicon-user span-customized-ob\"></span> Name:<span class='span-customized-ob'>"+' '+data.response.name+' '+data.response.surname+"</span></label></li>");
                $("#show-open-bank-user").append("<li><label><span class=\"glyphicon glyphicon-user span-customized-ob\"></span> Email:<span class='span-customized-ob'>"+' '+data.response.email+"</span></label></li>");
                $("#show-open-bank-user").append("</ul>");

            },
            error: function (data) {
                console.log(data);
                if (data.responseJSON != undefined) {
                    if(data.responseJSON.response === "No user found")
                    {
                        $('#associate_ob_account').css({"display":"block"});
                    }
                }
                else
                {
                    alert("Our server is unavailable. Try access later!");
                    location.replace('index.html')
                }


            }
        });
    };







    //Register Form Handler
    $('#open-bank-register-form').submit(function signup(e){
        e.preventDefault();

        if(!validatePassword()){
            console.log("Account information invalid")
            $('#open_bank_error_message').html("Passwords does not match.");
            return;
        }
        $.ajax({
            method: "POST",
            url: "https://127.0.0.1:5002/ob/associate",
            data: $(this).serializeArray(),
            beforeSend: function (xhr) {
                /* Authorization header */
                xhr.setRequestHeader("Authorization", getCookie("token"));
            },
            success: function (data) {
                console.log('Submission was successful.');
                console.log(data);
                alert("Your Open Bank Account has been successfully associated with your Nearsoft Payment Provider account!");
                location.replace('open-bank-register.html')
            },
            error: function (data) {
                $('#open_bank_error_message').html(data.responseJSON.response);
                console.log('An error occurred.');
                console.log(data);
            }
        })
    });
});