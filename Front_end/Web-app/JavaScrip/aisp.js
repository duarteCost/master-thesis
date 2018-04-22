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




function play_loader(){
    $('.loader_container').css({ display: "block" });
    $('body').css({"background-color":"rgba(230,230,230,0.8)"});
}

function stop_loader(){
    $('.loader_container').css({ display: "none" });
    $('body').css({"background-color":"white"});
}


function verify_login() {
    if(!verifyLogin()){
        location.replace('user-login.html');
        alert('You need to be logged in to access page');
        return false;
    }
    else
    {
        return true;
    }
}

function get_bank_accounts(){
    return $.ajax({
        url: "https://127.0.0.1:5003/aisp/bank/accounts",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function list_bank_accounts(accounts) {
    console.log(accounts)
    var form_id = 0;
    $('#bank_accounts').empty();
    $.each(accounts, function( key, account ) {
        form_id ++;
        $("#bank_accounts").append("<li id ='ob-list-active' style='background-color: #333; color:rgb(246,255,255);'><label>Your default account:</label></li>");
        $("#bank_accounts").append("<li><label>Bank_id:<span class='span-customized-ob'>"+' '+account.bank_id+"</span></label></li>");
        $("#bank_accounts").append("<li><label>Account_id:<span class='span-customized-ob'>"+' '+account.account_id+"</span></label></li>");
        $("#bank_accounts").append("<li><label>Currency:<span class='span-customized-ob'>"+' '+account.balance.currency+"</span></label></li>");
        $("#bank_accounts").append("<li><label>Amount:<span class='span-customized-ob'>"+' '+account.balance.amount+"</span></label></li>");
        $("#bank_accounts").append("<br>");
        $("#bank_accounts").append("<form id = '"+form_id+"' class='update_default_payment_account'>");
        $("#"+form_id).append("<input class='bank_id' type='hidden' name='bank_id' value='"+account.bank_id+"'>");
        $("#"+form_id).append("<input class='account_id' type='hidden' name='account_id' value='"+account.account_id+"'>");
        $("#"+form_id).append("<button type='submit' class='btn choose_default_payment_account' type='button'>Choose</button>")
        $("#bank_accounts").append("</form>");
        $("#bank_accounts").append("<br>");
        $("#bank_accounts").append("<br>");

    });

}

$(document).ready(function () {
    $("head").append('<link rel="stylesheet" href="../Css/alert_box.css">');
    $("head").append('<link rel="stylesheet" href="../Css/accounts_box.css">');
    $("head").append('<link rel="stylesheet" href="../Css/loader.css">');
    $("body").append('<div class="loader_container" style="display: none">')
    $('.loader_container').append('<div class="loader"></div>')
    $.support.cors = true;
    if (verify_login()) {
        play_loader();
        $.ajax({
            method: "GET",
            url: "https://127.0.0.1:5003/aisp/payment/bank/account/default",
            beforeSend: function (xhr) {
                /* Authorization header */
                xhr.setRequestHeader("Authorization", getCookie("token"));
            },
            success: function (data) {
                console.log('Success.');
                console.log(data);
                $("#show-default-payment-account").append("<h2><label>You have already chosen one default payment account!</label></h2>");
                $("#show-default-payment-account").append("<br>");
                $("#show-default-payment-account").append("<ul>");
                $("#show-default-payment-account").append("<li id ='ob-list-active' style='background-color: #333; color:rgb(246,255,255);'><label>Your default account:</label></li>");
                $("#show-default-payment-account").append("<li><label>Bank_id:<span id='bank_id' class='span-customized-ob'>"+' '+data.response.bank_id+"</span></label></li>");
                $("#show-default-payment-account").append("<li><label>Account_id:<span id = 'account_id' class='span-customized-ob'>"+' '+data.response.account_id+"</span></label></li>");
                $("#show-default-payment-account").append("</ul>");
                $("#show-default-payment-account").append("<br>");
                $("#show-default-payment-account").append("<br>");
                $("#show-default-payment-account").append("<p><label>You can change the default payment account on the \"Change\" button!</label></p>")
                $("#show-default-payment-account").append("<button  id='show_bank_acconts'  class='btn' type='button' >Change</button>")
                stop_loader();
            },
            error: function (data) {
                console.log(data);
                if (data.responseJSON != undefined) {
                    if(data.responseJSON.response === "No default payment account has been found")
                    {

                        $("#show-default-payment-account").append("<img style='width: 20%' src='http://divorcemediationstrategies.com/wp-content/uploads/2011/02/sad_face.png'>");
                        $("#show-default-payment-account").append("<br>");
                        $("#show-default-payment-account").append("<br>");
                        $("#show-default-payment-account").append("<h5><label>You have not chosen one default payment account!</label></h5>");
                        $("#show-default-payment-account").append("<br>");
                        $("#show-default-payment-account").append("<br>");
                        $("#show-default-payment-account").append("<button  id='show_bank_acconts'  class='btn' type='button' data-toggle='modal' data-target='#myModal'>Choose</button>")
                    }
                    else
                    {
                        alert(data.responseJSON.response);
                        location.replace('index.html')
                    }
                }
                else
                {
                    alert("Our server is unavailable. Try access later!");
                    location.replace('index.html')
                }
                stop_loader();
            }
        });
    }
    $("#show-default-payment-account").on('click', '#show_bank_acconts', function() {
        play_loader();
        get_bank_accounts().done(function(data) {
            var accounts = data.response;
            stop_loader();
            $('#accounts_modal_id').css({"display":"block"});
            list_bank_accounts(accounts);
        }).fail(function () {
            alert("Error getting bank accounts!!")
            stop_loader();
        })

    });

    $('#bank_accounts').on('submit', '.update_default_payment_account', function (e) {
        e.preventDefault();
        var bank_id = $('.bank_id', this).val();
        var account_id = $('.account_id', this).val();
        $('#accounts_modal_id').css({"display":"none"});
        play_loader();
        $.ajax({
            method: "POST",
            url: "https://127.0.0.1:5003/aisp/payment/bank/account/default",
            data: $(this).serializeArray(),
            beforeSend: function (xhr) {
                /* Authorization header */
                xhr.setRequestHeader("Authorization", getCookie("token"));
            },
            success: function (data) {
                stop_loader();
                Alert("Nearsoft Payment Provader", data.response+"...").done(function () {
                    $('#bank_id').html(bank_id);
                    $('#account_id').html(account_id);
                });
            },
            error: function (data) {
                stop_loader();
                $('#accounts_modal_id').css({"display":"none"});
                Alert("Nearsoft Payment Provader", data.response).done(function () {
                    location.replace('aisp.html')
                });
            }

        });
    });

    $('.close_accounts_box').click(function () {
        $('.accounts-modal-overlay').css({"display":"none"});
    });



});