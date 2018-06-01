
// function get_user() {
//     return $.ajax({
//         url: "https://127.0.0.1:5001/user/account",
//         method: "GET",
//         data: true,
//         beforeSend: function (xhr) {
//             /* Authorization header */
//             xhr.setRequestHeader("Authorization", getCookie("token"));
//         }
//     });
// }



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
function delete_obp_association(){
    return $.ajax({
        url: "https://127.0.0.1:5001/user/obp/associate",
        method: "DELETE",
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
        $("#bank_accounts").append("<li id ='ob-list-active' style='background-color: #333; color:rgb(246,255,255);'><label>Account</label></li>");
        $("#bank_accounts").append("<li><label>Bank_id:<span class='span-customized-ob'>"+' '+account.bank_id+"</span></label></li>");
        $("#bank_accounts").append("<li><label>Account_id:<span class='span-customized-ob'>"+' '+account.account_id+"</span></label></li>");
        $("#bank_accounts").append("<li><label>Currency:<span class='span-customized-ob'>"+' '+account.balance.currency+"</span></label></li>");
        $("#bank_accounts").append("<li><label>Amount:<span class='span-customized-ob'>"+' '+account.balance.amount+"</span></label></li>");
        $("#bank_accounts").append("<br>");
        $("#bank_accounts").append("<form id = '"+form_id+"' class='update_default_payment_account'>");
        $("#"+form_id).append("<input class='bank_id' type='hidden' name='bank_id' value='"+account.bank_id+"'>");
        $("#"+form_id).append("<input class='account_id' type='hidden' name='account_id' value='"+account.account_id+"'>");
        $("#"+form_id).append("<button type='submit' class='btn choose_default_payment_account' type='button'>Choose</button>");
        $("#bank_accounts").append("</form>");
        $("#bank_accounts").append("<br>");
        $("#bank_accounts").append("<br>");

    });

}

$(document).ready(function () {
    $("head").append('<link rel="stylesheet" href="../Css/accounts_box.css">');
    //$("head").append('<link rel="stylesheet" href="../Css/loader.css">');
    //$("head").append('<link rel="stylesheet" href="../Css/confirm_box.css">');
    //$("body").append('<div class="loader_container" style="display: none">');
    //$('.loader_container').append('<div class="loader"></div>');
    play_loader();
    $.support.cors = true;
    if (verify_login()) {
        $('.user_settings').append("<p><label>Hello,</p></label>");
        $('.user_settings').append("<p><label>we hope you are enjoying our services!</label></p>");
        $('.user_settings').append("<br>");
        $('.user_settings').append("<p><label>If you wish to remove the association in OBP you can do so by clicking on the following button.</label></p>");
        $('.user_settings').append("<br>");
        $('.user_settings').append("<br>");
        $('.user_settings').append("<button type='submit' class='btn remove_obp_association' type='button'><p>Remove <br>association</p></button>");
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
                $("#show-default-payment-account").append("<button  class='show_bank_accounts btn'  type='button' >Change</button>")
                stop_loader();
            },
            error: function (data) {
                console.log(data);
                if (data.responseJSON != undefined) {
                    if(data.responseJSON.response === "No default payment account has been found")
                    {

                        $("#show-default-payment-account").append("<img style='width: 20%' src='../Images/sad_smail.png'>");
                        $("#show-default-payment-account").append("<br>");
                        $("#show-default-payment-account").append("<br>");
                        $("#show-default-payment-account").append("<h5><label>You have not chosen one default payment account!</label></h5>");
                        $("#show-default-payment-account").append("<br>");
                        $("#show-default-payment-account").append("<br>");
                        $("#show-default-payment-account").append("<button  class='show_bank_accounts btn' type='button' data-toggle='modal'>Choose</button>")
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
    $("#show-default-payment-account").on('click', '.show_bank_accounts', function() {
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


    $(".user_settings").on('click', '.remove_obp_association', function() {
        Confirm("Nearsoft Payment Provider", "Are you sure you want to remove your OBP association?", "Yes", "No").done(function () {
            play_loader();
            delete_obp_association().done(function (data) {
                stop_loader();
                Alert("Nearsoft Payment Provider", data.response+"...").done(function () {
                    location.replace('open-bank-association.html');
                });
            });
        }).fail(function () {
            //nothing to do yet
        });
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

                $("#show-default-payment-account").empty();
                stop_loader();
                Alert("Nearsoft Payment Provider", data.response+"...").done(function () {
                    $("#show-default-payment-account").append("<h2><label>You have already chosen one default payment account!</label></h2>");
                    $("#show-default-payment-account").append("<br>");
                    $("#show-default-payment-account").append("<ul>");
                    $("#show-default-payment-account").append("<li id ='ob-list-active' style='background-color: #333; color:rgb(246,255,255);'><label>Your default account:</label></li>");
                    $("#show-default-payment-account").append("<li><label>Bank_id:<span id='bank_id' class='span-customized-ob'>"+' '+bank_id+"</span></label></li>");
                    $("#show-default-payment-account").append("<li><label>Account_id:<span id = 'account_id' class='span-customized-ob'>"+' '+account_id+"</span></label></li>");
                    $("#show-default-payment-account").append("</ul>");
                    $("#show-default-payment-account").append("<br>");
                    $("#show-default-payment-account").append("<br>");
                    $("#show-default-payment-account").append("<p><label>You can change the default payment account on the \"Change\" button!</label></p>")
                    $("#show-default-payment-account").append("<button  class='show_bank_accounts btn'  type='button' >Change</button>")
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