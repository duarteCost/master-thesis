function get_default_payment_account(){
    return $.ajax({
        url: "https://127.0.0.1:5003/aisp/payment/bank/account/default",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function delete_default_payment_account(){
    return $.ajax({
        url: "https://127.0.0.1:5003/aisp/payment/bank/account/default",
        method: "DELETE",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function get_current_account() {
    return $.ajax({
        url: "https://127.0.0.1:5001/user/account",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function delete_current_account() {
    return $.ajax({
        url: "https://127.0.0.1:5001/user/account",
        method: "DELETE",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function get_transactions() {
    return $.ajax({
        url: "https://127.0.0.1:5004/transactions_record/transactions",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function delete_transactions() {
    return $.ajax({
        url: "https://127.0.0.1:5004/transactions_record/transactions",
        method: "DELETE",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function exportToFile(data){

    var hiddenElement = document.createElement('a');
    hiddenElement.href = 'data:text/json;filename=exportar.json;charset=utf-8,' + JSON.stringify(data, null, 4);
    hiddenElement.target = '_blank';
    hiddenElement.download = 'user_data.json';
    hiddenElement.click();
}

$(document).ready(function () {

    $('#remove-user-data').click(function () {
        play_loader();
        delete_transactions().done(function () {
            delete_default_payment_account().done(function () {
                delete_current_account().done(function () {
                    stop_loader();
                    Alert("Success", "User data deleted successfully.").done(function () {
                        location.replace('user-login.html');
                    });
                });
            }).fail(function () {
                stop_loader();
                Alert("Error", "Error deleting user data.");
            });
        }).fail(function () {
            stop_loader();
            Alert("Error", "Error deleting user data.");
        }).fail(function () {
            stop_loader();
            Alert("Error", "Error deleting user data.");
        });
    });

    $('#export-user-data').click(function (e) {
        e.preventDefault();
        play_loader();
        var user_data = {};
        get_current_account().done(function (data) {
            delete data['obp_authorization'];
            user_data['user'] = data;
            get_default_payment_account().done(function (data) {
                user_data['default_payment_account'] = data.response;
                get_transactions().done(function (data) {
                    user_data['transactions'] = data.response;
                    exportToFile(user_data);
                    stop_loader();
                    Alert("Success", "User data exported successfully.");

                }).fail(function () {
                    stop_loader();
                    Alert("Error", "Error exporting user data.");
                });
            }).fail(function () {
                stop_loader();
                Alert("Error", "Error exporting user data.");
            });
        }).fail(function () {
            stop_loader();
            Alert("Error", "Error exporting user data.");
        });
    });

});